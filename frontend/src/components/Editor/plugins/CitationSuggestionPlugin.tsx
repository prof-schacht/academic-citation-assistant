/**
 * Lexical plugin for real-time citation suggestions
 */

import { useEffect, useRef, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getSelection, $isRangeSelection, $getRoot } from 'lexical';
import type { EditorState } from 'lexical';
import { getCitationWebSocketClient, CitationWebSocketClient } from '../../../services/websocketService';
import type { CitationSuggestion, CitationConfig } from '../../../services/websocketService';
import { debounce } from '../../../utils/debounce';

interface CitationSuggestionPluginProps {
  userId: string;
  citationConfig?: CitationConfig;
  onSuggestionsUpdate: (suggestions: CitationSuggestion[]) => void;
  onConnectionChange?: (connected: boolean) => void;
  onWsClientReady?: (client: CitationWebSocketClient) => void;
}

export function CitationSuggestionPlugin({
  userId,
  citationConfig,
  onSuggestionsUpdate,
  onConnectionChange,
  onWsClientReady
}: CitationSuggestionPluginProps): null {
  const [editor] = useLexicalComposerContext();
  const wsClientRef = useRef<CitationWebSocketClient | null>(null);
  const lastTextRef = useRef<string>('');
  const lastPositionRef = useRef<number>(-1);
  const lastRequestTimeRef = useRef<number>(0);
  const [, setIsConnected] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    console.log('[CitationPlugin] Initializing WebSocket for user:', userId, 'config:', citationConfig);
    const wsClient = getCitationWebSocketClient(userId, citationConfig);
    wsClientRef.current = wsClient;
    
    // Notify parent component that client is ready
    onWsClientReady?.(wsClient);

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
  }, [userId, citationConfig, onSuggestionsUpdate, onConnectionChange, onWsClientReady]);

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

        // Get cursor position - calculate absolute position in document
        const anchor = selection.anchor;
        const anchorNode = anchor.getNode();
        
        // Get the full text content
        const root = $getRoot();
        const fullText = root.getTextContent();
        
        // Calculate absolute cursor position by finding text before anchor
        let absoluteOffset = 0;
        const allTextNodes: any[] = [];
        
        // Collect all text nodes
        function collectTextNodes(node: any) {
          if (node.getType() === 'text') {
            allTextNodes.push(node);
          } else if (node.getChildren) {
            const children = node.getChildren();
            for (const child of children) {
              collectTextNodes(child);
            }
          }
        }
        
        collectTextNodes(root);
        
        // Find position
        for (const textNode of allTextNodes) {
          if (textNode === anchorNode) {
            absoluteOffset += anchor.offset;
            break;
          } else {
            absoluteOffset += textNode.getTextContent().length;
          }
        }
        
        console.log('[CitationPlugin] Cursor at absolute position:', absoluteOffset, 'in text of length:', fullText.length);
        
        // Extract context from editor with correct cursor position
        const context = CitationWebSocketClient.extractContextFromEditor(editorState, absoluteOffset);
        
        // Get current text
        const currentText = context.currentSentence || '';
        
        console.log('[CitationPlugin] Context extraction:', {
          currentSentence: currentText,
          previousSentence: context.previousSentence,
          nextSentence: context.nextSentence,
          cursorPosition: context.cursorPosition,
          textLength: currentText.trim().length
        });
        
        // Skip if text is too short
        if (currentText.trim().length < 10) {
          console.log('[CitationPlugin] Skipping - text too short');
          return;
        }
        
        // Skip if same text and same position (no actual change)
        if (currentText === lastTextRef.current && absoluteOffset === lastPositionRef.current) {
          console.log('[CitationPlugin] Skipping - same text and position');
          return;
        }
        
        // Rate limit requests to prevent flooding
        const now = Date.now();
        if (now - lastRequestTimeRef.current < 1000) { // Max 1 request per second
          console.log('[CitationPlugin] Skipping - rate limit');
          return;
        }

        lastTextRef.current = currentText;
        lastPositionRef.current = absoluteOffset;
        lastRequestTimeRef.current = now;
        
        console.log('[CitationPlugin] Requesting suggestions for:', currentText);
        
        // Request suggestions
        if (wsClientRef.current) {
          console.log('[CitationPlugin] Calling requestSuggestions with WebSocket client');
          wsClientRef.current.requestSuggestions(currentText, context);
        } else {
          console.log('[CitationPlugin] No WebSocket client available!');
        }
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