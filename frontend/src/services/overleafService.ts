/**
 * Service for exporting documents to Overleaf
 */

import { api } from './api';

export interface OverleafExportOptions {
  documentId: string;
  documentTitle: string;
  useReferencesFilename?: boolean; // Use 'references.bib' instead of document-specific name
}

export class OverleafService {
  /**
   * Export document and bibliography to Overleaf
   * Creates a new Overleaf project with the LaTeX document and BibTeX bibliography
   */
  static async exportToOverleaf(options: OverleafExportOptions): Promise<void> {
    const { documentId, documentTitle, useReferencesFilename = true } = options;
    
    try {
      // Fetch LaTeX content with proper bibliography reference
      const latexResponse = await api.get(`/documents/${documentId}/export/latex`, {
        params: {
          template: 'article',
          bib_filename: useReferencesFilename ? 'references' : undefined
        }
      });
      const latexContent = latexResponse.data;
      
      // Fetch BibTeX content
      const bibtexResponse = await api.get(`/documents/${documentId}/export/bibtex`);
      const bibtexContent = bibtexResponse.data;
      
      // Create form for Overleaf submission
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = 'https://www.overleaf.com/docs';
      form.target = '_blank';
      form.style.display = 'none';
      
      // Main LaTeX file
      const mainFile = document.createElement('textarea');
      mainFile.name = 'snip[]';
      mainFile.value = latexContent;
      form.appendChild(mainFile);
      
      const mainFileName = document.createElement('input');
      mainFileName.type = 'hidden';
      mainFileName.name = 'snip_name[]';
      mainFileName.value = 'main.tex';
      form.appendChild(mainFileName);
      
      // BibTeX file (only if bibliography exists)
      if (bibtexContent && !bibtexContent.includes('No papers assigned')) {
        const bibFile = document.createElement('textarea');
        bibFile.name = 'snip[]';
        bibFile.value = bibtexContent;
        form.appendChild(bibFile);
        
        const bibFileName = document.createElement('input');
        bibFileName.type = 'hidden';
        bibFileName.name = 'snip_name[]';
        bibFileName.value = 'references.bib';
        form.appendChild(bibFileName);
      }
      
      // Set compiler to pdflatex
      const engineInput = document.createElement('input');
      engineInput.type = 'hidden';
      engineInput.name = 'engine';
      engineInput.value = 'pdflatex';
      form.appendChild(engineInput);
      
      // Submit form
      document.body.appendChild(form);
      form.submit();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(form);
      }, 100);
      
    } catch (error) {
      console.error('Failed to export to Overleaf:', error);
      throw new Error('Failed to export to Overleaf. Please try again.');
    }
  }
  
  /**
   * Check if a document has any papers in its bibliography
   */
  static async hasBibliography(documentId: string): Promise<boolean> {
    try {
      const response = await api.get(`/documents/${documentId}/papers`, {
        params: { limit: 1 }
      });
      return response.data && response.data.length > 0;
    } catch (error) {
      console.error('Failed to check bibliography:', error);
      return false;
    }
  }
}

export default OverleafService;