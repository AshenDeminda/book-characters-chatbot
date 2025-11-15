import pdfplumber
import PyPDF2
import re
from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract and preprocess text from PDF files"""

    def __init__(self):
        self.min_text_length = 50  # Minimum page text length

    def _validate_pdf(self, pdf_path: str) -> None:
        """Validate PDF file before extraction"""
        # Check file exists
        if not os.path.exists(pdf_path):
            raise Exception("PDF file not found")
        
        # Check file size (must be > 1KB)
        file_size = os.path.getsize(pdf_path)
        if file_size < 1024:
            raise Exception("PDF file is too small (less than 1KB). File may be corrupted.")
        
        # Check file header (PDF files start with %PDF)
        with open(pdf_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise Exception("File is not a valid PDF (invalid header)")

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF using pdfplumber (primary)
        with PyPDF2 fallback

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with extracted text and metadata
        """
        # Validate PDF first
        try:
            self._validate_pdf(pdf_path)
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            raise
        
        # Try pdfplumber first
        pdfplumber_error = None
        try:
            result = self._extract_with_pdfplumber(pdf_path)
            logger.info(f"Successfully extracted {result['page_count']} pages using pdfplumber")
            return result
        except Exception as e:
            pdfplumber_error = str(e)
            logger.warning(f"pdfplumber extraction failed: {pdfplumber_error}")
        
        # Fallback to PyPDF2
        logger.info("Attempting PyPDF2 fallback extraction...")
        try:
            result = self._extract_with_pypdf2(pdf_path)
            logger.info(f"Successfully extracted {result['page_count']} pages using PyPDF2")
            return result
        except Exception as e2:
            pypdf2_error = str(e2)
            logger.error(f"PyPDF2 extraction also failed: {pypdf2_error}")
            raise Exception(f"PDF extraction failed with both methods. pdfplumber error: {pdfplumber_error}. PyPDF2 error: {pypdf2_error}")

    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict:
        """Extract using pdfplumber (better layout preservation)"""
        text_by_page = []
        total_pages = 0
        
        try:
            pdf = pdfplumber.open(pdf_path)
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text and len(text.strip()) > self.min_text_length:
                        cleaned_text = self._clean_text(text)
                        text_by_page.append({
                            "page": page_num,
                            "text": cleaned_text
                        })
                except Exception as page_error:
                    logger.warning(f"Failed to extract page {page_num}: {page_error}")
                    # Continue to next page even if one page fails
                    continue
            
            pdf.close()
            
            full_text = "\n\n".join([p["text"] for p in text_by_page])
            
            if not full_text or len(full_text.strip()) < 100:
                raise Exception("PDF appears to be empty or contains no extractable text")

            return {
                "full_text": full_text,
                "pages": text_by_page,
                "page_count": total_pages,
                "total_length": len(full_text),
                "method": "pdfplumber"
            }
        except Exception as e:
            error_msg = str(e)
            if "Compressed file" in error_msg or "end-of-stream" in error_msg:
                raise Exception(f"PDF compression error: {error_msg}. This PDF may use unsupported compression or be corrupted.")
            raise Exception(f"pdfplumber extraction failed: {error_msg}")

    def _extract_with_pypdf2(self, pdf_path: str) -> Dict:
        """Fallback extraction using PyPDF2"""
        text_by_page = []

        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)

                for page_num in range(total_pages):
                    try:
                        page = reader.pages[page_num]
                        text = page.extract_text()
                        if text and len(text.strip()) > self.min_text_length:
                            cleaned_text = self._clean_text(text)
                            text_by_page.append({
                                "page": page_num + 1,
                                "text": cleaned_text
                            })
                    except Exception as page_error:
                        logger.warning(f"Failed to extract page {page_num + 1}: {page_error}")
                        continue

            full_text = "\n\n".join([p["text"] for p in text_by_page])
            
            if not full_text or len(full_text.strip()) < 100:
                raise Exception("PDF appears to be empty or contains no extractable text")

            return {
                "full_text": full_text,
                "pages": text_by_page,
                "page_count": total_pages,
                "total_length": len(full_text),
                "method": "PyPDF2"
            }
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}. The file may be corrupted, password-protected, or in an unsupported format.")

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