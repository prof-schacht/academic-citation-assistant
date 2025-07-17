import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload/FileUpload';
import SelectDocumentDialog from '../components/SelectDocumentDialog';
import SettingsModal from '../components/SettingsModal';
import { paperService } from '../services/paperService';

interface Paper {
  id: string;
  title: string;
  authors: string[] | null;
  year: number | null;
  journal?: string;
  citation_count?: number;
  chunk_count?: number;
  status: 'processing' | 'indexed' | 'error';
  created_at: string;
}

const PaperLibrary: React.FC = () => {
  const navigate = useNavigate();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'indexed' | 'processing' | 'error'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'citations'>('date');
  const [selectedPaper, setSelectedPaper] = useState<{ id: string; title: string } | null>(null);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    loadPapers();
    
    // Poll for updates every 3 seconds while any papers are processing
    const interval = setInterval(() => {
      loadPapers();
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const loadPapers = async () => {
    try {
      const userPapers = await paperService.getUserPapers();
      setPapers(userPapers);
    } catch (error) {
      console.error('Failed to load papers:', error);
    } finally {
      if (isLoading) {
        setIsLoading(false);
      }
    }
  };
  
  const handleDeletePaper = async (paperId: string) => {
    if (!confirm('Are you sure you want to delete this paper?')) {
      return;
    }
    
    try {
      await paperService.deletePaper(paperId);
      await loadPapers();
    } catch (error) {
      console.error('Failed to delete paper:', error);
      alert('Failed to delete paper');
    }
  };

  const handleFilesSelected = async (files: File[]) => {
    console.log('Files selected for upload:', files);
    try {
      for (const file of files) {
        await paperService.uploadPaper(file);
      }
      // Immediately reload papers after upload to show processing status
      await loadPapers();
      // Close the upload section
      setShowUpload(false);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file. Please try again.');
    }
  };

  const filteredPapers = papers
    .filter(paper => {
      if (filterStatus !== 'all' && paper.status !== filterStatus) return false;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          paper.title.toLowerCase().includes(query) ||
          (paper.authors && paper.authors.some(author => author.toLowerCase().includes(query)))
        );
      }
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'citations':
          return (b.citation_count || 0) - (a.citation_count || 0);
        case 'date':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - Following Issue #6 design */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              📚 Paper Library
            </h1>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/documents')}
                className="text-gray-600 hover:text-gray-900"
              >
                Back to Documents
              </button>
              <button
                onClick={() => navigate('/logs')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                View Logs
              </button>
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                + Upload Papers
              </button>
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 text-gray-600 hover:text-gray-900"
                title="Settings"
              >
                ⚙️
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Upload Section */}
        {showUpload && (
          <div className="mb-8 bg-white rounded-lg shadow p-6">
            <FileUpload onFilesSelected={handleFilesSelected} />
          </div>
        )}

        {/* Library Controls - Following Issue #6 design */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">
                My Papers ({papers.length})
              </h2>
            </div>
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  placeholder="🔍 Search papers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as any)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Filter: All</option>
                <option value="indexed">Indexed</option>
                <option value="processing">Processing</option>
                <option value="error">Errors</option>
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="date">Sort: Date</option>
                <option value="title">Sort: Title</option>
                <option value="citations">Sort: Citations</option>
              </select>
            </div>
          </div>

          {/* Papers List */}
          <div className="divide-y">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">
                Loading papers...
              </div>
            ) : filteredPapers.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                {searchQuery || filterStatus !== 'all'
                  ? 'No papers match your search criteria'
                  : 'No papers uploaded yet. Click "Upload Papers" to get started!'}
              </div>
            ) : (
              filteredPapers.map(paper => (
                <div
                  key={paper.id}
                  className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => {/* TODO: View paper details */}}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">📄</span>
                        <h3 className="font-semibold text-gray-900">
                          {paper.title}
                        </h3>
                      </div>
                      <div className="mt-1 text-sm text-gray-600">
                        {paper.authors && paper.authors.length > 0 ? (
                          <>
                            {paper.authors.slice(0, 3).join(', ')}
                            {paper.authors.length > 3 && ' et al.'}
                            {' • '}
                          </>
                        ) : null}
                        {paper.year || 'No year'}
                        {paper.journal && ` • ${paper.journal}`}
                        {paper.citation_count !== undefined && ` • ${paper.citation_count.toLocaleString()} citations`}
                      </div>
                      <div className="mt-2 flex items-center space-x-4 text-sm">
                        {paper.status === 'indexed' ? (
                          <span className="text-green-600">
                            ✓ Fully indexed • {paper.chunk_count || 0} chunks
                          </span>
                        ) : paper.status === 'processing' ? (
                          <span className="text-yellow-600">
                            ⚙️ Processing...
                          </span>
                        ) : (
                          <span className="text-red-600">
                            ❌ Error processing
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="ml-4 flex items-center space-x-2">
                      {paper.status === 'indexed' && (
                        <button
                          className="p-1 text-gray-400 hover:text-blue-600"
                          title="Assign to Document"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedPaper({ id: paper.id, title: paper.title });
                            setShowAssignDialog(true);
                          }}
                        >
                          📎
                        </button>
                      )}
                      <button
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Edit"
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Edit paper metadata
                        }}
                      >
                        ✏️
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeletePaper(paper.id);
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Select Document Dialog */}
      {selectedPaper && (
        <SelectDocumentDialog
          paperId={selectedPaper.id}
          paperTitle={selectedPaper.title}
          isOpen={showAssignDialog}
          onClose={() => {
            setShowAssignDialog(false);
            setSelectedPaper(null);
          }}
          onAssigned={() => {
            setShowAssignDialog(false);
            setSelectedPaper(null);
          }}
        />
      )}

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  );
};

export default PaperLibrary;