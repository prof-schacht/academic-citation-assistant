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
from app.models import Paper
from app.services.embedding import EmbeddingService
from app.services.text_chunking import TextChunkingService
from app.core.config import settings
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
                
                # Chunk the text (500 words with 50-word overlap as per Issue #6)
                chunks = processor.chunking_service.chunk_text(
                    markdown_text,
                    chunk_size=500,
                    overlap_size=50,
                    respect_sentences=True
                )
                
                logger.info(f"Created {len(chunks)} chunks for paper {paper_id}")
                
                # Generate embedding for the abstract or first chunk
                embedding_text = paper.abstract if paper.abstract else chunks[0].content if chunks else ""
                if embedding_text:
                    embedding = await processor.embedding_service.generate_embedding(embedding_text)
                    paper.embedding = embedding
                
                # Mark as processed
                paper.is_processed = True
                paper.processing_error = None
                
                # Save paper updates
                await db.commit()
                
                # Store chunks (TODO: Create PaperChunk model and store chunks)
                # For now, we're just storing the main embedding
                
                logger.info(f"Successfully processed paper {paper_id}")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper_id}: {str(e)}")
                
                # Update paper with error
                if paper:
                    paper.processing_error = str(e)
                    await db.commit()
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from file using MarkItDown."""
        try:
            result = self.markitdown.convert(file_path)
            return result.text
        except Exception as e:
            logger.error(f"MarkItDown extraction failed: {e}")
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
        
        # Extract title (first # heading)
        for line in lines:
            if line.startswith('# ') and 'title' not in metadata:
                metadata['title'] = line[2:].strip()
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
                    if ',' in line and not line.startswith('#'):
                        # Might be authors
                        potential_authors = [a.strip() for a in line.split(',')]
                        if all(len(a.split()) <= 4 for a in potential_authors):  # Names are usually 1-4 words
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
        
        while i < len(words):
            # Get chunk_size words
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append(TextChunk(
                id=f"chunk_{chunk_id}",
                content=chunk_text,
                position=chunk_id,
                word_count=len(chunk_words)
            ))
            
            # Move forward by (chunk_size - overlap_size)
            i += chunk_size - overlap_size
            chunk_id += 1
        
        return chunks


class TextChunk:
    """Represents a chunk of text from a paper."""
    
    def __init__(self, id: str, content: str, position: int, word_count: int):
        self.id = id
        self.content = content
        self.position = position
        self.word_count = word_count