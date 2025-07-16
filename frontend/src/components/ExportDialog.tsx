import React, { useState } from 'react';
import type { EditorState } from 'lexical';
import { exportDocument, downloadFile } from '../utils/exportDocument';
import { documentPaperService } from '../services/documentPaperService';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  documentTitle: string;
  documentId?: string;
  editorState: EditorState | null;
}

const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  documentTitle,
  documentId,
  editorState,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  
  if (!isOpen) return null;

  const handleExport = async (format: 'markdown' | 'html' | 'txt' | 'json' | 'bibtex' | 'latex') => {
    setIsExporting(true);
    try {
      if (format === 'bibtex') {
        if (!documentId) {
          alert('Please save the document before exporting BibTeX');
          return;
        }
        const bibtex = await documentPaperService.exportBibTeX(documentId);
        documentPaperService.downloadFile(bibtex, `${documentTitle}_bibliography.bib`, 'application/x-bibtex');
      } else if (format === 'latex') {
        if (!documentId) {
          alert('Please save the document before exporting LaTeX');
          return;
        }
        const latex = await documentPaperService.exportLaTeX(documentId);
        documentPaperService.downloadFile(latex, `${documentTitle}.tex`, 'application/x-tex');
      } else {
        if (!editorState) return;
        const blob = await exportDocument(editorState, {
          title: documentTitle,
          format,
        });
        
        const extension = format === 'markdown' ? 'md' : format;
        downloadFile(blob, `${documentTitle}.${extension}`);
      }
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const exportFormats = [
    {
      format: 'markdown' as const,
      name: 'Markdown',
      description: 'Compatible with GitHub, Obsidian, and most editors',
      icon: '📝',
    },
    {
      format: 'html' as const,
      name: 'HTML',
      description: 'Web-ready format with styling',
      icon: '🌐',
    },
    {
      format: 'txt' as const,
      name: 'Plain Text',
      description: 'Simple text without formatting',
      icon: '📄',
    },
    {
      format: 'latex' as const,
      name: 'LaTeX',
      description: 'Professional typesetting for academic papers',
      icon: '📐',
    },
    {
      format: 'bibtex' as const,
      name: 'BibTeX',
      description: 'Bibliography for LaTeX documents',
      icon: '📚',
    },
    {
      format: 'json' as const,
      name: 'JSON',
      description: 'Raw editor data for re-import',
      icon: '🔧',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Export Document</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isExporting}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-3">
          {exportFormats.map(({ format, name, description, icon }) => (
            <button
              key={format}
              onClick={() => handleExport(format)}
              disabled={isExporting}
              className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex items-start space-x-3">
                <span className="text-2xl">{icon}</span>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{name}</h3>
                  <p className="text-sm text-gray-500">{description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

      </div>
    </div>
  );
};

export default ExportDialog;