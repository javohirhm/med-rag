"""
Document processor for extracting and chunking text from PDFs.
"""
import os
from typing import List, Dict, Any
from pathlib import Path
import re

import pdfplumber
from loguru import logger
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata."""
    text: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]
    

class DocumentProcessor:
    """Process PDF documents and split into semantic chunks."""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF file page by page.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page text and metadata
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")
        pages_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF has {total_pages} pages")
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    
                    if text:
                        # Clean the text
                        text = self._clean_text(text)
                        
                        pages_data.append({
                            'page_number': page_num,
                            'text': text,
                            'metadata': {
                                'source': os.path.basename(pdf_path),
                                'total_pages': total_pages
                            }
                        })
                        logger.debug(f"Extracted {len(text)} characters from page {page_num}")
                    else:
                        logger.warning(f"No text extracted from page {page_num}")
                        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
        
        logger.info(f"Successfully extracted text from {len(pages_data)} pages")
        return pages_data
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing unwanted characters and formatting.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep medical notation
        text = re.sub(r'[^\w\s.,;:!()\-–—/%°±×÷<>≤≥\[\]{}\'\"α-ωΑ-Ω]', '', text)
        
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        
        return text.strip()
    
    def chunk_text(self, pages_data: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        Split pages into overlapping chunks.
        
        Args:
            pages_data: List of page data dictionaries
            
        Returns:
            List of DocumentChunk objects
        """
        logger.info(f"Chunking text from {len(pages_data)} pages")
        chunks = []
        chunk_index = 0
        
        for page_data in pages_data:
            text = page_data['text']
            page_number = page_data['page_number']
            metadata = page_data['metadata']
            
            # Split text into sentences for better semantic chunking
            sentences = self._split_into_sentences(text)
            
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                if current_length + sentence_length > self.chunk_size and current_chunk:
                    # Create chunk from accumulated sentences
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(DocumentChunk(
                        text=chunk_text,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        metadata={
                            **metadata,
                            'chunk_length': len(chunk_text)
                        }
                    ))
                    chunk_index += 1
                    
                    # Keep overlap
                    overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else chunk_text
                    current_chunk = [overlap_text, sentence]
                    current_length = len(overlap_text) + sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # Add remaining text as final chunk
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    metadata={
                        **metadata,
                        'chunk_length': len(chunk_text)
                    }
                ))
                chunk_index += 1
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple heuristics.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitter (can be improved with NLTK or spaCy)
        # Handle common medical abbreviations
        text = text.replace('Dr.', 'Dr').replace('Mr.', 'Mr').replace('Mrs.', 'Mrs')
        text = text.replace('e.g.', 'eg').replace('i.e.', 'ie').replace('etc.', 'etc')
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def process_document(self, pdf_path: str) -> List[DocumentChunk]:
        """
        Main processing pipeline: extract and chunk document.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of document chunks ready for embedding
        """
        logger.info(f"Processing document: {pdf_path}")
        
        # Extract text from PDF
        pages_data = self.extract_text_from_pdf(pdf_path)
        
        if not pages_data:
            logger.error("No text extracted from PDF")
            return []
        
        # Chunk the text
        chunks = self.chunk_text(pages_data)
        
        logger.info(f"Document processing complete: {len(chunks)} chunks created")
        return chunks


def main():
    """Example usage of DocumentProcessor."""
    from dotenv import load_dotenv
    import sys
    
    load_dotenv()
    
    # Setup logging
    logger.add(
        "logs/document_processing.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    # Check if PDF path is provided
    pdf_path = os.getenv('PDF_PATH', './data/oxford_cardiology.pdf')
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Process document
    processor = DocumentProcessor(chunk_size=800, chunk_overlap=200)
    chunks = processor.process_document(pdf_path)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"Document Processing Results")
    print(f"{'='*80}")
    print(f"Total chunks created: {len(chunks)}")
    print(f"\nFirst 3 chunks:\n")
    
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"Page: {chunk.page_number}")
        print(f"Length: {len(chunk.text)} characters")
        print(f"Text preview: {chunk.text[:200]}...")
        print(f"{'-'*80}")


if __name__ == "__main__":
    main()
