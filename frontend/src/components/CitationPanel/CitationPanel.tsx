import React, { useState, useEffect } from 'react';

interface Citation {
  id: string;
  title: string;
  authors: string[];
  year: number;
  journal?: string;
  abstract?: string;
  relevanceScore: number;
}

interface CitationPanelProps {
  documentId: string;
  selectedText?: string;
}

const CitationPanel: React.FC<CitationPanelProps> = ({ documentId, selectedText }) => {
  const [citations, setCitations] = useState<Citation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'suggestions' | 'library'>('suggestions');

  // Placeholder data for now
  const placeholderCitations: Citation[] = [
    {
      id: '1',
      title: 'Deep Learning for Natural Language Processing',
      authors: ['Smith, J.', 'Doe, A.'],
      year: 2023,
      journal: 'Journal of AI Research',
      relevanceScore: 0.95,
    },
    {
      id: '2',
      title: 'Advances in Neural Machine Translation',
      authors: ['Johnson, M.', 'Lee, K.'],
      year: 2023,
      journal: 'Computational Linguistics',
      relevanceScore: 0.87,
    },
  ];

  const handleInsertCitation = (citation: Citation) => {
    console.log('Inserting citation:', citation);
    // TODO: Implement citation insertion into editor
  };

  const handleAddToLibrary = (citation: Citation) => {
    console.log('Adding to library:', citation);
    // TODO: Implement adding to library
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header with tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex items-center justify-between p-4">
          <h2 className="text-lg font-semibold text-gray-900">Citations</h2>
          <button
            className="text-sm text-blue-600 hover:text-blue-700"
            onClick={() => console.log('Search papers')}
          >
            Search papers
          </button>
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

            {isLoading ? (
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
            ) : placeholderCitations.length > 0 ? (
              <div className="space-y-3">
                {placeholderCitations.map((citation) => (
                  <div
                    key={citation.id}
                    className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 text-sm mb-1">
                          {citation.title}
                        </h4>
                        <p className="text-xs text-gray-600 mb-2">
                          {citation.authors.join(', ')} • {citation.year}
                          {citation.journal && ` • ${citation.journal}`}
                        </p>
                        <div className="flex items-center space-x-4">
                          <span className="text-xs text-gray-500">
                            Relevance: {Math.round(citation.relevanceScore * 100)}%
                          </span>
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
                        className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition"
                      >
                        Add to Library
                      </button>
                      <button
                        className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800 transition"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                ))}
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