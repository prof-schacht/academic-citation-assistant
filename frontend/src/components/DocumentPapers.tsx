import React, { useState, useEffect } from 'react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { documentPaperService, DocumentPaper } from '../services/documentPaperService';
import AssignPaperDialog from './AssignPaperDialog';

interface DocumentPapersProps {
  documentId: string;
  documentTitle: string;
}

interface SortablePaperItemProps {
  paper: DocumentPaper;
  onUpdateNotes: (paperId: string, notes: string) => void;
  onRemove: (paperId: string) => void;
}

const SortablePaperItem: React.FC<SortablePaperItemProps> = ({ paper, onUpdateNotes, onRemove }) => {
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notes, setNotes] = useState(paper.notes || '');
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: paper.paper_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleSaveNotes = () => {
    onUpdateNotes(paper.paper_id, notes);
    setIsEditingNotes(false);
  };

  const formatAuthors = (authors?: string[]) => {
    if (!authors || authors.length === 0) return '';
    if (authors.length === 1) return authors[0];
    if (authors.length === 2) return authors.join(' & ');
    return `${authors[0]} et al.`;
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white border rounded-lg p-4 mb-3"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center mb-2">
            <div
              {...attributes}
              {...listeners}
              className="cursor-move mr-3 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">{paper.paper.title}</h4>
              <p className="text-sm text-gray-600">
                {formatAuthors(paper.paper.authors)}
                {paper.paper.year && ` (${paper.paper.year})`}
                {paper.paper.journal && ` • ${paper.paper.journal}`}
              </p>
            </div>
          </div>
          
          {isEditingNotes ? (
            <div className="ml-8 mt-2">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes about this paper..."
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
              />
              <div className="mt-2 flex space-x-2">
                <button
                  onClick={handleSaveNotes}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setNotes(paper.notes || '');
                    setIsEditingNotes(false);
                  }}
                  className="px-3 py-1 text-gray-600 hover:text-gray-800 text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="ml-8">
              {paper.notes ? (
                <p className="text-sm text-gray-600 italic mt-1">{paper.notes}</p>
              ) : null}
              <button
                onClick={() => setIsEditingNotes(true)}
                className="text-sm text-blue-600 hover:text-blue-700 mt-1"
              >
                {paper.notes ? 'Edit notes' : 'Add notes'}
              </button>
            </div>
          )}
        </div>
        
        <button
          onClick={() => onRemove(paper.paper_id)}
          className="ml-4 text-red-600 hover:text-red-700"
          title="Remove from bibliography"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
};

const DocumentPapers: React.FC<DocumentPapersProps> = ({ documentId, documentTitle }) => {
  const [papers, setPapers] = useState<DocumentPaper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    loadPapers();
  }, [documentId]);

  const loadPapers = async () => {
    setIsLoading(true);
    try {
      const documentPapers = await documentPaperService.getDocumentPapers(documentId);
      setPapers(documentPapers);
    } catch (error) {
      console.error('Failed to load document papers:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = papers.findIndex(p => p.paper_id === active.id);
      const newIndex = papers.findIndex(p => p.paper_id === over.id);
      
      const newOrder = arrayMove(papers, oldIndex, newIndex);
      setPapers(newOrder);
      
      // Update positions on backend
      try {
        await documentPaperService.reorderPapers(
          documentId,
          newOrder.map(p => p.paper_id)
        );
      } catch (error) {
        console.error('Failed to reorder papers:', error);
        // Revert on error
        loadPapers();
      }
    }
  };

  const handleUpdateNotes = async (paperId: string, notes: string) => {
    try {
      await documentPaperService.updateAssignment(documentId, paperId, { notes });
      // Update local state
      setPapers(papers.map(p => 
        p.paper_id === paperId ? { ...p, notes } : p
      ));
    } catch (error) {
      console.error('Failed to update notes:', error);
    }
  };

  const handleRemovePaper = async (paperId: string) => {
    if (!confirm('Remove this paper from the bibliography?')) return;
    
    try {
      await documentPaperService.removePaper(documentId, paperId);
      setPapers(papers.filter(p => p.paper_id !== paperId));
    } catch (error) {
      console.error('Failed to remove paper:', error);
    }
  };

  const handleExportBibTeX = async () => {
    setIsExporting(true);
    try {
      const bibtex = await documentPaperService.exportBibTeX(documentId);
      documentPaperService.downloadFile(bibtex, `${documentTitle}_bibliography.bib`, 'application/x-bibtex');
    } catch (error) {
      console.error('Failed to export BibTeX:', error);
      alert('Failed to export BibTeX');
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportLaTeX = async () => {
    setIsExporting(true);
    try {
      const latex = await documentPaperService.exportLaTeX(documentId);
      documentPaperService.downloadFile(latex, `${documentTitle}.tex`, 'application/x-tex');
    } catch (error) {
      console.error('Failed to export LaTeX:', error);
      alert('Failed to export LaTeX');
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Loading bibliography...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">
          Bibliography ({papers.length} papers)
        </h3>
        <div className="flex space-x-3">
          <button
            onClick={handleExportBibTeX}
            disabled={papers.length === 0 || isExporting}
            className="px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Export BibTeX
          </button>
          <button
            onClick={handleExportLaTeX}
            disabled={isExporting}
            className="px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Export LaTeX
          </button>
          <button
            onClick={() => setShowAssignDialog(true)}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            + Add Papers
          </button>
        </div>
      </div>

      {papers.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600 mb-4">No papers assigned to this document yet</p>
          <button
            onClick={() => setShowAssignDialog(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Papers to Bibliography
          </button>
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={papers.map(p => p.paper_id)}
            strategy={verticalListSortingStrategy}
          >
            {papers.map(paper => (
              <SortablePaperItem
                key={paper.paper_id}
                paper={paper}
                onUpdateNotes={handleUpdateNotes}
                onRemove={handleRemovePaper}
              />
            ))}
          </SortableContext>
        </DndContext>
      )}

      <AssignPaperDialog
        documentId={documentId}
        documentTitle={documentTitle}
        isOpen={showAssignDialog}
        onClose={() => setShowAssignDialog(false)}
        onAssigned={loadPapers}
        excludePaperIds={papers.map(p => p.paper_id)}
      />
    </div>
  );
};

export default DocumentPapers;