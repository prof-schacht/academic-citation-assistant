import React, { useState, useEffect } from 'react';
import { paperService } from '../../services/paperService';

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
  metadata_source?: string;
  abstract?: string;
  doi?: string;
  arxiv_id?: string;
  pubmed_id?: string;
  semantic_scholar_id?: string;
}

interface PaperMetadataEditorProps {
  paper: Paper;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (updatedPaper: Paper) => void;
}

export function PaperMetadataEditor({
  paper,
  isOpen,
  onClose,
  onUpdate,
}: PaperMetadataEditorProps) {
  const [formData, setFormData] = useState({
    title: '',
    authors: [] as string[],
    abstract: '',
    year: '',
    journal: '',
    doi: '',
  });
  const [bibtex, setBibtex] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'form' | 'bibtex'>('form');

  useEffect(() => {
    // Initialize form with paper data
    setFormData({
      title: paper.title || '',
      authors: paper.authors || [],
      abstract: paper.abstract || '',
      year: paper.year?.toString() || '',
      journal: paper.journal || '',
      doi: paper.doi || '',
    });
    setBibtex('');
    setError(null);
  }, [paper, isOpen]);

  if (!isOpen) return null;

  const handleFormChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAuthorsChange = (value: string) => {
    // Split by comma or semicolon
    const authors = value.split(/[,;]/).map(a => a.trim()).filter(a => a);
    setFormData(prev => ({ ...prev, authors }));
  };

  const parseBibtex = () => {
    // Simple BibTeX parser - in production, we'd use the backend API
    try {
      const titleMatch = bibtex.match(/title\s*=\s*[{"']([^}"']+)[}"']/i);
      const authorMatch = bibtex.match(/author\s*=\s*[{"']([^}"']+)[}"']/i);
      const yearMatch = bibtex.match(/year\s*=\s*[{"'](\d{4})[}"']/i);
      const journalMatch = bibtex.match(/(?:journal|booktitle)\s*=\s*[{"']([^}"']+)[}"']/i);
      const doiMatch = bibtex.match(/doi\s*=\s*[{"']([^}"']+)[}"']/i);
      const abstractMatch = bibtex.match(/abstract\s*=\s*[{"']([^}"']+)[}"']/i);

      const parsed: any = {};
      if (titleMatch) parsed.title = titleMatch[1].replace(/[{}]/g, '');
      if (authorMatch) {
        // Parse "Last, First and Last, First" format
        const authorString = authorMatch[1];
        const authors = authorString.split(' and ').map(author => {
          author = author.trim();
          if (author.includes(',')) {
            const [last, first] = author.split(',', 2);
            return `${first.trim()} ${last.trim()}`;
          }
          return author;
        });
        parsed.authors = authors;
      }
      if (yearMatch) parsed.year = yearMatch[1];
      if (journalMatch) parsed.journal = journalMatch[1].replace(/[{}]/g, '');
      if (doiMatch) parsed.doi = doiMatch[1];
      if (abstractMatch) parsed.abstract = abstractMatch[1].replace(/[{}]/g, '');

      setFormData(prev => ({ ...prev, ...parsed }));
      setActiveTab('form');
      setError(null);
    } catch (err) {
      setError('Failed to parse BibTeX. Please check the format.');
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const updateData: any = {
        title: formData.title,
        authors: formData.authors,
        abstract: formData.abstract || null,
        year: formData.year ? parseInt(formData.year) : null,
        journal: formData.journal || null,
        doi: formData.doi || null,
      };

      const updatedPaper = await paperService.updatePaper(paper.id, updateData);
      onUpdate(updatedPaper);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update paper metadata');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Edit Paper Metadata</h2>
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
          {paper.metadata_source && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg flex items-start space-x-2">
              <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-blue-800">
                Current metadata source: <strong>{paper.metadata_source}</strong>
              </div>
            </div>
          )}

          <div className="mb-6">
            <div className="flex border-b">
              <button
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'form'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                onClick={() => setActiveTab('form')}
              >
                Manual Edit
              </button>
              <button
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'bibtex'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                onClick={() => setActiveTab('bibtex')}
              >
                Import BibTeX
              </button>
            </div>
          </div>

          {activeTab === 'form' ? (
            <div className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  id="title"
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleFormChange('title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Paper title"
                />
              </div>

              <div>
                <label htmlFor="authors" className="block text-sm font-medium text-gray-700 mb-1">
                  Authors (comma-separated)
                </label>
                <input
                  id="authors"
                  type="text"
                  value={formData.authors.join(', ')}
                  onChange={(e) => handleAuthorsChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe, Jane Smith"
                />
              </div>

              <div>
                <label htmlFor="abstract" className="block text-sm font-medium text-gray-700 mb-1">
                  Abstract
                </label>
                <textarea
                  id="abstract"
                  value={formData.abstract}
                  onChange={(e) => handleFormChange('abstract', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Paper abstract"
                  rows={4}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-1">
                    Year
                  </label>
                  <input
                    id="year"
                    type="number"
                    value={formData.year}
                    onChange={(e) => handleFormChange('year', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="2024"
                    min="1900"
                    max="2100"
                  />
                </div>

                <div>
                  <label htmlFor="journal" className="block text-sm font-medium text-gray-700 mb-1">
                    Journal/Venue
                  </label>
                  <input
                    id="journal"
                    type="text"
                    value={formData.journal}
                    onChange={(e) => handleFormChange('journal', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Journal name or conference"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="doi" className="block text-sm font-medium text-gray-700 mb-1">
                  DOI
                </label>
                <input
                  id="doi"
                  type="text"
                  value={formData.doi}
                  onChange={(e) => handleFormChange('doi', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="10.1234/example"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label htmlFor="bibtex" className="block text-sm font-medium text-gray-700 mb-1">
                  Paste BibTeX Entry
                </label>
                <textarea
                  id="bibtex"
                  value={bibtex}
                  onChange={(e) => setBibtex(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder={`@article{key2024,
  title = {Your Paper Title},
  author = {Doe, John and Smith, Jane},
  year = {2024},
  journal = {Journal Name},
  doi = {10.1234/example}
}`}
                  rows={10}
                />
              </div>
              <button
                onClick={parseBibtex}
                disabled={!bibtex.trim()}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Parse BibTeX
              </button>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-800 rounded-lg flex items-start space-x-2">
              <svg className="w-5 h-5 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm">{error}</div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t px-6 py-4">
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update Metadata'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}