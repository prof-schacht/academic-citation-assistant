import React, { useEffect, useState } from 'react';
import { Viewer, Worker } from '@react-pdf-viewer/core';
import { zoomPlugin } from '@react-pdf-viewer/zoom';
import { api } from '../../services/api';
import type { CitationSuggestion } from '../../types';
import PdfViewerErrorBoundary from './ErrorBoundary';

// Import styles
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/zoom/lib/styles/index.css';

interface PdfViewerProps {
  paper: CitationSuggestion | null;
  onClose: () => void;
  highlightChunk?: boolean;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ paper, onClose, highlightChunk = false }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Create zoom plugin instance
  const zoomPluginInstance = zoomPlugin();
  const { ZoomIn, ZoomOut, Zoom } = zoomPluginInstance;
  
  // Track current zoom level
  const [currentScale, setCurrentScale] = useState(1.0);
  
  useEffect(() => {
    // Subscribe to zoom changes
    const unsubscribe = zoomPluginInstance.store?.subscribe('scale', () => {
      const scale = zoomPluginInstance.store?.get('scale') || 1;
      setCurrentScale(scale);
    });
    
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [zoomPluginInstance]);

  useEffect(() => {
    if (!paper) {
      setLoading(false);
      return;
    }

    const loadPdf = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Check if paper has PDF
        const paperDetails = await api.get(`/papers/${paper.paperId}`);
        
        if (!paperDetails.data.has_pdf) {
          setError('No PDF available for this paper');
          setLoading(false);
          return;
        }

        // Set PDF URL
        const baseUrl = api.defaults.baseURL || '';
        const pdfUrl = `${baseUrl}/papers/${paper.paperId}/pdf`;
        setPdfUrl(pdfUrl);
      } catch (err) {
        console.error('Failed to load PDF:', err);
        setError('Failed to load PDF');
      } finally {
        setLoading(false);
      }
    };

    loadPdf();
  }, [paper]);

  if (!paper) {
    return null;
  }

  // Handle document load - for now just log the page info
  const handleDocumentLoad = (e: any) => {
    if (highlightChunk && paper.pageStart) {
      console.log(`PDF loaded. Chunk is on page ${paper.pageStart}`);
      // Note: Page navigation would require additional plugins that are causing issues
      // For now, we'll just display the page information in the header
    }
  };

  return (
    <PdfViewerErrorBoundary onError={(error) => {
      console.error('PDF Viewer crashed:', error);
      setError('Failed to render PDF');
      setPdfUrl(null);
    }}>
      <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {paper.title}
          </h3>
          <p className="text-sm text-gray-600">
            {paper.authors?.join(', ')} {paper.year && `(${paper.year})`}
          </p>
          {highlightChunk && paper.pageStart && (
            <p className="text-xs text-blue-600 mt-1">
              📍 Citation found on page {paper.pageStart}
              {paper.pageEnd && paper.pageEnd !== paper.pageStart && ` to ${paper.pageEnd}`}
              {paper.sectionTitle && ` in section: ${paper.sectionTitle}`}
            </p>
          )}
        </div>
        
        {/* Zoom Controls */}
        <div className="flex items-center space-x-2 mx-4">
          <ZoomOut>
            {(props: any) => (
              <button
                {...props}
                className="p-2 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom out"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                </svg>
              </button>
            )}
          </ZoomOut>
          
          <span className="text-sm font-medium text-gray-700 min-w-[60px] text-center">
            {Math.round(currentScale * 100)}%
          </span>
          
          <ZoomIn>
            {(props: any) => (
              <button
                {...props}
                className="p-2 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom in"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
                </svg>
              </button>
            )}
          </ZoomIn>
          
          <Zoom scale={1}>
            {(props: any) => (
              <button
                {...props}
                className="p-2 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100"
                title="Reset zoom"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
            )}
          </Zoom>
        </div>
        
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
          title="Close PDF viewer"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Page Info Message */}
      {highlightChunk && paper.pageStart && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2">
          <p className="text-sm text-blue-800">
            💡 The citation chunk is located on <strong>page {paper.pageStart}</strong>. 
            Please navigate to that page to find the highlighted content.
          </p>
        </div>
      )}

      {/* PDF Viewer */}
      <div className="flex-1 overflow-hidden">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-gray-600">Loading PDF...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-8">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-600 mb-2">{error}</p>
              {paper.url && (
                <a
                  href={paper.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 text-sm"
                >
                  View paper online →
                </a>
              )}
            </div>
          </div>
        )}

        {pdfUrl && !loading && !error && (
          <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
            <div className="h-full">
              <Viewer
                fileUrl={pdfUrl}
                plugins={[zoomPluginInstance]}
                defaultScale={1}
                onDocumentLoad={handleDocumentLoad}
              />
            </div>
          </Worker>
        )}
      </div>
    </div>
    </PdfViewerErrorBoundary>
  );
};

export default PdfViewer;