import { api } from './api';

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  year: number;
  journal?: string;
  doi?: string;
  abstract?: string;
  citationCount?: number;
  chunkCount?: number;
  status: 'processing' | 'indexed' | 'error';
  createdAt: string;
  updatedAt: string;
}

export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

class PaperService {
  private uploadProgressCallbacks: ((progress: UploadProgress) => void)[] = [];

  async getUserPapers(): Promise<Paper[]> {
    try {
      const response = await api.get('/papers');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch papers:', error);
      return [];
    }
  }

  async uploadPaper(file: File): Promise<Paper> {
    const formData = new FormData();
    formData.append('file', file);

    // Create a unique file ID for tracking
    const fileId = `${file.name}-${Date.now()}`;

    try {
      // Notify progress: uploading
      this.notifyProgress({
        fileId,
        fileName: file.name,
        progress: 0,
        status: 'uploading'
      });

      // Upload file using api instance
      // Note: Don't set Content-Type header, axios will set it automatically with boundary
      const response = await api.post('/papers/upload', formData);

      // Notify progress: processing
      this.notifyProgress({
        fileId,
        fileName: file.name,
        progress: 50,
        status: 'processing'
      });

      const paper = response.data;

      // Notify progress: completed
      this.notifyProgress({
        fileId,
        fileName: file.name,
        progress: 100,
        status: 'completed'
      });

      return paper;
    } catch (error) {
      // Notify progress: error
      this.notifyProgress({
        fileId,
        fileName: file.name,
        progress: 0,
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed'
      });
      throw error;
    }
  }

  async getPaper(paperId: string): Promise<Paper> {
    const response = await api.get(`/papers/${paperId}`);
    return response.data;
  }

  async updatePaper(paperId: string, updates: Partial<Paper>): Promise<Paper> {
    const response = await api.patch(`/papers/${paperId}`, updates);
    return response.data;
  }

  async deletePaper(paperId: string): Promise<void> {
    await api.delete(`/papers/${paperId}`);
  }

  async searchPapers(query: string): Promise<Paper[]> {
    const response = await api.get('/papers/search', {
      params: { q: query }
    });
    return response.data;
  }

  // Progress tracking
  onUploadProgress(callback: (progress: UploadProgress) => void): () => void {
    this.uploadProgressCallbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      this.uploadProgressCallbacks = this.uploadProgressCallbacks.filter(cb => cb !== callback);
    };
  }

  private notifyProgress(progress: UploadProgress): void {
    this.uploadProgressCallbacks.forEach(callback => {
      try {
        callback(progress);
      } catch (error) {
        console.error('Error in progress callback:', error);
      }
    });
  }
}

export const paperService = new PaperService();