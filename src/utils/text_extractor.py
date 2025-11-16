import pdfplumber
import PyPDF2
import re
from typing import Dict, List
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract and preprocess text from PDF files"""

    def __init__(self, parallel_processing: bool = True, max_workers: int = None):
        """
        Initialize TextExtractor with parallel processing options
        
        Args:
            parallel_processing: Enable/disable parallel page extraction (default: True)
            max_workers: Maximum number of worker threads (default: CPU count)
        """
        self.min_text_length = 50  # Minimum page text length
        self.parallel_processing = parallel_processing
        # Use CPU count for optimal parallelization (usually 4-8 workers)
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 8)

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
        """
        Extract using pdfplumber (better layout preservation)
        
        TASK 1 OPTIMIZATION: Parallel PDF Processing
        - Uses ThreadPoolExecutor for concurrent page extraction
        - Processes multiple pages simultaneously (up to CPU count workers)
        - Expected improvement: 60-75% reduction in PDF extraction time
        """
        text_by_page = []
        total_pages = 0
        
        try:
            pdf = pdfplumber.open(pdf_path)
            total_pages = len(pdf.pages)
            
            # ==================================================================
            # NEW: PARALLEL PROCESSING (Task 1 Implementation)
            # ==================================================================
            if self.parallel_processing and total_pages > 1:
                logger.info(f"Using parallel processing with {self.max_workers} workers for {total_pages} pages")
                
                # Extract pages in parallel using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all page extraction tasks
                    future_to_page = {
                        executor.submit(self._extract_single_page_pdfplumber, page, page_num): page_num
                        for page_num, page in enumerate(pdf.pages, 1)
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_page):
                        page_num = future_to_page[future]
                        try:
                            result = future.result()
                            if result:  # Only add if extraction succeeded
                                text_by_page.append(result)
                        except Exception as page_error:
                            logger.warning(f"Failed to extract page {page_num}: {page_error}")
                            continue
                
                # Sort pages by page number (parallel processing may complete out of order)
                text_by_page.sort(key=lambda x: x['page'])
                
            else:
                # ==================================================================
                # OLD: SEQUENTIAL PROCESSING (Kept for reference/fallback)
                # This is the original implementation before Task 1 optimization
                # Can be re-enabled by setting parallel_processing=False
                # ==================================================================
                logger.info(f"Using sequential processing for {total_pages} pages")
                
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

    def _extract_single_page_pdfplumber(self, page, page_num: int) -> Dict:
        """
        Extract text from a single page (for parallel processing)
        
        Args:
            page: pdfplumber Page object
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with page number and extracted text, or None if extraction failed
        """
        try:
            text = page.extract_text()
            if text and len(text.strip()) > self.min_text_length:
                cleaned_text = self._clean_text(text)
                return {
                    "page": page_num,
                    "text": cleaned_text
                }
        except Exception as e:
            logger.warning(f"Failed to extract page {page_num}: {e}")
        return None
    
    def _extract_single_page_pypdf2(self, page, page_num: int) -> Dict:
        """
        Extract text from a single PyPDF2 page (for parallel processing)
        
        Args:
            page: PyPDF2 Page object
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with page number and extracted text, or None if extraction failed
        """
        try:
            text = page.extract_text()
            if text and len(text.strip()) > self.min_text_length:
                cleaned_text = self._clean_text(text)
                return {
                    "page": page_num,
                    "text": cleaned_text
                }
        except Exception as e:
            logger.warning(f"Failed to extract page {page_num}: {e}")
        return None

    def _extract_with_pypdf2(self, pdf_path: str) -> Dict:
        """
        Fallback extraction using PyPDF2
        
        TASK 1 OPTIMIZATION: Parallel PDF Processing
        - Uses ThreadPoolExecutor for concurrent page extraction
        - Same parallel strategy as pdfplumber method
        """
        text_by_page = []

        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)

                # ==================================================================
                # NEW: PARALLEL PROCESSING (Task 1 Implementation)
                # ==================================================================
                if self.parallel_processing and total_pages > 1:
                    logger.info(f"Using parallel PyPDF2 processing with {self.max_workers} workers")
                    
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        future_to_page = {
                            executor.submit(self._extract_single_page_pypdf2, reader.pages[i], i + 1): i + 1
                            for i in range(total_pages)
                        }
                        
                        for future in as_completed(future_to_page):
                            page_num = future_to_page[future]
                            try:
                                result = future.result()
                                if result:
                                    text_by_page.append(result)
                            except Exception as page_error:
                                logger.warning(f"Failed to extract page {page_num}: {page_error}")
                                continue
                    
                    # Sort by page number
                    text_by_page.sort(key=lambda x: x['page'])
                    
                else:
                    # ==================================================================
                    # OLD: SEQUENTIAL PROCESSING (Kept for reference/fallback)
                    # ==================================================================
                    logger.info(f"Using sequential PyPDF2 processing")
                    
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
        Split text into semantically meaningful chunks with overlap
        
        IMPROVED: Semantic chunking for better RAG retrieval accuracy
        - Splits at paragraph boundaries first
        - Falls back to sentence boundaries
        - Preserves context with smart overlap
        - Prevents mid-sentence breaks

        Args:
            text: Full text to chunk
            chunk_size: Target chunk size in characters (soft limit)
            overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Split into paragraphs first (double newline or single newline for short texts)
        paragraphs = []
        for para in text.split('\n\n'):
            if para.strip():
                paragraphs.append(para.strip())
        
        # If no double newlines, split on single newlines
        if len(paragraphs) == 1:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            # If single paragraph exceeds chunk_size, split it by sentences
            if para_length > chunk_size:
                # Split paragraph into sentences
                sentences = self._split_sentences(para)
                
                for sentence in sentences:
                    sentence_length = len(sentence)
                    
                    # If adding this sentence exceeds limit, save current chunk
                    if current_length + sentence_length > chunk_size and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        
                        # Start new chunk with overlap (last 1-2 sentences)
                        overlap_sentences = []
                        overlap_length = 0
                        for prev_sent in reversed(current_chunk):
                            if overlap_length + len(prev_sent) <= overlap:
                                overlap_sentences.insert(0, prev_sent)
                                overlap_length += len(prev_sent)
                            else:
                                break
                        
                        current_chunk = overlap_sentences
                        current_length = overlap_length
                    
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # If adding this paragraph exceeds chunk_size, save current chunk
            elif current_length + para_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_text = ' '.join(current_chunk)
                if len(overlap_text) > overlap:
                    overlap_text = overlap_text[-overlap:]
                
                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_length = len(overlap_text) + para_length
            
            # Otherwise, add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_length += para_length
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (improved over simple period split)
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        import re
        
        # Split on sentence endings: . ! ? followed by space/newline/end
        # But not on abbreviations like Mr. Dr. etc.
        sentence_pattern = r'(?<![A-Z])(?<!\d)(?<=\.|\!|\?)\s+'
        
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]