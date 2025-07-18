import { api } from './api';

export interface CleanDocumentsRequest {
  confirmation: string;
}

export interface CleanDocumentsResponse {
  documents_deleted: number;
  citations_deleted: number;
  document_papers_deleted: number;
}

export const adminService = {
  async cleanAllDocuments(confirmation: string): Promise<CleanDocumentsResponse> {
    const response = await api.post<CleanDocumentsResponse>('/admin/clean-documents', {
      confirmation,
    });
    return response.data;
  },
};