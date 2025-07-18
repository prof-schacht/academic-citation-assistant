"""Text analysis service for extracting context from editor content."""
import re
from typing import Optional, List
from dataclasses import dataclass
import nltk
from nltk.tokenize import sent_tokenize
import logging

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab', quiet=True)
    except:
        # Fallback to old punkt if punkt_tab fails
        try:
            nltk.download('punkt', quiet=True)
        except:
            logger.warning("Failed to download NLTK punkt tokenizer data")


@dataclass
class TextContext:
    """Represents the context around the current text."""
    current_sentence: str
    previous_sentence: Optional[str] = None
    next_sentence: Optional[str] = None
    paragraph: str = ""
    section: Optional[str] = None
    position: int = 0
    

class TextAnalysisService:
    """Service for analyzing and extracting context from text."""
    
    def __init__(self):
        self.min_sentence_length = 10
        self.context_window_size = 3  # sentences before and after
        
    def extract_context(self, text: str, editor_context: dict) -> TextContext:
        """Extract context from the current text and editor state."""
        # Clean the text
        cleaned_text = self.preprocess_text(text)
        
        # Get cursor position if available
        cursor_pos = editor_context.get("cursorPosition", len(text))
        
        # Extract sentences
        sentences = self._extract_sentences(cleaned_text)
        
        # Find current sentence based on cursor position
        current_idx = self._find_current_sentence_index(sentences, text, cursor_pos)
        
        # Build context
        context = TextContext(
            current_sentence=sentences[current_idx] if current_idx < len(sentences) else "",
            previous_sentence=sentences[current_idx - 1] if current_idx > 0 else None,
            next_sentence=sentences[current_idx + 1] if current_idx < len(sentences) - 1 else None,
            paragraph=self._extract_paragraph(text, cursor_pos),
            section=editor_context.get("section"),
            position=cursor_pos
        )
        
        return context
        
    def should_update_suggestions(self, old_text: str, new_text: str) -> bool:
        """Determine if text change warrants new suggestions."""
        # Skip if texts are too similar
        if old_text == new_text:
            return False
            
        # Check if significant change (more than just whitespace)
        old_clean = re.sub(r'\s+', ' ', old_text.strip())
        new_clean = re.sub(r'\s+', ' ', new_text.strip())
        
        # Calculate change ratio
        if not old_clean:
            return len(new_clean) > self.min_sentence_length
            
        change_ratio = self._calculate_change_ratio(old_clean, new_clean)
        
        # Update if change is significant (>20% different)
        return change_ratio > 0.2
        
    def preprocess_text(self, text: str) -> str:
        """Clean and prepare text for analysis."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep sentence endings
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        
        # Fix common issues
        text = re.sub(r'\.{2,}', '.', text)  # Multiple periods
        text = re.sub(r'\s+([\.!\?])', r'\1', text)  # Space before punctuation
        
        return text.strip()
        
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        try:
            sentences = sent_tokenize(text)
            # Filter out very short sentences
            return [s for s in sentences if len(s.strip()) >= self.min_sentence_length]
        except Exception as e:
            logger.error(f"Error tokenizing sentences: {e}")
            # Fallback to simple splitting
            return text.split('.')
            
    def _find_current_sentence_index(self, sentences: List[str], original_text: str, cursor_pos: int) -> int:
        """Find which sentence contains the cursor position."""
        if not sentences:
            return 0
            
        current_pos = 0
        for i, sentence in enumerate(sentences):
            # Find sentence in original text
            sentence_pos = original_text.find(sentence, current_pos)
            if sentence_pos == -1:
                continue
                
            sentence_end = sentence_pos + len(sentence)
            
            if cursor_pos <= sentence_end:
                return i
                
            current_pos = sentence_end
            
        # Default to last sentence
        return len(sentences) - 1
        
    def _extract_paragraph(self, text: str, cursor_pos: int) -> str:
        """Extract the paragraph containing the cursor position."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_pos = 0
        for paragraph in paragraphs:
            paragraph_end = current_pos + len(paragraph)
            
            if cursor_pos <= paragraph_end:
                return paragraph.strip()
                
            current_pos = paragraph_end + 2  # Account for double newline
            
        return paragraphs[-1].strip() if paragraphs else ""
        
    def _calculate_change_ratio(self, old_text: str, new_text: str) -> float:
        """Calculate how much the text has changed (0-1)."""
        if not old_text and not new_text:
            return 0.0
        if not old_text:
            return 1.0
        if not new_text:
            return 1.0
            
        # Simple character-based comparison
        max_len = max(len(old_text), len(new_text))
        
        # Count matching characters at same positions
        matches = sum(1 for i in range(min(len(old_text), len(new_text))) 
                     if old_text[i] == new_text[i])
        
        # Calculate change ratio
        return 1.0 - (matches / max_len)