import React, { useState, useEffect } from 'react';
import { documentService } from '../services/documentService';
import { documentPaperService } from '../services/documentPaperService';
import type { DocumentType } from '../services/documentService';

interface SelectDocumentDialogProps {
  paperId: string;
  paperTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onAssigned: () => void;
}

const SelectDocumentDialog: React.FC<SelectDocumentDialogProps> = ({
  paperId,
  paperTitle,
  isOpen,
  onClose,
  onAssigned
}) => {
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isAssigning, setIsAssigning] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen]);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await documentService.list({ limit: 100 });
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!selectedDocumentId) return;

    setIsAssigning(true);
    try {
      await documentPaperService.assignPaper(selectedDocumentId, {
        paper_id: paperId,
        notes: notes.trim() || undefined
      });
      onAssigned();
      onClose();
      // Reset state
      setSelectedDocumentId('');
      setNotes('');
    } catch (error: any) {
      console.error('Failed to assign paper:', error);
      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert('Failed to assign paper. Please try again.');
      }
    } finally {
      setIsAssigning(false);
    }
  };

  const filteredDocuments = documents.filter(doc => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return doc.title.toLowerCase().includes(query);
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            Assign Paper to Document
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Select a document to add "{paperTitle}" to its bibliography
          </p>
        </div>

        <div className="px-6 py-4 border-b">
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Loading documents...</div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {documents.length === 0 
                ? "No documents found. Create a document first." 
                : "No documents match your search"}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDocuments.map(doc => (
                <label
                  key={doc.id}
                  className="flex items-start p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="document"
                    value={doc.id}
                    checked={selectedDocumentId === doc.id}
                    onChange={(e) => setSelectedDocumentId(e.target.value)}
                    className="mt-1 mr-3"
                  />
                  <div className="flex-1">
                    <h4 className="font-medium">{doc.title}</h4>
                    <p className="text-sm text-gray-500">
                      {doc.word_count.toLocaleString()} words • 
                      {doc.citation_count} citations • 
                      Last updated {new Date(doc.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          )}
          
          {selectedDocumentId && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes about why this paper is relevant to your document..."
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
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
            disabled={!selectedDocumentId || isAssigning}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAssigning ? 'Assigning...' : 'Assign to Document'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SelectDocumentDialog;