import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface Paper {
  id: string;
  title: string;
}

interface Chunk {
  id: string;
  chunk_index: number;
  content: string;
  start_char: number;
  end_char: number;
  word_count: number;
  section_title: string | null;
}

interface PaperChunksViewerProps {
  paper: Paper;
  isOpen: boolean;
  onClose: () => void;
}

export function PaperChunksViewer({ paper, isOpen, onClose }: PaperChunksViewerProps) {
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [fullText, setFullText] = useState<string>('');
  const [fullTextLength, setFullTextLength] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'text' | 'chunks'>('text');

  useEffect(() => {
    if (isOpen && paper) {
      fetchChunks();
    }
  }, [isOpen, paper]);

  const fetchChunks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/papers/${paper.id}/chunks`);
      setChunks(response.data.chunks);
      setFullText(response.data.full_text || '');
      setFullTextLength(response.data.full_text_length);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chunks');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  // Search for identifiers in the text
  const findIdentifiers = (text: string) => {
    const identifiers = [];
    
    // ArXiv patterns
    const arxivPatterns = [
      /arXiv[:\s]+(\d{4}\.\d{4,5}(?:v\d+)?)/gi,
      /10\.48550\/arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)/gi,
      /\b(\d{4}\.\d{4,5}(?:v\d+)?)\b/g
    ];
    
    // DOI patterns
    const doiPatterns = [
      /(?:doi[:\s]+|https?:\/\/doi\.org\/)(10\.\d{4,}\/[-._;()/:a-zA-Z0-9]+)/gi,
      /\b(10\.\d{4,}\/[-._;()/:a-zA-Z0-9]+)\b/g
    ];
    
    arxivPatterns.forEach(pattern => {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        identifiers.push({
          type: 'arXiv',
          value: match[1] || match[0],
          position: match.index || 0,
          fullMatch: match[0]
        });
      }
    });
    
    doiPatterns.forEach(pattern => {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        identifiers.push({
          type: 'DOI',
          value: match[1] || match[0],
          position: match.index || 0,
          fullMatch: match[0]
        });
      }
    });
    
    return identifiers;
  };

  const identifiers = findIdentifiers(fullText);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Paper Processing Details</h2>
              <p className="text-sm text-gray-600 mt-1">{paper.title}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={loading}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading chunks...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">
              <p>Error: {error}</p>
            </div>
          ) : (
            <>
              {/* Identifiers Found */}
              {identifiers.length > 0 && (
                <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">🔍 Identifiers Found</h3>
                  <div className="space-y-1">
                    {identifiers.map((id, idx) => (
                      <div key={idx} className="text-sm">
                        <span className="font-medium text-blue-700">{id.type}:</span>{' '}
                        <code className="bg-blue-100 px-2 py-0.5 rounded">{id.value}</code>
                        <span className="text-gray-500 ml-2">(at position {id.position})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tabs */}
              <div className="mb-6">
                <div className="flex border-b">
                  <button
                    className={`px-4 py-2 font-medium transition-colors ${
                      activeTab === 'text'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                    onClick={() => setActiveTab('text')}
                  >
                    Extracted Text ({fullTextLength} chars)
                  </button>
                  <button
                    className={`px-4 py-2 font-medium transition-colors ${
                      activeTab === 'chunks'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                    onClick={() => setActiveTab('chunks')}
                  >
                    Chunks ({chunks.length})
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="max-h-[60vh] overflow-y-auto">
                {activeTab === 'text' ? (
                  <div className="prose max-w-none">
                    <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-50 p-4 rounded">
                      {fullText || 'No text extracted'}
                      {fullTextLength > 5000 && (
                        <div className="mt-4 text-gray-500 italic">
                          ... (showing first 5000 characters of {fullTextLength} total)
                        </div>
                      )}
                    </pre>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chunks.map((chunk) => (
                      <div key={chunk.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <span className="font-semibold text-sm">
                              Chunk {chunk.chunk_index + 1}
                            </span>
                            {chunk.section_title && (
                              <span className="ml-2 text-sm text-gray-600">
                                - {chunk.section_title}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">
                            {chunk.word_count} words | chars {chunk.start_char}-{chunk.end_char}
                          </div>
                        </div>
                        <div className="text-sm text-gray-700 whitespace-pre-wrap">
                          {chunk.content}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}