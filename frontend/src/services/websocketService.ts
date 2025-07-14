/**
 * WebSocket service for real-time citation suggestions
 */

import type { EditorState } from 'lexical';

export interface TextContext {
  currentSentence: string;
  previousSentence?: string;
  nextSentence?: string;
  paragraph: string;
  section?: string;
  cursorPosition: number;
}

export interface CitationSuggestion {
  paperId: string;
  title: string;
  authors: string[];
  year: number;
  abstract: string;
  confidence: number;
  citationStyle: 'inline' | 'footnote';
  displayText: string;
}

export interface WSMessage {
  type: 'suggest' | 'suggestions' | 'error' | 'ping' | 'pong';
  text?: string;
  context?: TextContext;
  results?: CitationSuggestion[];
  message?: string;
}

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
   */
  static extractContextFromEditor(editorState: EditorState, cursorOffset?: number): Partial<TextContext> {
    const textContent = editorState.read(() => {
      const root = editorState.getRoot();
      return root.getTextContent();
    });

    // Simple sentence extraction (can be improved)
    const sentences = textContent.match(/[^.!?]+[.!?]+/g) || [];
    
    // Find current sentence based on cursor position
    let currentSentenceIndex = 0;
    let charCount = 0;
    
    if (cursorOffset !== undefined) {
      for (let i = 0; i < sentences.length; i++) {
        if (charCount + sentences[i].length >= cursorOffset) {
          currentSentenceIndex = i;
          break;
        }
        charCount += sentences[i].length;
      }
    }

    return {
      currentSentence: sentences[currentSentenceIndex]?.trim() || '',
      previousSentence: sentences[currentSentenceIndex - 1]?.trim(),
      nextSentence: sentences[currentSentenceIndex + 1]?.trim(),
      paragraph: textContent, // Simplified for now
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