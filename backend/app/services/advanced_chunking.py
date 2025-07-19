"""
Advanced chunking service with sentence-aware and hierarchical chunking strategies.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
import logging
from enum import Enum
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
from sentence_transformers import SentenceTransformer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except:
        pass

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies."""
    SIMPLE_WORD = "simple_word"
    SENTENCE_AWARE = "sentence_aware"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"
    ELEMENT_BASED = "element_based"


@dataclass
class EnhancedTextChunk:
    """Enhanced text chunk with additional metadata."""
    text: str
    start_char: int
    end_char: int
    chunk_index: int
    word_count: int
    sentence_count: int
    section: Optional[str] = None
    subsection: Optional[str] = None
    chunk_type: str = "body"  # abstract, intro, methods, results, discussion, conclusion, references
    semantic_score: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AdvancedChunkingService:
    """Advanced text chunking service with multiple strategies."""
    
    # Common academic section patterns
    SECTION_PATTERNS = [
        (r'^abstract\s*$', 'abstract'),
        (r'^introduction\s*$', 'intro'),
        (r'^background\s*$', 'intro'),
        (r'^(literature review|related work)\s*$', 'intro'),
        (r'^(methodology|methods|materials and methods)\s*$', 'methods'),
        (r'^(results|findings)\s*$', 'results'),
        (r'^discussion\s*$', 'discussion'),
        (r'^(conclusion|conclusions)\s*$', 'conclusion'),
        (r'^references\s*$', 'references'),
        (r'^bibliography\s*$', 'references'),
    ]
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000,
        embedding_model: Optional[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Initialize embedding model for semantic chunking
        self.embedding_model = None
        if embedding_model:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
    
    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE_AWARE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTextChunk]:
        """
        Chunk text using the specified strategy.
        
        Args:
            text: The text to chunk
            strategy: The chunking strategy to use
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of enhanced text chunks
        """
        if strategy == ChunkingStrategy.SIMPLE_WORD:
            return self._simple_word_chunking(text, metadata)
        elif strategy == ChunkingStrategy.SENTENCE_AWARE:
            return self._sentence_aware_chunking(text, metadata)
        elif strategy == ChunkingStrategy.SEMANTIC:
            return self._semantic_chunking(text, metadata)
        elif strategy == ChunkingStrategy.HIERARCHICAL:
            return self._hierarchical_chunking(text, metadata)
        elif strategy == ChunkingStrategy.ELEMENT_BASED:
            return self._element_based_chunking(text, metadata)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def _simple_word_chunking(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTextChunk]:
        """Simple word-based chunking (legacy compatibility)."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate character positions
            start_char = len(' '.join(words[:i])) + (1 if i > 0 else 0)
            end_char = start_char + len(chunk_text)
            
            chunks.append(EnhancedTextChunk(
                text=chunk_text,
                start_char=start_char,
                end_char=end_char,
                chunk_index=len(chunks),
                word_count=len(chunk_words),
                sentence_count=len(sent_tokenize(chunk_text)),
                metadata=metadata
            ))
        
        return chunks
    
    def _sentence_aware_chunking(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTextChunk]:
        """Chunk text while respecting sentence boundaries."""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_word_count = 0
        current_start_char = 0
        
        for i, sentence in enumerate(sentences):
            sentence_words = word_tokenize(sentence)
            sentence_word_count = len(sentence_words)
            
            # Check if adding this sentence would exceed chunk size
            if current_word_count + sentence_word_count > self.chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = ' '.join(current_chunk)
                chunks.append(self._create_enhanced_chunk(
                    chunk_text, current_start_char, len(chunks), text, metadata
                ))
                
                # Handle overlap by including last few sentences
                overlap_sentences = []
                overlap_word_count = 0
                for j in range(len(current_chunk) - 1, -1, -1):
                    overlap_sentences.insert(0, current_chunk[j])
                    overlap_word_count += len(word_tokenize(current_chunk[j]))
                    if overlap_word_count >= self.chunk_overlap:
                        break
                
                # Start new chunk with overlap
                current_chunk = overlap_sentences
                current_word_count = overlap_word_count
                current_start_char = text.find(current_chunk[0], current_start_char)
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_word_count += sentence_word_count
        
        # Create final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(self._create_enhanced_chunk(
                chunk_text, current_start_char, len(chunks), text, metadata
            ))
        
        return chunks
    
    def _semantic_chunking(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTextChunk]:
        """Chunk text based on semantic similarity between sentences."""
        if not self.embedding_model:
            logger.warning("No embedding model available, falling back to sentence-aware chunking")
            return self._sentence_aware_chunking(text, metadata)
        
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return self._sentence_aware_chunking(text, metadata)
        
        # Generate embeddings for all sentences
        embeddings = self.embedding_model.encode(sentences)
        
        chunks = []
        current_chunk = [sentences[0]]
        current_start_char = 0
        current_embedding = embeddings[0]
        
        similarity_threshold = 0.7  # Adjustable threshold
        
        for i in range(1, len(sentences)):
            # Calculate similarity between current chunk and next sentence
            chunk_embedding = np.mean([current_embedding, embeddings[i]], axis=0)
            similarity = np.dot(current_embedding, embeddings[i]) / (
                np.linalg.norm(current_embedding) * np.linalg.norm(embeddings[i])
            )
            
            # Check if we should start a new chunk
            word_count = sum(len(word_tokenize(s)) for s in current_chunk)
            
            if (similarity < similarity_threshold and word_count >= self.min_chunk_size) or \
               word_count >= self.chunk_size:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = self._create_enhanced_chunk(
                    chunk_text, current_start_char, len(chunks), text, metadata
                )
                chunk.semantic_score = float(similarity)
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [sentences[i]]
                current_start_char = text.find(sentences[i], current_start_char + len(chunk_text))
                current_embedding = embeddings[i]
            else:
                # Add to current chunk
                current_chunk.append(sentences[i])
                current_embedding = chunk_embedding
        
        # Create final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = self._create_enhanced_chunk(
                chunk_text, current_start_char, len(chunks), text, metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _hierarchical_chunking(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTextChunk]:
        """Chunk text hierarchically by detecting sections and subsections."""
        lines = text.split('\n')
        sections = self._detect_sections(lines)
        chunks = []
        
        for section_name, section_start, section_end in sections:
            section_text = '\n'.join(lines[section_start:section_end])
            
            # Apply sentence-aware chunking within each section
            section_chunks = self._sentence_aware_chunking(section_text, metadata)
            
            # Update chunks with section information
            for chunk in section_chunks:
                chunk.section = section_name
                chunk.chunk_type = self._determine_chunk_type(section_name)
                chunk.chunk_index = len(chunks)
                chunks.append(chunk)
        
        return chunks
    
    def _element_based_chunking(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTextChunk]:
        """Chunk text based on document elements (paragraphs, sections, etc.)."""
        # Split by double newlines to get paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_section = None
        char_offset = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                char_offset += len(paragraph) + 2  # Account for newlines
                continue
            
            # Check if this paragraph is a section header
            first_line = paragraph.split('\n')[0].strip().lower()
            for pattern, section_type in self.SECTION_PATTERNS:
                if re.match(pattern, first_line):
                    current_section = section_type
                    break
            
            # Create chunk from paragraph
            chunk = self._create_enhanced_chunk(
                paragraph.strip(), char_offset, len(chunks), text, metadata
            )
            chunk.section = current_section
            chunk.chunk_type = current_section if current_section else "body"
            
            # If paragraph is too large, split it further
            if chunk.word_count > self.max_chunk_size:
                sub_chunks = self._sentence_aware_chunking(paragraph, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.section = current_section
                    sub_chunk.chunk_type = chunk.chunk_type
                    sub_chunk.chunk_index = len(chunks)
                    chunks.append(sub_chunk)
            else:
                chunks.append(chunk)
            
            char_offset += len(paragraph) + 2
        
        return chunks
    
    def _detect_sections(self, lines: List[str]) -> List[Tuple[str, int, int]]:
        """Detect sections in the text based on common patterns."""
        sections = []
        current_section = "introduction"
        section_start = 0
        
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            
            # Check if this line matches any section pattern
            for pattern, section_type in self.SECTION_PATTERNS:
                if re.match(pattern, line_lower):
                    # End previous section
                    if sections:
                        sections[-1] = (sections[-1][0], sections[-1][1], i)
                    else:
                        sections.append((current_section, section_start, i))
                    
                    # Start new section
                    current_section = section_type
                    section_start = i + 1
                    sections.append((current_section, section_start, -1))
                    break
        
        # Close the last section
        if sections:
            sections[-1] = (sections[-1][0], sections[-1][1], len(lines))
        else:
            sections.append((current_section, 0, len(lines)))
        
        return sections
    
    def _determine_chunk_type(self, section_name: str) -> str:
        """Determine chunk type from section name."""
        section_lower = section_name.lower() if section_name else ""
        
        for pattern, chunk_type in self.SECTION_PATTERNS:
            if re.match(pattern, section_lower):
                return chunk_type.split()[0]  # Get first word as chunk type
        
        return "body"
    
    def _create_enhanced_chunk(
        self,
        text: str,
        start_char: int,
        chunk_index: int,
        full_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EnhancedTextChunk:
        """Create an enhanced text chunk with calculated metadata."""
        end_char = start_char + len(text)
        
        # Ensure we have the correct character positions
        actual_start = full_text.find(text, start_char)
        if actual_start != -1:
            start_char = actual_start
            end_char = start_char + len(text)
        
        return EnhancedTextChunk(
            text=text,
            start_char=start_char,
            end_char=end_char,
            chunk_index=chunk_index,
            word_count=len(word_tokenize(text)),
            sentence_count=len(sent_tokenize(text)),
            metadata=metadata
        )
    
    def merge_small_chunks(
        self, chunks: List[EnhancedTextChunk], min_size: Optional[int] = None
    ) -> List[EnhancedTextChunk]:
        """Merge chunks that are smaller than the minimum size."""
        if not chunks:
            return chunks
        
        min_size = min_size or self.min_chunk_size
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
            elif current_chunk.word_count < min_size:
                # Merge with current chunk
                current_chunk = EnhancedTextChunk(
                    text=current_chunk.text + " " + chunk.text,
                    start_char=current_chunk.start_char,
                    end_char=chunk.end_char,
                    chunk_index=len(merged_chunks),
                    word_count=current_chunk.word_count + chunk.word_count,
                    sentence_count=current_chunk.sentence_count + chunk.sentence_count,
                    section=current_chunk.section,
                    subsection=current_chunk.subsection,
                    chunk_type=current_chunk.chunk_type,
                    metadata={**current_chunk.metadata, **chunk.metadata} if chunk.metadata else current_chunk.metadata
                )
            else:
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        return merged_chunks