/**
 * WebSocket service for real-time citation suggestions
 */

import type { EditorState } from 'lexical';
import type { TextContext, CitationSuggestion, WSMessage } from '../types';

export type { TextContext, CitationSuggestion, WSMessage };

export class CitationWebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private messageQueue: WSMessage[] = [];
  private userId: string;
  private isConnected = false;
  private pingInterval: NodeJS.Timeout | null = null;
  private callbacks: {
    onSuggestions?: (citations: CitationSuggestion[]) => void;
    onError?: (error: string) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
  } = {};

  constructor(userId: string) {
    this.userId = userId;
  }

  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws/citations?user_id=${this.userId}`;
    console.log('[WebSocket] Connecting to:', wsUrl);
    
    try {
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Send queued messages
        while (this.messageQueue.length > 0) {
          const message = this.messageQueue.shift();
          if (message) {
            this.sendMessage(message);
          }
        }
        
        // Start ping interval
        this.startPingInterval();
        
        // Notify callback
        this.callbacks.onConnect?.();
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.callbacks.onError?.('WebSocket connection error');
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.stopPingInterval();
        this.callbacks.onDisconnect?.();
        
        // Attempt to reconnect
        this.handleReconnection();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.callbacks.onError?.('Failed to establish WebSocket connection');
    }
  }

  disconnect(): void {
    this.stopPingInterval();
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.isConnected = false;
    this.messageQueue = [];
  }

  requestSuggestions(text: string, context: Partial<TextContext>): void {
    // Skip very short text
    if (text.trim().length < 10) {
      return;
    }

    const message: WSMessage = {
      type: 'suggest',
      text,
      context: context as TextContext
    };

    this.sendMessage(message);
  }

  onSuggestions(callback: (citations: CitationSuggestion[]) => void): void {
    this.callbacks.onSuggestions = callback;
  }

  onError(callback: (error: string) => void): void {
    this.callbacks.onError = callback;
  }

  onConnect(callback: () => void): void {
    this.callbacks.onConnect = callback;
  }

  onDisconnect(callback: () => void): void {
    this.callbacks.onDisconnect = callback;
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  private handleMessage(message: WSMessage): void {
    switch (message.type) {
      case 'suggestions':
        if (message.results) {
          this.callbacks.onSuggestions?.(message.results);
        }
        break;
      case 'error':
        if (message.message) {
          this.callbacks.onError?.(message.message);
        }
        break;
      case 'pong':
        // Server is alive
        break;
    }
  }

  private sendMessage(message: WSMessage): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      // Queue the message for later
      this.messageQueue.push(message);
    }
  }

  private handleReconnection(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.callbacks.onError?.('Unable to reconnect to server');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Max 30 seconds
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'ping' });
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Extract context from Lexical editor state
   * Note: This should be called from within an editor.read() callback
   */
  static extractContextFromEditor(editorState: EditorState, cursorOffset?: number): Partial<TextContext> {
    // Get the root node and extract text content
    const root = editorState._nodeMap.get('root');
    const textContent = root?.getTextContent() || '';

    // Handle both complete and incomplete sentences
    let currentSentence = '';
    let previousSentence = '';
    let nextSentence = '';
    
    // Always try to extract sentences, regardless of text length
    // Updated pattern to better handle sentence boundaries including questions
    // This pattern captures text ending with punctuation OR line breaks
    const sentencePattern = /[^.!?\n]+[.!?]+\s*|[^.!?\n]+(?=\n|$)/g;
    let sentences: string[] = [];
    const matches = textContent.match(sentencePattern);
    if (matches) {
      sentences = matches;
    }
    
    // If no sentences found with punctuation, split by newlines
    if (sentences.length === 0 && textContent.trim().length > 0) {
      const lines = textContent.split('\n').filter(line => line.trim());
      if (lines.length > 0) {
        sentences = lines;
      } else {
        sentences = [textContent];
      }
    }
    
    // Find current sentence based on cursor position
    if (cursorOffset !== undefined && sentences.length > 0) {
      let charCount = 0;
      let currentIndex = -1;
      
      for (let i = 0; i < sentences.length; i++) {
        const sentenceLength = sentences[i].length;
        if (charCount <= cursorOffset && cursorOffset <= charCount + sentenceLength) {
          currentIndex = i;
          currentSentence = sentences[i].trim();
          
          // Get previous and next sentences
          if (i > 0) {
            previousSentence = sentences[i - 1].trim();
          }
          if (i < sentences.length - 1) {
            nextSentence = sentences[i + 1].trim();
          }
          break;
        }
        charCount += sentenceLength;
      }
      
      // If cursor is at the very end, use the last sentence
      if (currentIndex === -1 && sentences.length > 0) {
        currentIndex = sentences.length - 1;
        currentSentence = sentences[currentIndex].trim();
        if (currentIndex > 0) {
          previousSentence = sentences[currentIndex - 1].trim();
        }
      }
    } else {
      // Use the last sentence if no cursor position
      if (sentences.length > 0) {
        currentSentence = sentences[sentences.length - 1].trim();
        if (sentences.length > 1) {
          previousSentence = sentences[sentences.length - 2].trim();
        }
      }
    }
    
    // Clean up the sentence - remove trailing punctuation for matching
    const cleanedSentence = currentSentence.replace(/[.!?]+\s*$/, '').trim();

    return {
      currentSentence: cleanedSentence || currentSentence,  // Use cleaned version for better matching
      previousSentence: previousSentence || undefined,
      nextSentence: nextSentence || undefined,
      paragraph: currentSentence,  // Use just the current sentence as paragraph for focused search
      cursorPosition: cursorOffset || textContent.length
    };
  }
}

// Singleton instance management
let instance: CitationWebSocketClient | null = null;

export function getCitationWebSocketClient(userId: string): CitationWebSocketClient {
  if (!instance || instance['userId'] !== userId) {
    instance?.disconnect();
    instance = new CitationWebSocketClient(userId);
  }
  return instance;
}

export function disconnectCitationWebSocket(): void {
  instance?.disconnect();
  instance = null;
}