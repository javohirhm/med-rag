#!/usr/bin/env python3
"""
Setup script to process the PDF and build the vector store.
Run this once before starting the bot.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.document_processor import DocumentProcessor
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore

load_dotenv()


def setup_logging():
    """Configure logging."""
    logger.add(
        "logs/setup.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )


def check_prerequisites():
    """Check if all prerequisites are met."""
    logger.info("Checking prerequisites...")
    
    # Check environment variables
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        logger.error("GOOGLE_AI_API_KEY not found in .env file")
        return False
    
    # Check PDF file
    pdf_path = os.getenv('PDF_PATH', './data/oxford_cardiology.pdf')
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        logger.info("Please place the Oxford Cardiology PDF in the data/ directory")
        return False
    
    logger.info("✅ All prerequisites met")
    return True


def run_ocr_if_needed(pdf_path: str) -> str:
    """Run OCR using ocrmypdf when no text could be extracted."""
    if shutil.which("ocrmypdf") is None:
        logger.error("ocrmypdf not found on PATH; install it to OCR scanned PDFs")
        return ""

    ocr_output = str(Path(pdf_path).with_name(Path(pdf_path).stem + "_ocr.pdf"))
    logger.info(f"Running OCR: ocrmypdf {pdf_path} {ocr_output}")

    try:
        subprocess.run([
            "ocrmypdf",
            "--skip-text",
            pdf_path,
            ocr_output
        ], check=True)
        logger.info("OCR completed successfully")
        return ocr_output
    except subprocess.CalledProcessError as exc:
        logger.error(f"OCR failed: {exc}")
        return ""


def main():
    """Main setup process."""
    print("\n" + "="*80)
    print("Cardiology RAG Bot - Setup Script")
    print("="*80 + "\n")
    
    setup_logging()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Setup failed: Missing prerequisites")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    pdf_path = os.getenv('PDF_PATH', '/Users/javohir/Downloads/cardiology-rag-bot/data/cardiologybook.pdf')
    
    print("📚 Processing document...")
    print(f"   Source: {pdf_path}")
    
    # Step 1: Process document
    logger.info("Step 1: Processing PDF document")
    processor = DocumentProcessor(chunk_size=800, chunk_overlap=200)
    
    try:
        chunks = processor.process_document(pdf_path)
        print(f"   ✅ Created {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        print(f"\n❌ Error processing document: {e}")
        sys.exit(1)
    
    if not chunks:
        logger.warning("No text extracted; attempting OCR with ocrmypdf")
        ocr_pdf = run_ocr_if_needed(pdf_path)
        if ocr_pdf:
            try:
                chunks = processor.process_document(ocr_pdf)
                print(f"   ✅ Created {len(chunks)} chunks after OCR")
            except Exception as e:
                logger.error(f"Error processing OCR output: {e}")
                print(f"\n❌ Error processing OCR output: {e}")
                sys.exit(1)

    if not chunks:
        print("\n❌ No chunks created. Check the PDF file or run OCR manually (ocrmypdf original.pdf ocr.pdf).")
        sys.exit(1)
    
    # Step 2: Generate embeddings
    print("\n🔢 Generating embeddings...")
    logger.info("Step 2: Generating embeddings")
    
    try:
        embedding_generator = EmbeddingGenerator()
        
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_generator.generate_embeddings_batch(
            texts,
            task_type="retrieval_document",
            batch_size=32,
            show_progress=True
        )
        
        print(f"   ✅ Generated {len(embeddings)} embeddings")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        print(f"\n❌ Error generating embeddings: {e}")
        print("   Make sure your GOOGLE_AI_API_KEY is valid")
        sys.exit(1)
    
    # Step 3: Build vector store
    print("\n💾 Building vector store...")
    logger.info("Step 3: Building vector store")
    
    try:
        vector_store = VectorStore(
            persist_directory="./chroma_db",
            collection_name="cardiology_handbook"
        )
        
        # Check if collection already has data
        stats = vector_store.get_collection_stats()
        if stats['total_documents'] > 0:
            response = input(f"   ⚠️  Collection already has {stats['total_documents']} documents. Reset? (y/n): ")
            if response.lower() == 'y':
                vector_store.reset()
                print("   ✅ Collection reset")
        
        # Add documents
        vector_store.add_documents(chunks, embeddings)
        
        # Verify
        final_stats = vector_store.get_collection_stats()
        print(f"   ✅ Vector store built successfully")
        print(f"   📊 Total documents: {final_stats['total_documents']}")
        
    except Exception as e:
        logger.error(f"Error building vector store: {e}")
        print(f"\n❌ Error building vector store: {e}")
        sys.exit(1)
    
    # Step 4: Test RAG pipeline
    print("\n🧪 Testing RAG pipeline...")
    logger.info("Step 4: Testing RAG pipeline")
    
    try:
        from src.rag_pipeline import RAGPipeline
        
        pipeline = RAGPipeline()
        
        # Test query
        test_question = "What is atrial fibrillation?"
        print(f"   Test query: {test_question}")
        
        result = pipeline.query(
            question=test_question,
            stream=False,
            return_context=False
        )
        
        print(f"   ✅ RAG pipeline working")
        print(f"   📝 Answer preview: {result['answer'][:150]}...")
        
    except Exception as e:
        logger.error(f"Error testing RAG pipeline: {e}")
        print(f"\n⚠️  Warning: RAG pipeline test failed: {e}")
        print("   The vector store is built but there may be configuration issues")
    
    # Summary
    print("\n" + "="*80)
    print("Setup Complete! 🎉")
    print("="*80)
    print("\nNext steps:")
    print("1. Make sure your .env file has TELEGRAM_BOT_TOKEN set")
    print("2. Run the bot: python -m src.telegram_bot")
    print("\nOr test the RAG pipeline: python -m src.rag_pipeline")
    print("="*80 + "\n")
    
    logger.info("Setup completed successfully")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
