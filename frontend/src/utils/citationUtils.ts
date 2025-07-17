/**
 * Utilities for citation formatting and key generation
 */

import type { CitationSuggestion } from '../types';

/**
 * Generate a LaTeX-style citation key from paper metadata
 * Format: FirstAuthorLastName + Year + FirstWordOfTitle
 * Example: "Smith2023Machine"
 */
export function generateCitationKey(citation: CitationSuggestion): string {
  let key = '';

  // Extract first author's last name
  if (citation.authors && citation.authors.length > 0) {
    const firstAuthor = citation.authors[0];
    // Try to extract last name (assume it's the last word)
    const nameParts = firstAuthor.trim().split(' ');
    const lastName = nameParts[nameParts.length - 1];
    key += lastName.replace(/[^a-zA-Z]/g, '');
  } else {
    key += 'Unknown';
  }

  // Add year
  key += citation.year || 'nd';

  // Add first significant word from title
  if (citation.title) {
    // Remove common words and get first significant word
    const titleWords = citation.title
      .split(' ')
      .filter(word => {
        const lower = word.toLowerCase();
        return !['the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but'].includes(lower);
      });
    
    if (titleWords.length > 0) {
      // Take first significant word, remove non-alphanumeric
      const firstWord = titleWords[0].replace(/[^a-zA-Z0-9]/g, '');
      if (firstWord.length > 0) {
        // Capitalize first letter
        key += firstWord.charAt(0).toUpperCase() + firstWord.slice(1).toLowerCase();
      }
    }
  }

  // If we still don't have a good key, use paper ID
  if (key === 'Unknownnd' || key.length < 5) {
    // Use first 8 chars of paper ID
    key = 'Paper_' + citation.paperId.substring(0, 8);
  }

  return key;
}

/**
 * Find the end of the current sentence from a given position
 */
export function findSentenceEnd(text: string, position: number): number {
  // Look for sentence ending punctuation
  const sentenceEnders = ['.', '!', '?'];
  
  for (let i = position; i < text.length; i++) {
    if (sentenceEnders.includes(text[i])) {
      // Check if it's not an abbreviation (e.g., "Dr.", "Mr.", "etc.")
      if (i + 1 < text.length && text[i + 1] === ' ') {
        // Check if next character is uppercase or end of text
        if (i + 2 >= text.length || /[A-Z]/.test(text[i + 2])) {
          return i + 1; // Return position after the punctuation
        }
      } else if (i + 1 === text.length) {
        return i + 1; // End of text
      }
    }
  }
  
  // If no sentence ender found, return end of text
  return text.length;
}

/**
 * Check if a position is at the end of a sentence
 */
export function isEndOfSentence(text: string, position: number): boolean {
  if (position === 0) return false;
  
  const prevChar = text[position - 1];
  const sentenceEnders = ['.', '!', '?'];
  
  return sentenceEnders.includes(prevChar);
}