import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Settings } from 'lucide-react';
import Editor from '../components/Editor/Editor';
import CitationPanel from '../components/CitationPanel/CitationPanel';
import DocumentPapers from '../components/DocumentPapersSimple';
import ExportDialog from '../components/ExportDialog';
import PdfViewer from '../components/PdfViewer';
import PaperUploadModal from '../components/PaperUploadModal';
import { CitationSettings } from '../components/CitationSettings';
import { documentService } from '../services/documentService';
import { documentPaperService } from '../services/documentPaperService';
import { OverleafService } from '../services/overleafService';
import type { DocumentType } from '../services/documentService';
import type { EditorState } from 'lexical';
import type { CitationSuggestion, CitationConfig } from '../services/websocketService';

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
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCitationPanel, setShowCitationPanel] = useState(true);
  const [activeTab, setActiveTab] = useState<'editor' | 'bibliography' | 'citations'>('editor');
  const [citationSuggestions, setCitationSuggestions] = useState<CitationSuggestion[]>([]);
  const [citationConnectionStatus, setCitationConnectionStatus] = useState(false);
  const [insertedCitations, setInsertedCitations] = useState<CitationSuggestion[]>([]);
  const [bibliographyKey, setBibliographyKey] = useState(0); // Force refresh of bibliography
  const [bibliographyPaperIds, setBibliographyPaperIds] = useState<Set<string>>(new Set());
  const [citedPaperIds, setCitedPaperIds] = useState<Set<string>>(new Set());
  const [isExportingToOverleaf, setIsExportingToOverleaf] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState<CitationSuggestion | null>(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [showCitationSettings, setShowCitationSettings] = useState(false);
  const [citationConfig, setCitationConfig] = useState<CitationConfig>({
    useEnhanced: true,
    useReranking: true,
    searchStrategy: 'hybrid'
  });
  const editorStateRef = useRef<EditorState | null>(null);
  const insertCitationRef = useRef<((citation: CitationSuggestion) => void) | null>(null);
  const editorSaveRef = useRef<(() => void) | null>(null);

  // Update citedPaperIds whenever insertedCitations changes
  useEffect(() => {
    const paperIds = new Set(insertedCitations.map(c => c.paperId));
    setCitedPaperIds(paperIds);
    console.log('[DocumentEditor] Updated citedPaperIds:', Array.from(paperIds));
  }, [insertedCitations]);

  useEffect(() => {
    let mounted = true;
    effectRunCount++;
    console.log(`DocumentEditor useEffect run #${effectRunCount}, id: ${id}`);
    
    const init = async () => {
      if (!mounted) return;
      
      if (id) {
        await loadDocument(id);
        await loadBibliographyPapers(id);
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
      
      // Parse document content to find cited papers
      if (doc.content) {
        parseCitationsFromContent(doc.content);
      }
      
      return doc;
    } catch (err) {
      setError('Failed to load document');
      console.error(err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const loadBibliographyPapers = async (docId: string) => {
    try {
      const papers = await documentPaperService.getDocumentPapers(docId);
      const paperIds = new Set(papers.map(p => p.paper_id));
      setBibliographyPaperIds(paperIds);
      console.log('Loaded bibliography papers:', paperIds.size);
    } catch (err) {
      console.error('Failed to load bibliography papers:', err);
    }
  };

  const parseCitationsFromContent = (content: any) => {
    try {
      const contentObj = typeof content === 'string' ? JSON.parse(content) : content;
      const citations: CitationSuggestion[] = [];
      
      // Recursive function to find all citation nodes
      const findCitationNodes = (node: any) => {
        if (node.type === 'citation') {
          // This is a citation node
          citations.push({
            paperId: node.paperId,
            title: node.title || '',
            authors: node.authors || [],
            year: node.year,
            abstract: '',
            confidence: 1.0,
            citationStyle: 'inline' as const,
            displayText: node.citationKey || ''
          });
        }
        
        // Check children nodes
        if (node.children && Array.isArray(node.children)) {
          node.children.forEach(findCitationNodes);
        }
      };
      
      // Start parsing from root
      if (contentObj.root && contentObj.root.children) {
        contentObj.root.children.forEach(findCitationNodes);
      }
      
      console.log('[DocumentEditor] Found citations in document:', citations.length);
      setInsertedCitations(citations);
    } catch (err) {
      console.error('Failed to parse citations from content:', err);
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

  const handleTabChange = async (newTab: 'editor' | 'bibliography' | 'citations') => {
    console.log('[DocumentEditor] Tab change from', activeTab, 'to', newTab);
    
    // Save current editor content before switching tabs
    if (activeTab === 'editor' && editorSaveRef.current) {
      console.log('[DocumentEditor] Forcing save before tab change');
      // Call the save function and wait a moment for it to complete
      editorSaveRef.current();
      // Add a small delay to ensure the save completes
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // When switching back from bibliography, reload bibliography papers
    // to catch any deletions that might have occurred
    if (activeTab === 'bibliography' && newTab !== 'bibliography' && document) {
      console.log('[DocumentEditor] Reloading bibliography papers after leaving bibliography tab');
      await loadBibliographyPapers(document.id);
    }
    
    setActiveTab(newTab);
  };

  const handleCitationInserted = async (citation: CitationSuggestion) => {
    if (!document) return;

    console.log('[DocumentEditor] Citation inserted:', citation.paperId, citation.title);

    // Add to inserted citations list if not already there
    setInsertedCitations(prev => {
      const exists = prev.some(c => c.paperId === citation.paperId);
      if (!exists) {
        console.log('[DocumentEditor] Adding to insertedCitations:', citation.paperId);
        return [...prev, citation];
      }
      console.log('[DocumentEditor] Citation already in insertedCitations:', citation.paperId);
      return prev;
    });

    // Auto-add to bibliography
    try {
      await documentPaperService.assignPaper(document.id, {
        paper_id: citation.paperId,
        notes: `Cited in document`,
      });
      console.log('Paper added to bibliography:', citation.title);
      // Force bibliography refresh
      setBibliographyKey(prev => prev + 1);
      // Add to bibliography set
      setBibliographyPaperIds(prev => new Set([...prev, citation.paperId]));
    } catch (error) {
      // Paper might already be in bibliography, which is fine
      console.log('Paper already in bibliography or error adding:', error);
    }

    // Force a save after citation insertion to ensure the document is saved
    // This is necessary because programmatic citation insertion might not trigger onChange
    if (editorSaveRef.current) {
      console.log('Triggering save after citation insertion');
      setTimeout(() => {
        editorSaveRef.current?.();
      }, 100); // Small delay to ensure the editor state is updated
    }
  };

  const handleAddToLibrary = async (citation: CitationSuggestion) => {
    if (!document) return;

    try {
      await documentPaperService.assignPaper(document.id, {
        paper_id: citation.paperId,
        notes: `Added to bibliography`,
      });
      console.log('Paper added to bibliography:', citation.title);
      // Force bibliography refresh
      setBibliographyKey(prev => prev + 1);
      // Add to bibliography set
      setBibliographyPaperIds(prev => new Set([...prev, citation.paperId]));
    } catch (error) {
      console.error('Failed to add paper to bibliography:', error);
    }
  };

  const handleOpenInOverleaf = async () => {
    if (!document) return;
    
    setIsExportingToOverleaf(true);
    
    try {
      // Save current content before exporting
      if (editorSaveRef.current) {
        editorSaveRef.current();
        // Wait a moment for save to complete
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      await OverleafService.exportToOverleaf({
        documentId: document.id,
        documentTitle: document.title,
        useReferencesFilename: true
      });
      
      // Show success (Overleaf opened in new tab)
      console.log('Document exported to Overleaf successfully');
    } catch (error) {
      console.error('Failed to export to Overleaf:', error);
      alert('Failed to export to Overleaf. Please try again.');
    } finally {
      setIsExportingToOverleaf(false);
    }
  };

  const handleViewPaperDetails = (paper: CitationSuggestion) => {
    console.log('Viewing paper details:', paper.title);
    setSelectedPaper(paper);
    setShowPdfViewer(true);
  };

  const handleClosePdfViewer = () => {
    setShowPdfViewer(false);
    setSelectedPaper(null);
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
              onClick={() => setShowUploadModal(true)}
              className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center space-x-1"
              title="Upload papers to library"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span>Upload Papers</span>
            </button>
            <button
              onClick={() => setShowExportDialog(true)}
              className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Export
            </button>
            <button
              onClick={handleOpenInOverleaf}
              disabled={isExportingToOverleaf}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
            >
              {isExportingToOverleaf ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Opening...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                    <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                  </svg>
                  <span>Open in Overleaf</span>
                </>
              )}
            </button>
            <div className="flex items-center gap-2">
              {showCitationPanel && (
                <button
                  onClick={() => setShowCitationSettings(!showCitationSettings)}
                  className="p-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                  title="Citation Settings"
                >
                  <Settings className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={() => setShowCitationPanel(!showCitationPanel)}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                {showCitationPanel ? 'Hide' : 'Show'} Citations
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tab navigation */}
      <div className="border-b border-gray-200 bg-white">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          <button
            onClick={() => handleTabChange('editor')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'editor'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Editor
          </button>
          <button
            onClick={() => handleTabChange('bibliography')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'bibliography'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Bibliography
          </button>
          <button
            onClick={() => handleTabChange('citations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm relative ${
              activeTab === 'citations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Citations
            {citationSuggestions.length > 0 && activeTab !== 'citations' && (
              <span className="absolute -top-1 -right-2 bg-blue-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {citationSuggestions.length}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-hidden" onClick={(e) => {
        // Save when clicking outside editor but within the document area
        const target = e.target as HTMLElement;
        if (activeTab === 'editor' && 
            editorSaveRef.current && 
            !target.closest('.lexical-editor') && 
            !target.closest('.citation-panel')) {
          console.log('[DocumentEditor] Click outside editor - saving');
          editorSaveRef.current();
        }
      }}>
        {/* Editor tab - keep mounted but hidden to preserve state */}
        <div className={`h-full ${activeTab === 'editor' ? '' : 'hidden'}`}>
          <PanelGroup direction="horizontal" className="h-full">
            {/* Editor Panel */}
            <Panel 
              defaultSize={showCitationPanel ? (showPdfViewer ? 40 : 60) : 100}
              minSize={30}
              className="overflow-hidden"
            >
              <Editor
                documentId={document.id}
                initialContent={document.content || undefined}
                onSave={handleSave}
                autoSaveDelay={2000}
                userId="test-user"
                citationConfig={citationConfig}
                onCitationSuggestionsUpdate={setCitationSuggestions}
                onCitationConnectionChange={setCitationConnectionStatus}
                onRegisterCitationInsert={(handler) => {
                  insertCitationRef.current = handler;
                }}
                onEditorReady={(saveFunction) => {
                  editorSaveRef.current = saveFunction;
                }}
                onCitationInserted={handleCitationInserted}
              />
            </Panel>
            
            {showCitationPanel && (
              <>
                <PanelResizeHandle className="w-2 bg-gray-200 hover:bg-gray-300 cursor-col-resize" />
                
                {/* Citations Panel */}
                <Panel 
                  defaultSize={showPdfViewer ? 20 : 40}
                  minSize={20}
                  className="bg-gray-50 overflow-hidden relative"
                >
                  {/* Floating Citation Settings */}
                  {showCitationSettings && (
                    <div className="absolute top-4 right-4 z-10 shadow-lg rounded-lg">
                      <CitationSettings 
                        config={citationConfig}
                        onConfigChange={(newConfig) => {
                          setCitationConfig(prev => ({ ...prev, ...newConfig }));
                        }}
                      />
                    </div>
                  )}
                  <CitationPanel 
                    documentId={document.id} 
                    suggestions={citationSuggestions}
                    isConnected={citationConnectionStatus}
                    onInsertCitation={(citation) => {
                      if (insertCitationRef.current) {
                        insertCitationRef.current(citation);
                      }
                    }}
                    onAddToLibrary={handleAddToLibrary}
                    bibliographyPaperIds={bibliographyPaperIds}
                    citedPaperIds={citedPaperIds}
                    onViewDetails={handleViewPaperDetails}
                    selectedPaperId={selectedPaper?.paperId}
                  />
                </Panel>
              </>
            )}
            
            {showPdfViewer && showCitationPanel && (
              <>
                <PanelResizeHandle className="w-2 bg-gray-200 hover:bg-gray-300 cursor-col-resize" />
                
                {/* PDF Viewer Panel */}
                <Panel 
                  defaultSize={40}
                  minSize={30}
                  className="overflow-hidden"
                >
                  <PdfViewer
                    paper={selectedPaper}
                    onClose={handleClosePdfViewer}
                  />
                </Panel>
              </>
            )}
          </PanelGroup>
        </div>
        
        {/* Bibliography tab */}
        <div className={`h-full overflow-y-auto bg-white p-6 ${activeTab === 'bibliography' ? '' : 'hidden'}`}>
          <DocumentPapers
            key={bibliographyKey}
            documentId={document.id}
            documentTitle={document.title}
          />
        </div>
        
        {/* Citations tab */}
        <div className={`h-full bg-gray-50 overflow-y-auto ${activeTab === 'citations' ? '' : 'hidden'}`}>
            {/* Inserted Citations Section */}
            {insertedCitations.length > 0 && (
              <div className="p-6 bg-white border-b">
                <h3 className="text-lg font-semibold mb-4">Citations in Document</h3>
                <div className="space-y-3">
                  {insertedCitations.map((citation, index) => (
                    <div key={`${citation.paperId}-${index}`} className="p-3 bg-gray-50 rounded-lg">
                      <div className="font-medium text-gray-900">{citation.title}</div>
                      <div className="text-sm text-gray-600 mt-1">
                        {citation.authors?.join(', ')} {citation.year && `(${citation.year})`}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Added to bibliography ✓
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Citation Settings */}
            <div className="mb-4">
              <CitationSettings 
                config={citationConfig}
                onConfigChange={(newConfig) => {
                  setCitationConfig(prev => ({ ...prev, ...newConfig }));
                }}
              />
            </div>
            
            {/* Suggestions Section */}
            <CitationPanel 
              documentId={document.id} 
              suggestions={citationSuggestions}
              isConnected={citationConnectionStatus}
              onInsertCitation={(citation) => {
                if (insertCitationRef.current) {
                  insertCitationRef.current(citation);
                  // Switch back to editor tab after inserting
                  setActiveTab('editor');
                }
              }}
              onAddToLibrary={handleAddToLibrary}
              bibliographyPaperIds={bibliographyPaperIds}
              citedPaperIds={citedPaperIds}
              onViewDetails={(paper) => {
                handleViewPaperDetails(paper);
                // Switch to editor tab to show PDF viewer
                setActiveTab('editor');
              }}
              selectedPaperId={selectedPaper?.paperId}
            />
        </div>
      </div>

      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        documentTitle={document.title}
        documentId={document.id}
        editorState={editorStateRef.current}
      />
      
      {/* Paper Upload Modal */}
      <PaperUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadComplete={() => {
          // Papers have been uploaded successfully
          console.log('Papers uploaded successfully');
        }}
      />
    </div>
  );
};

export default DocumentEditor;