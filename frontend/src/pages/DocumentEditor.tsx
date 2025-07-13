import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '../components/Editor/Editor';
import CitationPanel from '../components/CitationPanel/CitationPanel';
import ExportDialog from '../components/ExportDialog';
import { documentService } from '../services/documentService';
import type { DocumentType } from '../services/documentService';
import type { EditorState } from 'lexical';

// Global counter for debugging
let effectRunCount = 0;

const DocumentEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showCitationPanel, setShowCitationPanel] = useState(true);
  const editorStateRef = useRef<EditorState | null>(null);

  useEffect(() => {
    let mounted = true;
    effectRunCount++;
    console.log(`DocumentEditor useEffect run #${effectRunCount}, id: ${id}`);
    
    const init = async () => {
      if (!mounted) return;
      
      if (id) {
        await loadDocument(id);
      } else {
        // Small delay to ensure single execution
        const timeoutId = setTimeout(() => {
          if (mounted) {
            createNewDocument();
          }
        }, 50);
        
        return () => clearTimeout(timeoutId);
      }
    };
    
    init();
    
    return () => {
      mounted = false;
      // Clean up session storage on unmount
      if (!id) {
        sessionStorage.removeItem('creating-new-document');
      }
    };
  }, [id]); // Remove isCreating from dependencies

  const loadDocument = async (docId: string) => {
    try {
      setIsLoading(true);
      const doc = await documentService.getById(docId);
      setDocument(doc);
      return doc;
    } catch (err) {
      setError('Failed to load document');
      console.error(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const createNewDocument = async () => {
    // Use sessionStorage to prevent duplicate creation
    const creationKey = 'creating-new-document';
    const lastCreationKey = 'last-document-creation';
    const isAlreadyCreating = sessionStorage.getItem(creationKey);
    const lastCreation = sessionStorage.getItem(lastCreationKey);
    
    // Check if we're already creating or created a document in the last 2 seconds
    if (isAlreadyCreating === 'true' || isCreating) {
      console.log('Document creation already in progress, skipping...');
      return;
    }
    
    if (lastCreation) {
      const timeSinceLastCreation = Date.now() - parseInt(lastCreation);
      if (timeSinceLastCreation < 2000) {
        console.log('Document was created recently, skipping...', timeSinceLastCreation);
        return;
      }
    }
    
    try {
      // Set both local state and sessionStorage
      sessionStorage.setItem(creationKey, 'true');
      setIsCreating(true);
      setIsLoading(true);
      
      console.log('Creating new document...');
      const newDoc = await documentService.create({
        title: 'Untitled Document',
        description: '',
        content: null,
        is_public: false,
      });
      console.log('Document created:', newDoc.id);
      
      setDocument(newDoc);
      // Set the last creation timestamp
      sessionStorage.setItem(lastCreationKey, Date.now().toString());
      // Clear the flag before navigation
      sessionStorage.removeItem(creationKey);
      // Redirect to the new document URL
      navigate(`/editor/${newDoc.id}`, { replace: true });
    } catch (err) {
      setError('Failed to create document');
      console.error(err);
      sessionStorage.removeItem(creationKey);
    } finally {
      setIsLoading(false);
      setIsCreating(false);
    }
  };

  const handleTitleChange = async (newTitle: string) => {
    if (!document) return;
    
    try {
      const updated = await documentService.update(document.id, { title: newTitle });
      setDocument(updated);
    } catch (err) {
      console.error('Failed to update title:', err);
    }
  };

  const handleTitleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const newTitle = e.target.value.trim();
    if (newTitle && newTitle !== document?.title) {
      handleTitleChange(newTitle);
    } else if (!newTitle && document?.title) {
      // If user clears the title, restore the original
      e.target.value = document.title;
    }
  };

  const handleSave = (content: any, editorState?: EditorState) => {
    console.log('Document saved:', content);
    if (editorState) {
      editorStateRef.current = editorState;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600">
          <h2 className="text-xl font-bold mb-2">Error</h2>
          <p>{error}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  if (!document) {
    return null;
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/documents')}
              className="text-gray-600 hover:text-gray-900"
              title="Back to documents"
            >
              ← Back
            </button>
            <input
              type="text"
              defaultValue={document.title}
              onBlur={handleTitleBlur}
              className="text-2xl font-bold border-none outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
              placeholder="Document Title"
            />
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowExportDialog(true)}
              className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Export
            </button>
            <button
              onClick={() => setShowCitationPanel(!showCitationPanel)}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {showCitationPanel ? 'Hide' : 'Show'} Citations
            </button>
          </div>
        </div>
      </header>

      {/* Main content area with split layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Editor - 60% width */}
        <div className="flex-[3] min-w-[400px] overflow-hidden border-r border-gray-200">
          <Editor
            documentId={document.id}
            initialContent={document.content || undefined}
            onSave={handleSave}
            autoSaveDelay={2000}
          />
        </div>
        
        {/* Citation suggestions panel - 40% width */}
        {showCitationPanel && (
          <div className="flex-[2] min-w-[300px] bg-gray-50 overflow-hidden">
            <CitationPanel documentId={document.id} />
          </div>
        )}
      </div>

      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        documentTitle={document.title}
        editorState={editorStateRef.current}
      />
    </div>
  );
};

export default DocumentEditor;