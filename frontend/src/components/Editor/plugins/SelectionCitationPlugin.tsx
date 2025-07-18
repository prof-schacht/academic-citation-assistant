/**
 * Plugin to handle text selection and manual citation searches
 */

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection, SELECTION_CHANGE_COMMAND, COMMAND_PRIORITY_LOW } from 'lexical';
import type { CitationWebSocketClient } from '../../../services/websocketService';

interface SelectionCitationPluginProps {
  wsClient: CitationWebSocketClient | null;
  onSelectionChange?: (selectedText: string) => void;
}

export function SelectionCitationPlugin({ wsClient, onSelectionChange }: SelectionCitationPluginProps): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        const selection = $getSelection();
        
        if ($isRangeSelection(selection) && !selection.isCollapsed()) {
          // Get selected text
          const selectedText = selection.getTextContent();
          
          if (selectedText.trim().length > 10) {
            console.log('[SelectionPlugin] Selected text:', selectedText);
            
            // Notify parent component
            onSelectionChange?.(selectedText);
            
            // Request citations for selected text
            if (wsClient?.getConnectionStatus()) {
              const context = {
                currentSentence: selectedText,
                previousSentence: '',
                nextSentence: '',
                paragraph: selectedText,
                cursorPosition: 0
              };
              
              wsClient.requestSuggestions(selectedText, context);
            }
          }
        }
        
        return false;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor, wsClient, onSelectionChange]);

  return null;
}