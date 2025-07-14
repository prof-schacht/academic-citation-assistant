/**
 * Lexical plugin for real-time citation suggestions
 */

import { useEffect, useRef, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection } from 'lexical';
import type { EditorState } from 'lexical';
import { getCitationWebSocketClient, CitationWebSocketClient } from '../../../services/websocketService';
import type { CitationSuggestion } from '../../../services/websocketService';
import { debounce } from '../../../utils/debounce';

interface CitationSuggestionPluginProps {
  userId: string;
  onSuggestionsUpdate: (suggestions: CitationSuggestion[]) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export function CitationSuggestionPlugin({
  userId,
  onSuggestionsUpdate,
  onConnectionChange
}: CitationSuggestionPluginProps): null {
  const [editor] = useLexicalComposerContext();
  const wsClientRef = useRef<CitationWebSocketClient | null>(null);
  const lastTextRef = useRef<string>('');
  const [isConnected, setIsConnected] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    console.log('[CitationPlugin] Initializing WebSocket for user:', userId);
    const wsClient = getCitationWebSocketClient(userId);
    wsClientRef.current = wsClient;

    // Set up callbacks
    wsClient.onSuggestions((suggestions) => {
      console.log('[CitationPlugin] Received suggestions:', suggestions.length);
      onSuggestionsUpdate(suggestions);
    });

    wsClient.onError((error) => {
      console.error('[CitationPlugin] WebSocket error:', error);
    });

    wsClient.onConnect(() => {
      console.log('[CitationPlugin] WebSocket connected');
      setIsConnected(true);
      onConnectionChange?.(true);
    });

    wsClient.onDisconnect(() => {
      console.log('[CitationPlugin] WebSocket disconnected');
      setIsConnected(false);
      onConnectionChange?.(false);
    });

    // Check if already connected (singleton might already be connected)
    if (wsClient.getConnectionStatus()) {
      console.log('[CitationPlugin] WebSocket already connected');
      setIsConnected(true);
      onConnectionChange?.(true);
    } else {
      // Connect to WebSocket
      wsClient.connect();
    }

    return () => {
      // Don't disconnect on unmount as other components might use it
    };
  }, [userId, onSuggestionsUpdate, onConnectionChange]);

  // Debounced function to request suggestions
  const requestSuggestions = useRef(
    debounce((editorState: EditorState) => {
      if (!wsClientRef.current) {
        console.log('[CitationPlugin] No WebSocket client reference');
        return;
      }
      
      // Always check the actual connection status, not the React state
      const currentConnectionStatus = wsClientRef.current.getConnectionStatus();
      
      if (!currentConnectionStatus) {
        console.log('[CitationPlugin] Not connected, skipping suggestion request');
        return;
      }

      editorState.read(() => {
        const selection = $getSelection();
        
        if (!$isRangeSelection(selection)) {
          return;
        }

        // Get cursor position
        const anchor = selection.anchor;
        const cursorOffset = anchor.offset;
        
        // Extract context from editor
        const context = CitationWebSocketClient.extractContextFromEditor(editorState, cursorOffset);
        
        // Get current text
        const currentText = context.currentSentence || '';
        
        console.log('[CitationPlugin] Extracted text:', currentText, 'Length:', currentText.trim().length);
        
        // Skip if text hasn't changed significantly
        if (currentText === lastTextRef.current || currentText.trim().length < 10) {
          console.log('[CitationPlugin] Skipping - same text or too short');
          return;
        }

        lastTextRef.current = currentText;
        
        console.log('[CitationPlugin] Requesting suggestions for:', currentText);
        
        // Request suggestions
        wsClientRef.current.requestSuggestions(currentText, context);
      });
    }, 500) // 500ms debounce
  ).current;

  // Listen to editor updates
  useEffect(() => {
    const removeUpdateListener = editor.registerUpdateListener(({ editorState }) => {
      requestSuggestions(editorState);
    });

    return removeUpdateListener;
  }, [editor, requestSuggestions]);

  // No UI to render
  return null;
}