/**
 * WebSocket service for real-time citation suggestions
 */

import type { EditorState } from 'lexical';
import type { TextContext, CitationSuggestion, WSMessage } from '../types';

export type { TextContext, CitationSuggestion, WSMessage };

export interface CitationConfig {
  useEnhanced?: boolean;
  useReranking?: boolean;
  searchStrategy?: 'vector' | 'bm25' | 'hybrid';
}

export class CitationWebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private messageQueue: WSMessage[] = [];
  private userId: string;
  private pingInterval: NodeJS.Timeout | null = null;
  private connectionTimeout: NodeJS.Timeout | null = null;
  private config: CitationConfig = {
    useEnhanced: true,
    useReranking: true,
    searchStrategy: 'hybrid'
  };
  private callbacks: {
    onSuggestions?: (citations: CitationSuggestion[]) => void;
    onError?: (error: string) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
  } = {};

  constructor(userId: string, config?: CitationConfig) {
    this.userId = userId;
    this.config = { ...this.config, ...config };
  }

  connect(): void {
    // Clear any existing connection timeout
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }

    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Already connected or connecting, skipping');
      return;
    }

    // Build WebSocket URL with configuration parameters
    const params = new URLSearchParams({
      user_id: this.userId,
      use_enhanced: String(this.config.useEnhanced ?? true),
      use_reranking: String(this.config.useReranking ?? true),
      search_strategy: this.config.searchStrategy ?? 'hybrid'
    });
    
    const endpoint = this.config.useEnhanced ? '/ws/citations/v2' : '/ws/citations';
    // Use the same host as the current page but with port 8000 for the backend
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    const wsUrl = `${wsProtocol}//${wsHost}${endpoint}?${params.toString()}`;
    console.log('[WebSocket] Connecting to:', wsUrl);
    
    try {
      this.socket = new WebSocket(wsUrl);
      
      // Set connection timeout (5 seconds)
      this.connectionTimeout = setTimeout(() => {
        if (this.socket?.readyState !== WebSocket.OPEN) {
          console.error('[WebSocket] Connection timeout after 5 seconds');
          this.socket?.close();
          this.handleReconnection();
        }
      }, 5000);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected, readyState:', this.socket?.readyState);
        // Verify socket is actually open
        if (this.socket?.readyState !== WebSocket.OPEN) {
          console.error('[WebSocket] onopen fired but socket not in OPEN state!');
          return;
        }
        // Clear the connection timeout
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout);
          this.connectionTimeout = null;
        }
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Send queued messages (with error handling)
        const messagesToSend = [...this.messageQueue];
        this.messageQueue = [];
        for (const message of messagesToSend) {
          this.sendMessage(message);
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
        console.error('WebSocket readyState:', this.socket?.readyState);
        console.error('WebSocket URL was:', this.socket?.url);
        this.callbacks.onError?.('WebSocket connection error');
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected, code:', event.code, 'reason:', event.reason);
        // Clear the connection timeout if it exists
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout);
          this.connectionTimeout = null;
        }
        this.stopPingInterval();
        
        // Clear message queue on abnormal closure
        if (event.code !== 1000) { // 1000 = normal closure
          console.log('[WebSocket] Abnormal closure, clearing message queue');
          this.messageQueue = [];
        }
        
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
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    if (this.socket) {
      if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
        this.socket.close();
      }
      this.socket = null;
    }
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
    return this.socket?.readyState === WebSocket.OPEN;
  }

  /**
   * Update citation configuration and reconnect with new settings
   */
  updateConfig(config: Partial<CitationConfig>): void {
    const configChanged = 
      config.useEnhanced !== this.config.useEnhanced ||
      config.useReranking !== this.config.useReranking ||
      config.searchStrategy !== this.config.searchStrategy;
    
    this.config = { ...this.config, ...config };
    
    // Reconnect if configuration changed and we're connected
    if (configChanged) {
      if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
        console.log('[WebSocket] Configuration changed, reconnecting...');
        this.disconnect();
        // Delay reconnection to avoid race conditions
        setTimeout(() => {
          this.connect();
        }, 100);
      } else if (!this.socket) {
        // If no socket exists, just connect with new config
        this.connect();
      }
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): CitationConfig {
    return { ...this.config };
  }

  /**
   * Send preferences update message to server (for v2 endpoint)
   */
  updatePreferences(preferences: Partial<CitationConfig>): void {
    if (this.config.useEnhanced) {
      this.sendMessage({
        type: 'update_preferences',
        preferences: preferences as any
      });
    }
  }

  private handleMessage(message: WSMessage): void {
    switch (message.type) {
      case 'suggestions':
        if (message.results) {
          console.log('[WebSocket] Received suggestions:', {
            count: message.results.length,
            firstSuggestion: message.results[0] ? {
              title: message.results[0].title,
              pageStart: message.results[0].pageStart,
              pageEnd: message.results[0].pageEnd,
              pageBoundaries: message.results[0].pageBoundaries
            } : null
          });
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
      console.log('[WebSocket] Sending message:', message);
      try {
        this.socket.send(JSON.stringify(message));
      } catch (error) {
        console.error('[WebSocket] Error sending message:', error);
        this.callbacks.onError?.('Failed to send message');
      }
    } else if (this.socket?.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Still connecting, queueing message. ReadyState:', this.socket?.readyState);
      // Queue the message for later with a limit to prevent memory issues
      if (this.messageQueue.length < 10) {
        this.messageQueue.push(message);
      } else {
        console.warn('[WebSocket] Message queue full, dropping oldest message');
        this.messageQueue.shift(); // Remove oldest
        this.messageQueue.push(message);
      }
    } else {
      console.warn('[WebSocket] Socket is closed or closing, not queueing message. ReadyState:', this.socket?.readyState);
      // Don't queue messages if socket is closed or closing
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

export function getCitationWebSocketClient(userId: string, config?: CitationConfig): CitationWebSocketClient {
  if (!instance || instance['userId'] !== userId) {
    instance?.disconnect();
    instance = new CitationWebSocketClient(userId, config);
  } else if (config) {
    // Update config if provided
    instance.updateConfig(config);
  }
  return instance;
}

export function disconnectCitationWebSocket(): void {
  instance?.disconnect();
  instance = null;
}