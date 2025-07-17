import React, { useState } from 'react';
import type { CitationSuggestion } from '../../types';


interface CitationPanelProps {
  documentId: string;
  selectedText?: string;
  suggestions?: CitationSuggestion[];
  isConnected?: boolean;
  onInsertCitation?: (citation: CitationSuggestion) => void;
  onAddToLibrary?: (citation: CitationSuggestion) => void;
  bibliographyPaperIds?: Set<string>;
  citedPaperIds?: Set<string>;
}

const CitationPanel: React.FC<CitationPanelProps> = ({ 
  selectedText, 
  suggestions = [], 
  isConnected = false, 
  onInsertCitation,
  onAddToLibrary,
  bibliographyPaperIds = new Set(),
  citedPaperIds = new Set()
}) => {
  const [activeTab, setActiveTab] = useState<'suggestions' | 'library'>('suggestions');


  const handleInsertCitation = (citation: CitationSuggestion) => {
    console.log('Inserting citation:', citation);
    if (onInsertCitation) {
      onInsertCitation(citation);
    }
  };

  const handleAddToLibrary = (citation: CitationSuggestion) => {
    console.log('Adding to library:', citation);
    if (onAddToLibrary) {
      onAddToLibrary(citation);
    }
  };

  return (
    <div className="citation-panel h-full flex flex-col">
      {/* Header with tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex items-center justify-between p-4">
          <h2 className="text-lg font-semibold text-gray-900">Citations</h2>
          <div className="flex items-center space-x-3">
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-xs text-gray-500">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button
              className="text-sm text-blue-600 hover:text-blue-700"
              onClick={() => console.log('Search papers')}
            >
              Search papers
            </button>
          </div>
        </div>
        
        <div className="flex border-t border-gray-200">
          <button
            className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'suggestions'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('suggestions')}
          >
            Suggestions
          </button>
          <button
            className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'library'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('library')}
          >
            My Library
          </button>
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'suggestions' ? (
          <>
            {selectedText && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  Finding citations for: <em>"{selectedText}"</em>
                </p>
              </div>
            )}

            {false ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-white rounded-lg shadow-sm p-4">
                    <div className="animate-pulse">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-full"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : suggestions.length > 0 ? (
              <div className="space-y-3">
                {suggestions.map((citation, index) => {
                  const isInBibliography = bibliographyPaperIds.has(citation.paperId);
                  const isCited = citedPaperIds.has(citation.paperId);
                  
                  if (index === 0) {
                    console.log('[CitationPanel] First citation status:', {
                      paperId: citation.paperId,
                      isInBibliography,
                      isCited,
                      bibliographyPaperIds: Array.from(bibliographyPaperIds),
                      citedPaperIds: Array.from(citedPaperIds)
                    });
                  }
                  
                  return (
                    <div
                      key={citation.chunkId || `${citation.paperId}-${index}`}
                      className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-start gap-2">
                            <h4 className="font-medium text-gray-900 text-sm mb-1 flex-1">
                              {citation.title}
                            </h4>
                            <div className="flex gap-1">
                              {isInBibliography && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800" title="In bibliography">
                                  <svg className="w-3 h-3 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                                    <path fillRule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 000 2H6a2 2 0 00-2 2v6a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-1a1 1 0 100-2h1a4 4 0 014 4v6a4 4 0 01-4 4H6a4 4 0 01-4-4V7a4 4 0 014-4z" clipRule="evenodd" />
                                  </svg>
                                  In Library
                                </span>
                              )}
                              {isCited && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800" title="Cited in document">
                                  <svg className="w-3 h-3 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                  </svg>
                                  Cited
                                </span>
                              )}
                            </div>
                          </div>
                        <p className="text-xs text-gray-600 mb-2">
                          {citation.authors && citation.authors.length > 0 
                            ? citation.authors.join(', ') 
                            : 'Unknown authors'} • {citation.year || 'No year'}
                          {citation.journal && ` • ${citation.journal}`}
                        </p>
                        
                        {/* Chunk preview */}
                        {citation.chunkText && (
                          <div className="mt-2 mb-3 p-2 bg-gray-50 rounded text-xs">
                            {citation.sectionTitle && (
                              <p className="font-semibold text-gray-700 mb-1">
                                Section: {citation.sectionTitle}
                              </p>
                            )}
                            <p className="text-gray-600 line-clamp-3">
                              ...{citation.chunkText}
                            </p>
                          </div>
                        )}
                        
                        <div className="flex items-center space-x-4">
                          <span className="text-xs text-gray-500">
                            Confidence: {Math.round(citation.confidence * 100)}%
                          </span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            citation.confidence > 0.85 ? 'bg-green-100 text-green-800' : 
                            citation.confidence > 0.70 ? 'bg-yellow-100 text-yellow-800' : 
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {citation.confidence > 0.85 ? 'High' : 
                             citation.confidence > 0.70 ? 'Medium' : 'Low'}
                          </span>
                          {citation.chunkIndex !== undefined && (
                            <span className="text-xs text-gray-500">
                              Part {citation.chunkIndex + 1}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-3 flex items-center space-x-2">
                      <button
                        onClick={() => handleInsertCitation(citation)}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                      >
                        Insert
                      </button>
                      <button
                        onClick={() => handleAddToLibrary(citation)}
                        disabled={isInBibliography}
                        className={`px-3 py-1 text-xs rounded transition ${
                          isInBibliography 
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {isInBibliography ? 'In Library' : 'Add to Library'}
                      </button>
                      <button
                        className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800 transition"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center text-gray-500 mt-8">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm">Start typing to see citation suggestions</p>
                <p className="text-xs text-gray-400 mt-2">Powered by semantic search</p>
              </div>
            )}
          </>
        ) : (
          <div className="text-center text-gray-500 mt-8">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <p className="text-sm">Your library is empty</p>
            <p className="text-xs text-gray-400 mt-2">Papers you save will appear here</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CitationPanel;