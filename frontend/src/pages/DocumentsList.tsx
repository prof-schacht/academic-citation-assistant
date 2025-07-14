import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { documentService } from '../services/documentService';
import type { DocumentType } from '../services/documentService';
import { APP_VERSION, BUILD_NUMBER } from '../version';

const DocumentsList: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreatingDocument, setIsCreatingDocument] = useState(false);
  const navigationLock = useRef(false);

  useEffect(() => {
    loadDocuments();
    setIsCreatingDocument(false); // Reset flag when returning to this page
    navigationLock.current = false; // Reset navigation lock
    
    // Refresh documents list when navigating back
    const unsubscribe = () => {
      loadDocuments();
      setIsCreatingDocument(false);
      navigationLock.current = false;
    };
    
    window.addEventListener('focus', unsubscribe);
    return () => {
      window.removeEventListener('focus', unsubscribe);
      navigationLock.current = false;
    };
  }, []);

  const loadDocuments = async (search?: string) => {
    try {
      setIsLoading(true);
      const response = await documentService.list({
        search,
        limit: 50,
      });
      setDocuments(response.documents);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadDocuments(searchTerm);
  };

  const handleDelete = async (id: string, title: string) => {
    if (confirm(`Are you sure you want to delete "${title}"?`)) {
      try {
        await documentService.delete(id);
        setDocuments(documents.filter(doc => doc.id !== id));
      } catch (err) {
        console.error('Failed to delete document:', err);
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading documents...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">My Documents</h1>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/library')}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                📚 Paper Library
              </button>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  
                  // Use ref to prevent multiple navigations
                  if (!navigationLock.current) {
                    navigationLock.current = true;
                    setIsCreatingDocument(true);
                    navigate('/editor');
                    
                    // Reset lock after a delay
                    setTimeout(() => {
                      navigationLock.current = false;
                    }, 2000);
                  }
                }}
                onMouseDown={(e) => e.preventDefault()}
                disabled={isCreatingDocument || navigationLock.current}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed"
              >
                {isCreatingDocument ? 'Creating...' : '+ New Document'}
              </button>
            </div>
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="mt-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search documents..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Search
              </button>
            </div>
          </form>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {documents.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No documents found</p>
            <button
              type="button"
              onClick={async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (navigationLock.current === true) {
                  console.log('Navigation already in progress, ignoring click');
                  return;
                }
                
                console.log('Creating new document...');
                navigationLock.current = true;
                setIsCreatingDocument(true);
                
                await new Promise(resolve => setTimeout(resolve, 100));
                
                navigate('/editor');
              }}
              disabled={isCreatingDocument || navigationLock.current}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed select-none"
              style={{ pointerEvents: (isCreatingDocument || navigationLock.current) ? 'none' : 'auto' }}
            >
              {isCreatingDocument ? 'Creating...' : 'Create your first document'}
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="bg-white rounded-lg shadow-sm hover:shadow-md transition cursor-pointer overflow-hidden"
              >
                <div
                  onClick={() => navigate(`/editor/${doc.id}`)}
                  className="p-6"
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate">
                    {doc.title}
                  </h3>
                  {doc.description && (
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {doc.description}
                    </p>
                  )}
                  {!doc.description && (
                    <p className="text-gray-400 text-sm mb-4 italic">
                      No description
                    </p>
                  )}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{doc.word_count} words</span>
                    <span>{formatDate(doc.updated_at)}</span>
                  </div>
                </div>
                
                <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-200">
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="text-gray-600">
                      {doc.citation_count} citations
                    </span>
                    {doc.is_public && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Public</span>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(doc.id, doc.title);
                    }}
                    className="text-red-600 hover:text-red-700 font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
      
      {/* Version info for debugging */}
      <div className="fixed bottom-2 right-2 text-xs text-gray-500 bg-white px-2 py-1 rounded shadow">
        v{APP_VERSION} (Build: {BUILD_NUMBER})
      </div>
    </div>
  );
};

export default DocumentsList;