"""
Vector store implementation using ChromaDB for efficient similarity search.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from loguru import logger

from .document_processor import DocumentChunk


class VectorStore:
    """Manage document embeddings and similarity search with ChromaDB."""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "cardiology_handbook",
        distance_metric: str = "cosine"
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to store ChromaDB data
            collection_name: Name of the collection
            distance_metric: Distance metric for similarity (cosine, l2, ip)
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=None  # We'll provide embeddings manually
            )
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            metadata = {"hnsw:space": distance_metric}
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata,
                embedding_function=None
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> None:
        """
        Add document chunks and their embeddings to the vector store.
        
        Args:
            chunks: List of document chunks
            embeddings: Corresponding embeddings for each chunk
            batch_size: Number of documents to add at once
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
        
        logger.info(f"Adding {len(chunks)} documents to vector store")
        
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            # Prepare data for ChromaDB
            ids = [f"chunk_{chunk.chunk_index}" for chunk in batch_chunks]
            documents = [chunk.text for chunk in batch_chunks]
            metadatas = [
                {
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
                for chunk in batch_chunks
            ]
            
            try:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=batch_embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Added batch {batch_num}/{total_batches}")
            except Exception as e:
                logger.error(f"Error adding batch {batch_num}: {e}")
                raise
        
        logger.info(f"Successfully added {len(chunks)} documents")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using query embedding.
        
        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of top results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results with documents and metadata
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            logger.info(f"Search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        return {
            "name": self.collection_name,
            "total_documents": count,
            "persist_directory": str(self.persist_directory)
        }
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def reset(self) -> None:
        """Reset the vector store (delete and recreate collection)."""
        logger.warning("Resetting vector store...")
        self.delete_collection()
        
        metadata = {"hnsw:space": self.distance_metric}
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata=metadata,
            embedding_function=None
        )
        logger.info("Vector store reset complete")


def main():
    """Example usage of VectorStore."""
    from dotenv import load_dotenv
    import sys
    
    load_dotenv()
    
    # Setup logging
    logger.add(
        "logs/vector_store.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )
    
    try:
        print("\n" + "="*80)
        print("Vector Store Test")
        print("="*80)
        
        # Initialize vector store
        vector_store = VectorStore(
            persist_directory="./test_chroma_db",
            collection_name="test_collection"
        )
        
        # Check if we need to populate (for testing)
        stats = vector_store.get_collection_stats()
        print(f"\nCollection Stats:")
        print(f"  Name: {stats['name']}")
        print(f"  Total Documents: {stats['total_documents']}")
        print(f"  Directory: {stats['persist_directory']}")
        
        if stats['total_documents'] == 0:
            print("\n⚠️  Collection is empty. Run document_processor.py first to populate.")
        else:
            print("\n✅ Vector store loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
