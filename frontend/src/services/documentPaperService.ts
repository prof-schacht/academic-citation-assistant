import { api } from './api';

export interface DocumentPaper {
  id: string;
  document_id: string;
  paper_id: string;
  position: number;
  notes?: string;
  added_at: string;
  added_by?: string;
  paper: {
    id: string;
    title: string;
    authors?: string[];
    year?: number;
    journal?: string;
    doi?: string;
    arxiv_id?: string;
  };
}

export interface AssignPaperRequest {
  paper_id: string;
  notes?: string;
  position?: number;
}

export interface BulkAssignRequest {
  paper_ids: string[];
}

export interface ReorderRequest {
  paper_ids: string[];
}

export interface UpdateAssignmentRequest {
  notes?: string;
  position?: number;
}

class DocumentPaperService {
  async assignPaper(documentId: string, data: AssignPaperRequest): Promise<DocumentPaper> {
    const response = await api.post(`/documents/${documentId}/papers`, data);
    return response.data;
  }

  async bulkAssignPapers(documentId: string, paperIds: string[]): Promise<DocumentPaper[]> {
    const response = await api.post(`/documents/${documentId}/papers/bulk`, {
      paper_ids: paperIds
    });
    return response.data;
  }

  async getDocumentPapers(documentId: string, skip = 0, limit = 100): Promise<DocumentPaper[]> {
    const response = await api.get(`/documents/${documentId}/papers`, {
      params: { skip, limit }
    });
    return response.data;
  }

  async updateAssignment(
    documentId: string, 
    paperId: string, 
    data: UpdateAssignmentRequest
  ): Promise<DocumentPaper> {
    const response = await api.patch(`/documents/${documentId}/papers/${paperId}`, data);
    return response.data;
  }

  async reorderPapers(documentId: string, paperIds: string[]): Promise<void> {
    await api.post(`/documents/${documentId}/papers/reorder`, {
      paper_ids: paperIds
    });
  }

  async removePaper(documentId: string, paperId: string): Promise<void> {
    await api.delete(`/documents/${documentId}/papers/${paperId}`);
  }

  async exportBibTeX(documentId: string): Promise<string> {
    const response = await api.get(`/documents/${documentId}/export/bibtex`, {
      responseType: 'text'
    });
    return response.data;
  }

  async exportLaTeX(documentId: string, template = 'article'): Promise<string> {
    const response = await api.get(`/documents/${documentId}/export/latex`, {
      params: { template },
      responseType: 'text'
    });
    return response.data;
  }

  downloadFile(content: string, filename: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

export const documentPaperService = new DocumentPaperService();