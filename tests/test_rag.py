"""
Tests for RAG pipeline components.
"""
import pytest
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_processor import DocumentProcessor, DocumentChunk
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore


class TestDocumentProcessor:
    """Test document processing."""
    
    def test_chunk_text(self):
        """Test text chunking."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        
        pages_data = [
            {
                'page_number': 1,
                'text': "This is a test. " * 20,
                'metadata': {'source': 'test.pdf'}
            }
        ]
        
        chunks = processor.chunk_text(pages_data)
        
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(len(c.text) <= 120 for c in chunks)  # chunk_size + some tolerance
    
    def test_clean_text(self):
        """Test text cleaning."""
        processor = DocumentProcessor()
        
        text = "This   has    extra   spaces."
        cleaned = processor._clean_text(text)
        
        assert "  " not in cleaned
        assert cleaned.strip() == "This has extra spaces."
    
    def test_split_sentences(self):
        """Test sentence splitting."""
        processor = DocumentProcessor()
        
        text = "First sentence. Second sentence! Third sentence?"
        sentences = processor._split_into_sentences(text)
        
        assert len(sentences) == 3


class TestEmbeddingGenerator:
    """Test embedding generation."""
    
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_AI_API_KEY'),
        reason="GOOGLE_AI_API_KEY not set"
    )
    def test_generate_embedding(self):
        """Test single embedding generation."""
        generator = EmbeddingGenerator()
        
        text = "This is a test sentence."
        embedding = generator.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768  # text-embedding-004 dimension
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embedding_dimension(self):
        """Test getting embedding dimension."""
        generator = EmbeddingGenerator()
        
        dim = generator.get_embedding_dimension()
        assert dim == 768


class TestVectorStore:
    """Test vector store operations."""
    
    def test_initialization(self):
        """Test vector store initialization."""
        vs = VectorStore(
            persist_directory="./test_chroma",
            collection_name="test_collection"
        )
        
        stats = vs.get_collection_stats()
        assert stats['name'] == "test_collection"
        assert 'total_documents' in stats
        
        # Cleanup
        vs.delete_collection()
    
    def test_add_and_search(self):
        """Test adding documents and searching."""
        vs = VectorStore(
            persist_directory="./test_chroma",
            collection_name="test_collection"
        )
        
        # Create test chunks
        chunks = [
            DocumentChunk(
                text="Atrial fibrillation is a heart condition.",
                page_number=1,
                chunk_index=0,
                metadata={'source': 'test.pdf'}
            ),
            DocumentChunk(
                text="Heart failure affects cardiac output.",
                page_number=1,
                chunk_index=1,
                metadata={'source': 'test.pdf'}
            )
        ]
        
        # Create dummy embeddings (768-dim)
        embeddings = [[0.1] * 768, [0.2] * 768]
        
        # Add documents
        vs.add_documents(chunks, embeddings)
        
        # Search
        query_embedding = [0.15] * 768
        results = vs.search(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert 'document' in results[0]
        assert 'metadata' in results[0]
        
        # Cleanup
        vs.delete_collection()


def test_pipeline_integration():
    """Test full pipeline integration (requires setup)."""
    # This would require a fully set up environment
    # For now, just check imports work
    from src.rag_pipeline import RAGPipeline
    from src.llm_client import GeminiClient
    
    assert RAGPipeline is not None
    assert GeminiClient is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
