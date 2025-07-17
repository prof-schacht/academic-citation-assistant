"""Paper processing service using MarkItDown for text extraction."""
import os
import re
from typing import List, Dict, Optional, Tuple
from uuid import UUID
import asyncio
from markitdown import MarkItDown

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Paper, PaperChunk
from app.services.embedding import EmbeddingService
# TextChunkingService is defined in this file
from app.core.config import settings
from app.utils.logging_utils import log_async_info, log_async_error
from app.models.system_log import LogCategory
import logging

logger = logging.getLogger(__name__)


class PaperProcessorService:
    """Service for processing uploaded papers."""
    
    def __init__(self):
        self.markitdown = MarkItDown()
        self.embedding_service = EmbeddingService()
        self.chunking_service = TextChunkingService()
    
    @classmethod
    async def process_paper(cls, paper_id: str, file_path: str) -> None:
        """
        Process a paper file asynchronously.
        
        Steps:
        1. Extract text using MarkItDown
        2. Extract metadata from the text
        3. Chunk the text
        4. Generate embeddings
        5. Store everything in the database
        """
        processor = cls()
        
        async with AsyncSessionLocal() as db:
            try:
                # Get paper from database
                paper = await db.get(Paper, UUID(paper_id))
                if not paper:
                    logger.error(f"Paper {paper_id} not found")
                    return
                
                logger.info(f"Processing paper {paper_id}: {paper.title}")
                
                # Log processing start
                await log_async_info(
                    db,
                    LogCategory.PDF_PROCESSING,
                    f"Starting PDF processing for paper: {paper.title}",
                    entity_type="paper",
                    entity_id=str(paper_id),
                    details={"file_path": file_path}
                )
                
                # Extract text using MarkItDown
                markdown_text = processor._extract_text(file_path)
                if not markdown_text:
                    raise ValueError("Failed to extract text from file")
                
                # Extract metadata from the markdown
                metadata = processor._extract_metadata(markdown_text)
                
                # Update paper with extracted metadata
                paper.title = metadata.get('title', paper.title)
                paper.authors = metadata.get('authors', paper.authors)
                paper.abstract = metadata.get('abstract', paper.abstract)
                paper.year = metadata.get('year', paper.year)
                paper.full_text = markdown_text
                
                # Chunk the text (250 words with 50-word overlap for better granularity)
                chunks = processor.chunking_service.chunk_text(
                    markdown_text,
                    chunk_size=250,  # Reduced from 500 for better search granularity
                    overlap_size=50,
                    respect_sentences=True
                )
                
                logger.info(f"Created {len(chunks)} chunks for paper {paper_id}")
                
                # Delete existing chunks for this paper (in case of reprocessing)
                existing_chunks = await db.execute(
                    select(PaperChunk).where(PaperChunk.paper_id == UUID(paper_id))
                )
                for chunk in existing_chunks.scalars():
                    await db.delete(chunk)
                
                # Create and embed each chunk
                paper_chunks = []
                for i, chunk in enumerate(chunks):
                    # Generate embedding for this chunk
                    chunk_embedding = await processor.embedding_service.generate_embedding(chunk.content)
                    
                    # Create PaperChunk record
                    paper_chunk = PaperChunk(
                        paper_id=UUID(paper_id),
                        content=chunk.content,
                        chunk_index=i,
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        word_count=chunk.word_count,
                        embedding=chunk_embedding,
                        section_title=chunk.section_title
                    )
                    db.add(paper_chunk)
                    paper_chunks.append(paper_chunk)
                    
                    # Log progress for long documents
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(chunks)} chunks for paper {paper_id}")
                
                # Also generate and store a main embedding for the paper (abstract or first chunk)
                embedding_text = paper.abstract if paper.abstract else chunks[0].content if chunks else ""
                if embedding_text:
                    embedding = await processor.embedding_service.generate_embedding(embedding_text)
                    paper.embedding = embedding
                
                # Mark as processed
                paper.is_processed = True
                paper.processing_error = None
                
                # Save everything
                await db.commit()
                
                logger.info(f"Successfully stored {len(paper_chunks)} chunks with embeddings for paper {paper_id}")
                
                # Log success
                await log_async_info(
                    db,
                    LogCategory.PDF_PROCESSING,
                    f"Successfully processed PDF for paper: {paper.title}",
                    entity_type="paper",
                    entity_id=str(paper_id),
                    details={
                        "chunks_created": len(paper_chunks),
                        "text_length": len(markdown_text),
                        "has_abstract": bool(paper.abstract)
                    }
                )
                
                logger.info(f"Successfully processed paper {paper_id}")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper_id}: {str(e)}")
                
                # Log error
                await log_async_error(
                    db,
                    LogCategory.PDF_PROCESSING,
                    f"Failed to process PDF for paper: {paper.title if paper else paper_id}",
                    e,
                    entity_type="paper",
                    entity_id=str(paper_id),
                    details={"file_path": file_path, "error": str(e)}
                )
                
                # Update paper with error
                if paper:
                    paper.processing_error = str(e)
                    await db.commit()
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from file using MarkItDown."""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")
            
            result = self.markitdown.convert(file_path)
            return result.text_content
        except Exception as e:
            logger.error(f"MarkItDown extraction failed: {e}")
            if isinstance(e, FileNotFoundError):
                raise
            return ""
    
    def _extract_metadata(self, markdown_text: str) -> Dict[str, any]:
        """
        Extract metadata from markdown text.
        
        Looks for common patterns in academic papers:
        - Title (usually first heading)
        - Authors (often after title)
        - Abstract (section marked as abstract)
        - Year (from dates in text)
        """
        metadata = {}
        
        lines = markdown_text.split('\n')
        
        # Extract title - try multiple strategies
        # 1. Look for first # heading
        for line in lines:
            if line.startswith('# ') and 'title' not in metadata:
                metadata['title'] = line[2:].strip()
                break
        
        # 2. If no heading found, look for title-like patterns in first 50 lines
        if 'title' not in metadata:
            # Look for the first substantial text block
            found_content = False
            potential_titles = []
            
            for i, line in enumerate(lines[:50]):
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    continue
                
                # Skip common headers/footers
                if any(skip in stripped.lower() for skip in ['page', 'copyright', 'doi:', 'isbn', 'issn', 'vol.', 'no.']):
                    continue
                
                # Skip URLs and emails
                if any(pattern in stripped for pattern in ['http://', 'https://', 'www.', '@']):
                    continue
                
                # If we find a substantial line (10+ chars), consider it
                if len(stripped) >= 10:
                    found_content = True
                    
                    # Check if it looks like a title (no ending punctuation, reasonable length)
                    if (len(stripped) < 200 and 
                        not stripped.endswith(('.', ',', ';', ':', '?', '!')) and
                        not stripped.startswith(('Figure', 'Table', 'Algorithm'))):
                        
                        # Give higher priority to lines that are followed by author-like patterns
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and (',' in next_line or ' and ' in next_line.lower()):
                                metadata['title'] = stripped
                                break
                        
                        # Also consider lines that are in all caps or title case
                        words = stripped.split()
                        if len(words) >= 2:
                            # Check if most words start with capital (title case)
                            capitalized_words = sum(1 for word in words if word and word[0].isupper())
                            if capitalized_words >= len(words) * 0.7:
                                potential_titles.append(stripped)
                    
                    # If we've found substantial content but no title after 10 lines, use the best candidate
                    if found_content and i > 10 and potential_titles and 'title' not in metadata:
                        metadata['title'] = potential_titles[0]
                        break
        
        # Extract abstract (look for Abstract section)
        abstract_pattern = re.compile(r'^#+\s*Abstract\s*$', re.IGNORECASE)
        in_abstract = False
        abstract_lines = []
        
        for i, line in enumerate(lines):
            if abstract_pattern.match(line):
                in_abstract = True
                continue
            elif in_abstract and line.startswith('#'):
                # End of abstract section
                break
            elif in_abstract and line.strip():
                abstract_lines.append(line.strip())
        
        if abstract_lines:
            metadata['abstract'] = ' '.join(abstract_lines)
        
        # Extract authors (heuristic: look for lines with multiple commas near the title)
        if 'title' in metadata:
            title_index = next((i for i, line in enumerate(lines) if metadata['title'] in line), -1)
            if title_index >= 0:
                # Check next few lines for author-like patterns
                for i in range(title_index + 1, min(title_index + 10, len(lines))):
                    line = lines[i].strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip lines that are clearly not authors
                    if any(skip in line.lower() for skip in ['abstract', 'introduction', 'keywords', 'doi:', 'copyright']):
                        continue
                    
                    # Look for author patterns
                    # 1. Lines with commas (e.g., "John Doe, Jane Smith, Bob Johnson")
                    if ',' in line:
                        # Clean up the line - remove numbers, affiliations in parentheses
                        clean_line = re.sub(r'\([^)]*\)', '', line)  # Remove parentheses
                        clean_line = re.sub(r'\d+', '', clean_line)  # Remove numbers
                        clean_line = re.sub(r'\*', '', clean_line)    # Remove asterisks
                        
                        potential_authors = [a.strip() for a in clean_line.split(',')]
                        # Filter out empty entries and check if they look like names
                        potential_authors = [a for a in potential_authors if a and len(a.split()) <= 5 and len(a) > 2]
                        
                        if len(potential_authors) >= 1:
                            metadata['authors'] = potential_authors
                            break
                    
                    # 2. Lines with "and" (e.g., "John Doe and Jane Smith")
                    elif ' and ' in line.lower():
                        clean_line = re.sub(r'\([^)]*\)', '', line)
                        clean_line = re.sub(r'\d+', '', clean_line)
                        clean_line = re.sub(r'\*', '', clean_line)
                        
                        potential_authors = re.split(r'\s+and\s+', clean_line, flags=re.IGNORECASE)
                        potential_authors = [a.strip() for a in potential_authors if a.strip() and len(a.strip().split()) <= 5]
                        
                        if len(potential_authors) >= 1:
                            metadata['authors'] = potential_authors
                            break
        
        # Extract year (look for 4-digit years)
        year_pattern = re.compile(r'\b(19\d{2}|20\d{2})\b')
        years = year_pattern.findall(markdown_text)
        if years:
            # Use the most recent year found
            metadata['year'] = max(int(year) for year in years)
        
        return metadata


class TextChunkingService:
    """Service for chunking text intelligently."""
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap_size: int = 50,
        respect_sentences: bool = True
    ) -> List['TextChunk']:
        """
        Chunk text into smaller pieces with overlap.
        
        Args:
            text: The text to chunk
            chunk_size: Target size in words
            overlap_size: Number of words to overlap
            respect_sentences: Don't break sentences
        
        Returns:
            List of TextChunk objects
        """
        # Simple implementation for now
        # TODO: Implement proper sentence-aware chunking
        
        words = text.split()
        chunks = []
        
        i = 0
        chunk_id = 0
        char_offset = 0
        
        # Extract section headers (simple heuristic)
        lines = text.split('\n')
        current_section = None
        
        while i < len(words):
            # Get chunk_size words
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate character positions
            start_char = char_offset
            end_char = start_char + len(chunk_text)
            
            # Try to detect section title (very simple heuristic)
            chunk_lines = chunk_text.split('\n')
            if chunk_lines and len(chunk_lines[0]) < 100 and chunk_lines[0].strip():
                # Check if first line might be a section header
                first_line = chunk_lines[0].strip()
                if any(header in first_line.lower() for header in 
                       ['introduction', 'abstract', 'method', 'result', 'discussion', 
                        'conclusion', 'reference', 'background', 'related work']):
                    current_section = first_line
            
            chunks.append(TextChunk(
                id=f"chunk_{chunk_id}",
                content=chunk_text,
                position=chunk_id,
                word_count=len(chunk_words),
                start_char=start_char,
                end_char=end_char,
                section_title=current_section
            ))
            
            # Move forward by (chunk_size - overlap_size)
            i += chunk_size - overlap_size
            chunk_id += 1
            
            # Update character offset (approximate)
            if i < len(words):
                char_offset = text.find(' '.join(words[i:i+1]))
        
        return chunks


class TextChunk:
    """Represents a chunk of text from a paper."""
    
    def __init__(self, id: str, content: str, position: int, word_count: int, 
                 start_char: int = 0, end_char: int = 0, section_title: Optional[str] = None):
        self.id = id
        self.content = content
        self.position = position
        self.word_count = word_count
        self.start_char = start_char
        self.end_char = end_char
        self.section_title = section_title