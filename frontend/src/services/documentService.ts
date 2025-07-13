import { api } from './api';

export interface DocumentType {
  id: string;
  title: string;
  description?: string;
  content?: any;
  is_public: boolean;
  owner_id: string;
  plain_text?: string;
  word_count: number;
  citation_count: number;
  share_token?: string;
  created_at: string;
  updated_at: string;
  last_accessed_at: string;
}

export interface CreateDocumentDto {
  title: string;
  description?: string;
  content?: any;
  is_public?: boolean;
}

export interface UpdateDocumentDto {
  title?: string;
  description?: string;
  content?: any;
  is_public?: boolean;
}

export interface DocumentListResponse {
  documents: DocumentType[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}

export const documentService = {
  async create(data: CreateDocumentDto): Promise<DocumentType> {
    const response = await api.post<DocumentType>('/api/documents/', data);
    return response.data;
  },

  async getById(id: string): Promise<DocumentType> {
    const response = await api.get<DocumentType>(`/api/documents/${id}`);
    return response.data;
  },

  async list(params?: {
    page?: number;
    limit?: number;
    search?: string;
    public_only?: boolean;
  }): Promise<DocumentListResponse> {
    const response = await api.get<DocumentListResponse>('/api/documents/', { params });
    return response.data;
  },

  async update(id: string, data: UpdateDocumentDto): Promise<DocumentType> {
    const response = await api.put<DocumentType>(`/api/documents/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/documents/${id}`);
  },
};