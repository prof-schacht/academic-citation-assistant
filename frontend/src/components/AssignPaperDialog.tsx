import React, { useState, useEffect } from 'react';
import { paperService } from '../services/paperService';
import { documentPaperService } from '../services/documentPaperService';

interface Paper {
  id: string;
  title: string;
  authors: string[] | null;
  year: number | null;
  journal?: string;
  status: 'processing' | 'indexed' | 'error';
}

interface AssignPaperDialogProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onAssigned: () => void;
  excludePaperIds?: string[];
}

const AssignPaperDialog: React.FC<AssignPaperDialogProps> = ({
  documentId,
  documentTitle,
  isOpen,
  onClose,
  onAssigned,
  excludePaperIds = []
}) => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPapers, setSelectedPapers] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isAssigning, setIsAssigning] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadPapers();
    }
  }, [isOpen]);

  const loadPapers = async () => {
    setIsLoading(true);
    try {
      const allPapers = await paperService.getUserPapers();
      // Filter out already assigned papers and processing papers
      const availablePapers = allPapers.filter(
        paper => !excludePaperIds.includes(paper.id) && paper.status === 'indexed'
      );
      setPapers(availablePapers);
    } catch (error) {
      console.error('Failed to load papers:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePaper = (paperId: string) => {
    const newSelected = new Set(selectedPapers);
    if (newSelected.has(paperId)) {
      newSelected.delete(paperId);
    } else {
      newSelected.add(paperId);
    }
    setSelectedPapers(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedPapers.size === filteredPapers.length) {
      setSelectedPapers(new Set());
    } else {
      setSelectedPapers(new Set(filteredPapers.map(p => p.id)));
    }
  };

  const handleAssign = async () => {
    if (selectedPapers.size === 0) return;

    setIsAssigning(true);
    try {
      await documentPaperService.bulkAssignPapers(
        documentId,
        Array.from(selectedPapers)
      );
      onAssigned();
      onClose();
      setSelectedPapers(new Set());
    } catch (error) {
      console.error('Failed to assign papers:', error);
      alert('Failed to assign papers. Please try again.');
    } finally {
      setIsAssigning(false);
    }
  };

  const filteredPapers = papers.filter(paper => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      paper.title.toLowerCase().includes(query) ||
      (paper.authors && paper.authors.some(author => author.toLowerCase().includes(query))) ||
      (paper.journal && paper.journal.toLowerCase().includes(query))
    );
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            Assign Papers to "{documentTitle}"
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Select papers to add to this document's bibliography
          </p>
        </div>

        <div className="px-6 py-4 border-b">
          <input
            type="text"
            placeholder="Search papers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Loading papers...</div>
          ) : filteredPapers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {papers.length === 0 
                ? "No papers available to assign" 
                : "No papers match your search"}
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">
                  {selectedPapers.size} of {filteredPapers.length} selected
                </span>
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  {selectedPapers.size === filteredPapers.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              
              {filteredPapers.map(paper => (
                <label
                  key={paper.id}
                  className="flex items-start p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedPapers.has(paper.id)}
                    onChange={() => handleTogglePaper(paper.id)}
                    className="mt-1 mr-3"
                  />
                  <div className="flex-1">
                    <h4 className="font-medium">{paper.title}</h4>
                    {paper.authors && paper.authors.length > 0 && (
                      <p className="text-sm text-gray-600">
                        {paper.authors.join(', ')}
                      </p>
                    )}
                    <p className="text-sm text-gray-500">
                      {paper.year && `${paper.year}`}
                      {paper.year && paper.journal && ' • '}
                      {paper.journal}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isAssigning}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleAssign}
            disabled={selectedPapers.size === 0 || isAssigning}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAssigning ? 'Assigning...' : `Assign ${selectedPapers.size} Paper${selectedPapers.size !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssignPaperDialog;