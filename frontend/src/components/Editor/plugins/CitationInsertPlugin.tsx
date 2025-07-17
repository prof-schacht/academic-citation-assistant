/**
 * Plugin to handle citation insertion from external components
 */

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $createTextNode, $insertNodes, $createParagraphNode, $getRoot } from 'lexical';
import type { CitationSuggestion } from '../../../types';

interface CitationInsertPluginProps {
  onRegisterInsertHandler?: (handler: (citation: CitationSuggestion) => void) => void;
}

export function CitationInsertPlugin({ onRegisterInsertHandler }: CitationInsertPluginProps): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (!onRegisterInsertHandler) return;

    const insertCitation = (citation: CitationSuggestion) => {
      editor.update(() => {
        const selection = $getSelection();
        
        // Format citation text based on available metadata
        let citationText = '';
        
        // If we have proper metadata, format it nicely
        if (citation.title && citation.title !== citation.paperId) {
          // Author format: (First Author et al., Year) or (Author1 & Author2, Year)
          let authorPart = '';
          if (citation.authors && citation.authors.length > 0) {
            if (citation.authors.length === 1) {
              authorPart = citation.authors[0];
            } else if (citation.authors.length === 2) {
              authorPart = `${citation.authors[0]} & ${citation.authors[1]}`;
            } else {
              authorPart = `${citation.authors[0]} et al.`;
            }
          } else {
            authorPart = 'Unknown';
          }
          
          const yearPart = citation.year || 'n.d.';
          citationText = `(${authorPart}, ${yearPart})`;
        } else {
          // Fallback: use paper ID or filename
          citationText = `[${citation.paperId}]`;
        }
        
        // Create text node with citation
        const citationNode = $createTextNode(citationText);
        
        if (selection) {
          // Insert at current cursor position
          $insertNodes([citationNode]);
        } else {
          // No selection, append to the end
          const root = $getRoot();
          const paragraph = $createParagraphNode();
          paragraph.append(citationNode);
          root.append(paragraph);
        }
        
        // Focus back on editor
        editor.focus();
      });
    };

    onRegisterInsertHandler(insertCitation);
  }, [editor, onRegisterInsertHandler]);

  return null;
}