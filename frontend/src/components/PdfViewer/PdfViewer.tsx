import React, { useEffect, useState, useRef } from 'react';
import { Viewer, Worker } from '@react-pdf-viewer/core';
import { zoomPlugin } from '@react-pdf-viewer/zoom';
import { pageNavigationPlugin } from '@react-pdf-viewer/page-navigation';
// Removed search/highlight plugins - will show search terms to user instead
import { api } from '../../services/api';
import type { CitationSuggestion } from '../../types';
import PdfViewerErrorBoundary from './ErrorBoundary';

// Import styles
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/zoom/lib/styles/index.css';
import '@react-pdf-viewer/page-navigation/lib/styles/index.css';

interface PdfViewerProps {
  paper: CitationSuggestion | null;
  onClose: () => void;
  highlightChunk?: boolean;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ paper, onClose, highlightChunk = false }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerms, setSearchTerms] = useState<string>('');
  
  // Log the paper prop when component mounts/updates
  useEffect(() => {
    console.log('[PdfViewer] Component received paper:', {
      title: paper?.title,
      paperId: paper?.paperId,
      pageStart: paper?.pageStart,
      pageEnd: paper?.pageEnd,
      pageBoundaries: paper?.pageBoundaries,
      highlightChunk: highlightChunk
    });
  }, [paper, highlightChunk]);
  
  // Create plugin instances outside of component to avoid re-creation
  const zoomPluginInstanceRef = useRef(zoomPlugin());
  const pageNavigationPluginInstanceRef = useRef(pageNavigationPlugin());
  
  // Get plugin components
  const { ZoomIn, ZoomOut, Zoom } = zoomPluginInstanceRef.current;
  const { CurrentPageInput, GoToFirstPage, GoToLastPage, GoToNextPage, GoToPreviousPage } = pageNavigationPluginInstanceRef.current;
  
  // Track current zoom level and page
  const [currentScale, setCurrentScale] = useState(1.0);
  const [currentPage, setCurrentPage] = useState(0);
  
  useEffect(() => {
    const zoomPlugin = zoomPluginInstanceRef.current;
    const pagePlugin = pageNavigationPluginInstanceRef.current;
    
    // Subscribe to zoom changes
    const unsubscribeZoom = zoomPlugin.store?.subscribe('scale', () => {
      const scale = zoomPlugin.store?.get('scale') || 1;
      setCurrentScale(scale);
    });
    
    // Subscribe to page changes
    const unsubscribePage = pagePlugin.store?.subscribe('currentPage', () => {
      const page = pagePlugin.store?.get('currentPage') || 0;
      setCurrentPage(page);
    });
    
    return () => {
      if (unsubscribeZoom) unsubscribeZoom();
      if (unsubscribePage) unsubscribePage();
    };
  }, []);

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

  // Handle document load and navigate to the correct page
  const handleDocumentLoad = (e: any) => {
    console.log('[PdfViewer] PDF document loaded:', {
      numPages: e.doc?.numPages,
      paper: paper,
      pageStart: paper?.pageStart,
      highlightChunk: highlightChunk
    });
    
    if (highlightChunk && paper.pageStart && e.doc) {
      console.log(`[PdfViewer] Attempting to navigate to page ${paper.pageStart} (0-based: ${paper.pageStart - 1})`);
      // PDF viewers use 0-based page indexing, but our page numbers are 1-based
      const targetPage = paper.pageStart - 1;
      
      // Use the page navigation plugin to jump to the page
      setTimeout(() => {
        const pagePlugin = pageNavigationPluginInstanceRef.current;
        console.log('[PdfViewer] Page navigation plugin:', {
          hasJumpToPage: !!pagePlugin.jumpToPage,
          targetPage: targetPage,
          totalPages: e.doc.numPages,
          isValidPage: targetPage >= 0 && targetPage < e.doc.numPages
        });
        
        if (pagePlugin.jumpToPage && targetPage >= 0 && targetPage < e.doc.numPages) {
          console.log(`[PdfViewer] Jumping to page ${targetPage + 1} (0-based: ${targetPage})`);
          pagePlugin.jumpToPage(targetPage);
          
          // Extract first few words to help user locate the chunk
          if (paper.chunkText) {
            // Light cleaning - only remove markdown formatting, keep numbers and punctuation
            const cleanText = paper.chunkText
              .replace(/^[#*_]+/g, '') // Remove markdown at start of line
              .replace(/\*\*/g, '') // Remove bold markdown
              .replace(/\n/g, ' ') // Replace newlines with spaces
              .replace(/\s+/g, ' ') // Normalize whitespace
              .trim();
            
            // Get first 5-6 words including numbers and punctuation
            const words = cleanText
              .split(' ')
              .slice(0, 6); // Get first 6 words
            
            const searchText = words.join(' ');
            
            if (searchText) {
              setSearchTerms(searchText);
              console.log(`[PdfViewer] Setting search terms for user: "${searchText}"`);
            }
          }
        } else {
          console.log('[PdfViewer] Cannot jump to page - invalid conditions');
        }
      }, 300); // Give more time for initialization
    } else {
      console.log('[PdfViewer] Not navigating to page:', {
        highlightChunk: highlightChunk,
        hasPageStart: !!paper?.pageStart,
        hasDoc: !!e.doc
      });
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
        </div>
        
        {/* Page Navigation Controls */}
        <div className="flex items-center space-x-2 mx-4">
          <GoToPreviousPage>
            {(props: any) => (
              <button
                {...props}
                className="p-1.5 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Previous page"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
          </GoToPreviousPage>
          
          <CurrentPageInput>
            {(props: any) => (
              <input
                {...props}
                className="w-12 px-2 py-1 text-sm text-center border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            )}
          </CurrentPageInput>
          
          <GoToNextPage>
            {(props: any) => (
              <button
                {...props}
                className="p-1.5 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Next page"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            )}
          </GoToNextPage>
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
            💡 The citation chunk is located on <strong>page {paper.pageStart}</strong>
            {paper.pageEnd && paper.pageEnd !== paper.pageStart && ` to ${paper.pageEnd}`}. 
          </p>
          {searchTerms && (
            <p className="text-sm text-blue-900 mt-1">
              🔍 Look for: <strong className="font-mono bg-yellow-100 px-1 py-0.5 rounded">{searchTerms}</strong>
            </p>
          )}
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
                plugins={[zoomPluginInstanceRef.current, pageNavigationPluginInstanceRef.current]}
                defaultScale={1}
                initialPage={highlightChunk && paper.pageStart ? paper.pageStart - 1 : 0}
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