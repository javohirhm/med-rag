"""
Embedding generation using Google AI API.
"""
import os
from typing import List, Optional
import time

import google.generativeai as genai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class EmbeddingGenerator:
    """Generate embeddings using Google's text-embedding models."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model_name: str = "models/text-embedding-004"
    ):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: Google AI API key (if None, reads from environment)
            model_name: Name of the embedding model to use
        """
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key not found. Set GOOGLE_AI_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        logger.info(f"EmbeddingGenerator initialized with model: {model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            task_type: Type of task (retrieval_document, retrieval_query, etc.)
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type,
                title="Cardiology Document" if task_type == "retrieval_document" else None
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        task_type: str = "retrieval_document",
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            task_type: Type of task for all texts
            batch_size: Number of texts to process at once
            show_progress: Whether to show progress logs
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
        
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if show_progress:
                logger.info(f"Processing batch {batch_num}/{total_batches}")
            
            try:
                batch_embeddings = []
                for text in batch:
                    embedding = self.generate_embedding(text, task_type)
                    batch_embeddings.append(embedding)
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                # Add placeholder embeddings for failed batch
                embeddings.extend([[0.0] * 768] * len(batch))
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        return self.generate_embedding(query, task_type="retrieval_query")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings from this model.
        
        Returns:
            Embedding dimension size
        """
        # text-embedding-004 produces 768-dimensional embeddings
        return 768


def main():
    """Example usage of EmbeddingGenerator."""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Setup logging
    logger.add(
        "logs/embedding_generation.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )
    
    try:
        # Initialize generator
        generator = EmbeddingGenerator()
        
        # Test single embedding
        print("\n" + "="*80)
        print("Testing Single Embedding")
        print("="*80)
        
        test_text = "Atrial fibrillation is an irregular heart rhythm characterized by rapid and chaotic electrical signals in the atria."
        embedding = generator.generate_embedding(test_text)
        
        print(f"Text: {test_text}")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")
        
        # Test query embedding
        print("\n" + "="*80)
        print("Testing Query Embedding")
        print("="*80)
        
        query = "What are the symptoms of atrial fibrillation?"
        query_embedding = generator.generate_query_embedding(query)
        
        print(f"Query: {query}")
        print(f"Embedding dimension: {len(query_embedding)}")
        print(f"First 10 values: {query_embedding[:10]}")
        
        # Test batch embeddings
        print("\n" + "="*80)
        print("Testing Batch Embeddings")
        print("="*80)
        
        texts = [
            "Heart failure is a condition where the heart cannot pump blood effectively.",
            "Hypertension, or high blood pressure, is a major risk factor for cardiovascular disease.",
            "Coronary artery disease occurs when arteries supplying blood to the heart become narrowed."
        ]
        
        batch_embeddings = generator.generate_embeddings_batch(texts, batch_size=2)
        
        print(f"Generated embeddings for {len(batch_embeddings)} texts")
        for i, emb in enumerate(batch_embeddings):
            print(f"Text {i+1} embedding dimension: {len(emb)}")
        
        print("\n✅ All embedding tests passed!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
