"""
RAG Pipeline: Orchestrates document retrieval and generation.
"""
import os
from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path

from loguru import logger

from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .llm_client import GeminiClient


class RAGPipeline:
    """Complete RAG pipeline for question answering."""
    
    def __init__(
        self,
        config_path: str = "config/config.yaml",
        vector_store_path: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            config_path: Path to configuration file
            vector_store_path: Override vector store path
            collection_name: Override collection name
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        logger.info("Initializing RAG pipeline components...")
        
        # Embedding generator
        self.embedding_generator = EmbeddingGenerator(
            model_name=self.config['rag']['embedding_model']
        )
        
        # Vector store
        vs_path = vector_store_path or self.config['vector_store']['persist_directory']
        coll_name = collection_name or self.config['vector_store']['collection_name']
        
        self.vector_store = VectorStore(
            persist_directory=vs_path,
            collection_name=coll_name,
            distance_metric=self.config['vector_store']['distance_metric']
        )
        
        # LLM client
        self.llm_client = GeminiClient(
            model_name=self.config['rag']['model'],
            temperature=self.config['rag']['temperature'],
            max_tokens=self.config['rag']['max_tokens'],
            top_p=self.config['rag']['top_p'],
            top_k=self.config['rag']['top_k_llm']
        )
        
        # RAG parameters
        self.top_k = self.config['rag']['top_k']
        self.similarity_threshold = self.config['rag']['similarity_threshold']
        
        # Prompt templates
        self.system_prompt = self.config['prompts']['system']
        self.query_template = self.config['prompts']['query_template']
        
        logger.info("RAG pipeline initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User question
            top_k: Number of results to retrieve (overrides config)
            filter_metadata: Optional metadata filter
            
        Returns:
            List of retrieved documents with metadata
        """
        logger.info(f"Retrieving context for query: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(query)
        
        # Search vector store
        k = top_k or self.top_k
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k,
            filter_metadata=filter_metadata
        )
        
        # Filter by similarity threshold
        filtered_results = [
            r for r in results 
            if r['similarity'] >= self.similarity_threshold
        ]
        
        logger.info(f"Retrieved {len(filtered_results)} relevant documents")
        return filtered_results
    
    def format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No relevant context found in the handbook."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            page_num = doc['metadata'].get('page_number', 'Unknown')
            similarity = doc.get('similarity', 0)
            
            context_parts.append(
                f"[Context {i}] (Page {page_num}, Relevance: {similarity:.2f})\n"
                f"{doc['document']}\n"
            )
        
        return "\n".join(context_parts)
    
    def generate_answer(
        self,
        query: str,
        context: str,
        stream: bool = False
    ) -> str:
        """
        Generate answer using LLM with retrieved context.
        
        Args:
            query: User question
            context: Retrieved context
            stream: Whether to stream response
            
        Returns:
            Generated answer
        """
        # Build prompt
        prompt = self.query_template.format(
            context=context,
            question=query
        )
        
        logger.info("Generating answer with LLM")
        
        # Generate response
        if stream:
            return self.llm_client.generate_response_stream(
                prompt=prompt,
                system_instruction=self.system_prompt
            )
        else:
            return self.llm_client.generate_response(
                prompt=prompt,
                system_instruction=self.system_prompt
            )
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        stream: bool = False,
        return_context: bool = False
    ) -> Dict[str, Any]:
        """
        Complete RAG query: retrieve context and generate answer.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            stream: Whether to stream response
            return_context: Whether to include context in response
            
        Returns:
            Dictionary with answer and optionally context
        """
        logger.info(f"Processing RAG query: {question[:100]}...")
        
        # Retrieve context
        retrieved_docs = self.retrieve_context(question, top_k=top_k)
        
        # Format context
        context = self.format_context(retrieved_docs)
        
        # Generate answer
        if stream:
            # For streaming, return generator
            answer_generator = self.generate_answer(question, context, stream=True)
            
            result = {
                "answer": answer_generator,
                "retrieved_docs": len(retrieved_docs),
                "streaming": True
            }
        else:
            # For non-streaming, return complete answer
            answer = self.generate_answer(question, context, stream=False)
            
            result = {
                "answer": answer,
                "retrieved_docs": len(retrieved_docs),
                "streaming": False
            }
        
        # Optionally include context
        if return_context:
            result["context"] = context
            result["documents"] = retrieved_docs
        
        logger.info("RAG query completed successfully")
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary with statistics
        """
        vs_stats = self.vector_store.get_collection_stats()
        
        return {
            "vector_store": vs_stats,
            "embedding_model": self.config['rag']['embedding_model'],
            "llm_model": self.config['rag']['model'],
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold
        }


def main():
    """Example usage of RAGPipeline."""
    from dotenv import load_dotenv
    import sys
    
    load_dotenv()
    
    # Setup logging
    logger.add(
        "logs/rag_pipeline.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )
    
    try:
        print("\n" + "="*80)
        print("RAG Pipeline Test")
        print("="*80)
        
        # Initialize pipeline
        pipeline = RAGPipeline()
        
        # Get stats
        stats = pipeline.get_stats()
        print("\nPipeline Statistics:")
        print(f"  Vector Store: {stats['vector_store']['name']}")
        print(f"  Total Documents: {stats['vector_store']['total_documents']}")
        print(f"  Embedding Model: {stats['embedding_model']}")
        print(f"  LLM Model: {stats['llm_model']}")
        print(f"  Top-K: {stats['top_k']}")
        
        if stats['vector_store']['total_documents'] == 0:
            print("\n⚠️  Vector store is empty. Please run the setup script first.")
            sys.exit(0)
        
        # Test query
        print("\n" + "="*80)
        print("Test Query")
        print("="*80)
        
        question = "What is atrial fibrillation and what are its symptoms?"
        print(f"\nQuestion: {question}")
        print("\nRetrieving context and generating answer...\n")
        
        result = pipeline.query(
            question=question,
            stream=False,
            return_context=True
        )
        
        print("Answer:")
        print("-" * 80)
        print(result['answer'])
        print("-" * 80)
        
        print(f"\nRetrieved {result['retrieved_docs']} relevant documents")
        
        # Test streaming
        print("\n" + "="*80)
        print("Test Streaming Query")
        print("="*80)
        
        question = "What are the main treatments for heart failure?"
        print(f"\nQuestion: {question}")
        print("\nStreaming answer: ", end="", flush=True)
        
        result = pipeline.query(question=question, stream=True)
        
        for chunk in result['answer']:
            print(chunk, end="", flush=True)
        print("\n")
        
        print("\n✅ RAG pipeline tests completed!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
