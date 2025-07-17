/**
 * Plugin to handle citation insertion from external components
 */

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { 
  $getSelection, 
  $insertNodes, 
  $createParagraphNode, 
  $getRoot,
  $isRangeSelection,
  $setSelection,
  $createRangeSelection,
  $isTextNode,
  $createTextNode
} from 'lexical';
import { $createCitationNode } from '../nodes/CitationNode';
import { generateCitationKey, findSentenceEnd } from '../../../utils/citationUtils';
import type { CitationSuggestion } from '../../../types';

interface CitationInsertPluginProps {
  onRegisterInsertHandler?: (handler: (citation: CitationSuggestion) => void) => void;
  onCitationInserted?: (citation: CitationSuggestion) => void;
}

export function CitationInsertPlugin({ onRegisterInsertHandler, onCitationInserted }: CitationInsertPluginProps): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (!onRegisterInsertHandler) return;

    const insertCitation = (citation: CitationSuggestion) => {
      editor.update(() => {
        const selection = $getSelection();
        
        // Generate citation key
        const citationKey = generateCitationKey(citation);
        
        // Create citation node
        const citationNode = $createCitationNode(
          citationKey,
          citation.paperId,
          citation.title || 'Untitled',
          citation.authors || [],
          citation.year
        );
        
        if (selection && $isRangeSelection(selection)) {
          const anchorNode = selection.anchor.getNode();
          
          // If we're in a text node, find the end of the current sentence
          if ($isTextNode(anchorNode)) {
            const textContent = anchorNode.getTextContent();
            const anchorOffset = selection.anchor.offset;
            
            // Find the end of the current sentence
            const sentenceEndOffset = findSentenceEnd(textContent, anchorOffset);
            
            // If we need to move to the end of the sentence
            if (sentenceEndOffset > anchorOffset) {
              // Create a new selection at the end of the sentence
              const newSelection = $createRangeSelection();
              newSelection.anchor.set(anchorNode.getKey(), sentenceEndOffset, 'text');
              newSelection.focus.set(anchorNode.getKey(), sentenceEndOffset, 'text');
              $setSelection(newSelection);
            }
            
            // Insert citation with a space before it
            const spaceNode = $createTextNode(' ');
            $insertNodes([spaceNode, citationNode]);
          } else {
            // Not in a text node, just insert at current position
            $insertNodes([citationNode]);
          }
        } else {
          // No selection, append to the end
          const root = $getRoot();
          const lastChild = root.getLastChild();
          
          if (lastChild && $isTextNode(lastChild)) {
            // Add to the end of the last text node
            const spaceNode = $createTextNode(' ');
            lastChild.insertAfter(spaceNode);
            spaceNode.insertAfter(citationNode);
          } else {
            // Create a new paragraph
            const paragraph = $createParagraphNode();
            paragraph.append(citationNode);
            root.append(paragraph);
          }
        }
        
        // Focus back on editor
        editor.focus();
      });

      // Notify parent that a citation was inserted
      if (onCitationInserted) {
        onCitationInserted(citation);
      }
    };

    onRegisterInsertHandler(insertCitation);
  }, [editor, onRegisterInsertHandler, onCitationInserted]);

  return null;
}