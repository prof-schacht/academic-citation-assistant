"""PDF text extraction service with page number tracking using PyMuPDF."""
import os
import logging
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFPageExtractor:
    """Service for extracting text from PDFs while preserving page information."""
    
    def extract_text_with_pages(self, file_path: str, chunk_size: int = 1000) -> Tuple[str, List[Dict]]:
        """
        Extract text from PDF with page number information.
        
        Args:
            file_path: Path to the PDF file
            chunk_size: Approximate size of text chunks in characters
            
        Returns:
            Tuple of (full_text, page_mappings)
            where page_mappings contains character positions to page numbers
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with fitz.open(file_path) as doc:
                full_text = ""
                page_mappings = []
                char_position = 0
                
                for page_num, page in enumerate(doc, start=1):
                    # Extract text from page
                    page_text = page.get_text()
                    
                    if page_text:
                        # Record the character range for this page
                        page_start = char_position
                        page_end = char_position + len(page_text)
                        
                        page_mappings.append({
                            'page_number': page_num,
                            'start_char': page_start,
                            'end_char': page_end,
                            'text_length': len(page_text)
                        })
                        
                        full_text += page_text
                        char_position = page_end
                        
                        logger.debug(f"Extracted page {page_num}: {len(page_text)} characters")
                
                logger.info(f"Extracted {len(doc)} pages, total {len(full_text)} characters")
                return full_text, page_mappings
                
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise
    
    def get_page_for_chunk(self, chunk_start: int, chunk_end: int, page_mappings: List[Dict]) -> Dict:
        """
        Determine which page(s) a chunk belongs to based on character positions.
        
        Args:
            chunk_start: Starting character position of the chunk
            chunk_end: Ending character position of the chunk
            page_mappings: List of page mapping dictionaries
            
        Returns:
            Dictionary with page_start, page_end, and page_boundaries
        """
        page_start = None
        page_end = None
        pages_covered = []
        
        for page_info in page_mappings:
            page_num = page_info['page_number']
            page_char_start = page_info['start_char']
            page_char_end = page_info['end_char']
            
            # Check if chunk overlaps with this page
            if chunk_start < page_char_end and chunk_end > page_char_start:
                if page_start is None:
                    page_start = page_num
                page_end = page_num
                
                # Calculate overlap percentage
                overlap_start = max(chunk_start, page_char_start)
                overlap_end = min(chunk_end, page_char_end)
                overlap_length = overlap_end - overlap_start
                chunk_length = chunk_end - chunk_start
                
                if chunk_length > 0:
                    overlap_percentage = (overlap_length / chunk_length) * 100
                    pages_covered.append({
                        'page': page_num,
                        'percentage': round(overlap_percentage, 2)
                    })
        
        return {
            'page_start': page_start,
            'page_end': page_end,
            'page_boundaries': pages_covered
        }
    
    def extract_text_blocks_with_pages(self, file_path: str) -> List[Dict]:
        """
        Extract text blocks (paragraphs) with their page information.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of text blocks with page and position information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        blocks = []
        
        try:
            with fitz.open(file_path) as doc:
                for page_num, page in enumerate(doc, start=1):
                    # Get text blocks (paragraphs) with position info
                    page_blocks = page.get_text("blocks")
                    
                    for block in page_blocks:
                        if len(block) >= 5 and block[4].strip():  # Valid text block
                            blocks.append({
                                'text': block[4].strip(),
                                'page': page_num,
                                'bbox': {
                                    'x0': block[0],
                                    'y0': block[1],
                                    'x1': block[2],
                                    'y1': block[3]
                                }
                            })
                
                logger.info(f"Extracted {len(blocks)} text blocks from {len(doc)} pages")
                return blocks
                
        except Exception as e:
            logger.error(f"PyMuPDF block extraction failed: {e}")
            raise