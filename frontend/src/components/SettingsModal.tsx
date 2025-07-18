import React, { useState } from 'react';
import { adminService } from '../services/adminService';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'general' | 'database'>('general');
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteResult, setDeleteResult] = useState<{
    documents: number;
    citations: number;
    documentPapers: number;
  } | null>(null);

  if (!isOpen) return null;

  const handleCleanDatabase = async () => {
    if (deleteConfirmation !== 'DELETE ALL') {
      alert('Please type "DELETE ALL" to confirm');
      return;
    }

    if (!confirm('This action will permanently delete ALL documents from ALL users. This cannot be undone. Are you absolutely sure?')) {
      return;
    }

    try {
      setIsDeleting(true);
      const result = await adminService.cleanAllDocuments(deleteConfirmation);
      setDeleteResult({
        documents: result.documents_deleted,
        citations: result.citations_deleted,
        documentPapers: result.document_papers_deleted,
      });
      setDeleteConfirmation('');
    } catch (error) {
      console.error('Failed to clean database:', error);
      alert('Failed to clean database. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    setDeleteConfirmation('');
    setDeleteResult(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
            <button
              onClick={handleClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('general')}
            className={`px-6 py-3 font-medium transition ${
              activeTab === 'general'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            General
          </button>
          <button
            onClick={() => setActiveTab('database')}
            className={`px-6 py-3 font-medium transition ${
              activeTab === 'database'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Database Management
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {activeTab === 'general' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">General Settings</h3>
              <p className="text-gray-600">General settings will be available here in the future.</p>
            </div>
          )}

          {activeTab === 'database' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Database Management</h3>
              
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-medium text-red-900 mb-2">Danger Zone</h4>
                <p className="text-red-700 mb-4">
                  These actions are destructive and cannot be undone. Please proceed with caution.
                </p>

                <div className="space-y-4">
                  <div>
                    <h5 className="font-medium text-red-900 mb-2">Clean All Documents</h5>
                    <p className="text-sm text-red-700 mb-3">
                      This will permanently delete ALL documents from ALL users in the database. 
                      User accounts and papers will be preserved.
                    </p>
                    
                    {deleteResult && (
                      <div className="bg-green-50 border border-green-200 rounded p-3 mb-3">
                        <p className="text-green-800 text-sm">
                          Successfully deleted:
                          <br />• {deleteResult.documents} documents
                          <br />• {deleteResult.citations} citations
                          <br />• {deleteResult.documentPapers} document-paper associations
                        </p>
                      </div>
                    )}

                    <div className="flex items-center space-x-3">
                      <input
                        type="text"
                        value={deleteConfirmation}
                        onChange={(e) => setDeleteConfirmation(e.target.value)}
                        placeholder='Type "DELETE ALL" to confirm'
                        className="flex-1 px-3 py-2 border border-red-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                        disabled={isDeleting}
                      />
                      <button
                        onClick={handleCleanDatabase}
                        disabled={isDeleting || deleteConfirmation !== 'DELETE ALL'}
                        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:bg-red-400 disabled:cursor-not-allowed"
                      >
                        {isDeleting ? 'Cleaning...' : 'Clean Database'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;