import pdfplumber
import PyPDF2
import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract and preprocess text from PDF files"""

    def __init__(self):
        self.min_text_length = 50  # Minimum page text length

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF using pdfplumber (primary)
        with PyPDF2 fallback

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            return self._extract_with_pdfplumber(pdf_path)
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
            return self._extract_with_pypdf2(pdf_path)

    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict:
        """Extract using pdfplumber (better layout preservation)"""
        text_by_page = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and len(text.strip()) > self.min_text_length:
                    cleaned_text = self._clean_text(text)
                    text_by_page.append({
                        "page": page_num,
                        "text": cleaned_text
                    })

        full_text = "\n\n".join([p["text"] for p in text_by_page])

        return {
            "full_text": full_text,
            "pages": text_by_page,
            "page_count": total_pages,
            "total_length": len(full_text),
            "method": "pdfplumber"
        }

    def _extract_with_pypdf2(self, pdf_path: str) -> Dict:
        """Fallback extraction using PyPDF2"""
        text_by_page = []

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)

            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text and len(text.strip()) > self.min_text_length:
                    cleaned_text = self._clean_text(text)
                    text_by_page.append({
                        "page": page_num + 1,
                        "text": cleaned_text
                    })

        full_text = "\n\n".join([p["text"] for p in text_by_page])

        return {
            "full_text": full_text,
            "pages": text_by_page,
            "page_count": total_pages,
            "total_length": len(full_text),
            "method": "PyPDF2"
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers and headers/footers (basic)
        text = re.sub(r'\n\d+\n', '\n', text)

        # Fix common OCR errors
        text = text.replace("'", "'")
        text = text.replace('"', '"')
        text = text.replace('"', '"')
        text = text.replace('—', '-')
        text = text.replace('–', '-')

        return text.strip()

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks for embedding

        Args:
            text: Full text to chunk
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:
                    end = start + break_point + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            # Prevent infinite loop - ensure we're moving forward
            if start >= end or (len(chunks) > 1 and start <= 0):
                break
        
        return chunks