"""Improved metadata extraction for academic papers."""
import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImprovedMetadataExtractor:
    """Enhanced metadata extraction with better heuristics for academic papers."""
    
    def extract_metadata(self, text: str) -> Dict[str, any]:
        """
        Extract metadata from paper text using improved heuristics.
        
        Returns:
            Dict with title, authors, abstract, year
        """
        lines = text.split('\n')
        metadata = {}
        
        # Try multiple strategies for title extraction
        title_info = self._extract_title_advanced(lines)
        if title_info:
            metadata['title'] = title_info[0]
            title_line_idx = title_info[1]
            
            # Extract authors based on title location
            authors = self._extract_authors_near_title(lines, title_line_idx)
            if authors:
                metadata['authors'] = authors
        
        # Extract abstract
        abstract = self._extract_abstract(lines)
        if abstract:
            metadata['abstract'] = abstract
            
        # Extract year
        year = self._extract_year(text)
        if year:
            metadata['year'] = year
            
        return metadata
    
    def _extract_title_advanced(self, lines: List[str]) -> Optional[Tuple[str, int]]:
        """
        Extract title using multiple advanced strategies.
        
        Returns:
            Tuple of (title, line_index) or None
        """
        # Strategy 1: Look for the largest text block in the first part of the document
        title_candidates = []
        
        # First, try markdown headings
        for i, line in enumerate(lines[:100]):
            if line.startswith('# ') and len(line.strip()) > 10:
                clean_title = line[2:].strip()
                # Skip if it's a section heading
                if not any(word in clean_title.lower() for word in ['abstract', 'introduction', 'references', 'acknowledgments']):
                    return (clean_title, i)
        
        # Strategy 2: Look for title patterns in first 50 lines
        in_header_section = True
        found_substantial_text = False
        
        for i, line in enumerate(lines[:50]):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
                
            # Skip obvious non-title content
            if self._is_header_footer(stripped):
                continue
                
            # Skip dates, URLs, emails
            if self._contains_metadata_elements(stripped):
                continue
            
            # Look for title characteristics
            if len(stripped) >= 10:
                found_substantial_text = True
                
                # Check if this could be a title
                if self._looks_like_title(stripped, lines, i):
                    title_candidates.append((stripped, i, self._calculate_title_score(stripped, lines, i)))
        
        # Sort candidates by score and return the best one
        if title_candidates:
            title_candidates.sort(key=lambda x: x[2], reverse=True)
            best_candidate = title_candidates[0]
            return (best_candidate[0], best_candidate[1])
        
        return None
    
    def _looks_like_title(self, text: str, lines: List[str], index: int) -> bool:
        """Check if text looks like a paper title."""
        # Length constraints
        if len(text) < 10 or len(text) > 300:
            return False
            
        # Should not end with punctuation (except ? or !)
        if text.endswith(('.', ',', ';', ':')):
            return False
            
        # Should not start with common non-title words
        non_title_starts = ['figure', 'table', 'algorithm', 'equation', 'section', 'chapter']
        if any(text.lower().startswith(word) for word in non_title_starts):
            return False
            
        # Check capitalization pattern
        words = text.split()
        if len(words) >= 2:
            # Count capitalized words (excluding short words)
            significant_words = [w for w in words if len(w) > 3]
            if significant_words:
                capitalized = sum(1 for w in significant_words if w[0].isupper())
                if capitalized / len(significant_words) > 0.5:
                    return True
        
        # Check if followed by author-like content
        if index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if self._looks_like_authors(next_line):
                return True
                
        return len(words) >= 3  # At least 3 words
    
    def _calculate_title_score(self, text: str, lines: List[str], index: int) -> float:
        """Calculate a score for how likely this text is to be the title."""
        score = 0.0
        
        # Length score (prefer medium length titles)
        optimal_length = 100
        length_diff = abs(len(text) - optimal_length)
        score += max(0, 100 - length_diff) / 100
        
        # Position score (prefer earlier in document)
        score += (50 - index) / 50 if index < 50 else 0
        
        # Capitalization score
        words = text.split()
        if words:
            cap_ratio = sum(1 for w in words if w and w[0].isupper()) / len(words)
            score += cap_ratio
        
        # Following line score
        if index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if self._looks_like_authors(next_line):
                score += 2.0
            elif not next_line:  # Empty line after
                score += 0.5
                
        # Question mark bonus (research questions are common in titles)
        if '?' in text:
            score += 0.5
            
        # Keyword bonus
        title_keywords = ['analysis', 'study', 'approach', 'method', 'system', 'framework', 
                         'investigation', 'examination', 'review', 'survey', 'model']
        if any(keyword in text.lower() for keyword in title_keywords):
            score += 0.3
            
        return score
    
    def _is_header_footer(self, text: str) -> bool:
        """Check if text is likely a header or footer."""
        lower_text = text.lower()
        patterns = ['page ', 'copyright', '©', 'all rights reserved', 
                   'preprint', 'arxiv:', 'doi:', 'isbn', 'issn', 
                   'vol.', 'no.', 'pp.', 'journal', 'conference', 'proceedings']
        return any(pattern in lower_text for pattern in patterns)
    
    def _contains_metadata_elements(self, text: str) -> bool:
        """Check if text contains metadata elements."""
        # URLs
        if any(pattern in text for pattern in ['http://', 'https://', 'www.', '@']):
            return True
        # Dates in common formats
        if re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text):
            return True
        # Email addresses
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            return True
        return False
    
    def _looks_like_authors(self, text: str) -> bool:
        """Check if text looks like an author line."""
        if not text or len(text) < 5:
            return False
            
        # Common author patterns
        if ',' in text or ' and ' in text.lower():
            # Remove common suffixes and check if names remain
            clean_text = re.sub(r'\([^)]*\)', '', text)  # Remove parentheses
            clean_text = re.sub(r'[0-9\*†‡§¶]+', '', clean_text)  # Remove numbers and symbols
            
            # Split by commas or 'and'
            if ',' in clean_text:
                parts = [p.strip() for p in clean_text.split(',')]
            else:
                parts = re.split(r'\s+and\s+', clean_text, flags=re.IGNORECASE)
            
            # Check if parts look like names
            valid_parts = 0
            for part in parts:
                words = part.strip().split()
                if 1 <= len(words) <= 5:  # Names typically have 1-5 words
                    valid_parts += 1
                    
            return valid_parts >= 1 and valid_parts >= len(parts) * 0.5
            
        return False
    
    def _extract_authors_near_title(self, lines: List[str], title_idx: int) -> Optional[List[str]]:
        """Extract authors near the title line."""
        # Look in the next 15 lines after title
        for i in range(title_idx + 1, min(title_idx + 15, len(lines))):
            line = lines[i].strip()
            
            if not line:
                continue
                
            # Skip if it's clearly not authors
            skip_words = ['abstract', 'introduction', 'keywords', 'doi:', 'copyright', 
                         'received', 'accepted', 'published', 'corresponding']
            if any(word in line.lower() for word in skip_words):
                continue
                
            # Try to extract authors
            authors = self._parse_author_line(line)
            if authors:
                return authors
                
        return None
    
    def _parse_author_line(self, line: str) -> Optional[List[str]]:
        """Parse a line to extract author names."""
        # Clean the line
        clean_line = re.sub(r'\([^)]*\)', '', line)  # Remove parentheses
        clean_line = re.sub(r'[0-9\*†‡§¶]+', '', clean_line)  # Remove numbers and symbols
        clean_line = clean_line.strip()
        
        if not clean_line:
            return None
            
        authors = []
        
        # Try comma separation first
        if ',' in clean_line:
            parts = [p.strip() for p in clean_line.split(',')]
            for part in parts:
                if self._is_valid_name(part):
                    authors.append(part)
        # Try 'and' separation
        elif ' and ' in clean_line.lower():
            parts = re.split(r'\s+and\s+', clean_line, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if self._is_valid_name(part):
                    authors.append(part)
        # Single author
        elif self._is_valid_name(clean_line):
            authors.append(clean_line)
            
        return authors if authors else None
    
    def _is_valid_name(self, text: str) -> bool:
        """Check if text could be a person's name."""
        if not text:
            return False
            
        words = text.split()
        # Names typically have 1-5 words
        if not (1 <= len(words) <= 5):
            return False
            
        # At least one word should start with capital
        if not any(w[0].isupper() for w in words if w):
            return False
            
        # Shouldn't contain certain characters
        if any(char in text for char in ['@', '/', '\\', '|', '<', '>', '[', ']', '{', '}']):
            return False
            
        return True
    
    def _extract_abstract(self, lines: List[str]) -> Optional[str]:
        """Extract abstract section."""
        abstract_lines = []
        in_abstract = False
        
        for i, line in enumerate(lines):
            # Check for abstract heading
            if re.match(r'^(#+\s*)?abstract\s*$', line.strip(), re.IGNORECASE):
                in_abstract = True
                continue
            elif in_abstract:
                # Stop at next section
                if line.startswith('#') or re.match(r'^\d+\.?\s+[A-Z]', line):
                    break
                elif line.strip():
                    abstract_lines.append(line.strip())
                    
        if abstract_lines:
            return ' '.join(abstract_lines)
            
        # Alternative: Look for "Abstract" followed by text on same/next line
        for i, line in enumerate(lines):
            if 'abstract' in line.lower() and i + 1 < len(lines):
                # Check if abstract starts on same line
                match = re.match(r'^abstract[:\s]+(.+)$', line, re.IGNORECASE)
                if match:
                    abstract_text = match.group(1).strip()
                    if len(abstract_text) > 50:
                        return abstract_text
                # Check next lines
                else:
                    next_lines = []
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if lines[j].strip():
                            next_lines.append(lines[j].strip())
                        else:
                            break
                    if next_lines and len(' '.join(next_lines)) > 50:
                        return ' '.join(next_lines)
                        
        return None
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract publication year."""
        # Look for 4-digit years
        year_pattern = re.compile(r'\b(19[5-9]\d|20[0-2]\d)\b')
        years = year_pattern.findall(text)
        
        if years:
            # Convert to integers and get the most recent
            year_ints = [int(y) for y in years]
            # Filter out unlikely years
            current_year = 2025
            valid_years = [y for y in year_ints if 1950 <= y <= current_year]
            if valid_years:
                return max(valid_years)
                
        return None