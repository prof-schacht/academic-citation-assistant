// Document types
export interface Document {
  id: string;
  title: string;
  content: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
}

// Paper types
export interface Paper {
  id: string;
  paperId: string;
  title: string;
  authors: string[];
  year: number;
  abstract: string;
  journal?: string;
  venue?: string;
  doi?: string;
  url?: string;
  citationCount?: number;
  referenceCount?: number;
  fieldsOfStudy?: string[];
  publicationTypes?: string[];
  publicationDate?: string;
  isOpenAccess?: boolean;
  has_pdf?: boolean;
}

// Extended citation suggestion type
export interface CitationSuggestion extends Omit<Paper, 'id'> {
  confidence: number;
  citationStyle: 'inline' | 'footnote';
  displayText: string;
  chunkText?: string;
  chunkIndex?: number;
  chunkId?: string;
  sectionTitle?: string;
}

// Document-Paper relationship
export interface DocumentPaper {
  id: string;
  documentId: string;
  paperId: string;
  addedAt: string;
  citationText?: string;
  citationStyle?: 'inline' | 'footnote';
  position?: number;
}

// Text context for suggestions
export interface TextContext {
  currentSentence: string;
  previousSentence?: string;
  nextSentence?: string;
  paragraph: string;
  section?: string;
  cursorPosition: number;
}

// WebSocket message types
export interface WSMessage {
  type: 'suggest' | 'suggestions' | 'error' | 'ping' | 'pong';
  text?: string;
  context?: TextContext;
  results?: CitationSuggestion[];
  message?: string;
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Search parameters
export interface SearchParams {
  query: string;
  filters?: {
    year?: { min?: number; max?: number };
    fieldsOfStudy?: string[];
    publicationTypes?: string[];
    isOpenAccess?: boolean;
  };
  sort?: 'relevance' | 'citations' | 'year';
  limit?: number;
  offset?: number;
}