import React, { useEffect, useCallback, useRef, useState } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { ListPlugin } from '@lexical/react/LexicalListPlugin';
import { LinkPlugin } from '@lexical/react/LexicalLinkPlugin';
// import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { TabIndentationPlugin } from '@lexical/react/LexicalTabIndentationPlugin';
import { AutoFocusPlugin } from '@lexical/react/LexicalAutoFocusPlugin';
import { TablePlugin } from '@lexical/react/LexicalTablePlugin';
// import LexicalErrorBoundary from '@lexical/react/LexicalErrorBoundary';
import { $getRoot } from 'lexical';
import type { EditorState } from 'lexical';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

import editorConfig from './EditorConfig';
import Toolbar from './Toolbar';
import StatusBar from './StatusBar';
import WordCountPlugin from './plugins/WordCountPlugin';
import KeyboardShortcutsPlugin from './plugins/KeyboardShortcutsPlugin';
import { CitationSuggestionPlugin } from './plugins/CitationSuggestionPlugin';
import { CitationInsertPlugin } from './plugins/CitationInsertPlugin';
import { documentService } from '../../services/documentService';
import { debounce } from 'lodash';
import type { CitationSuggestion } from '../../services/websocketService';

interface EditorProps {
  documentId?: string;
  initialContent?: any;
  onSave?: (content: any, editorState?: EditorState) => void;
  autoSaveDelay?: number;
  userId?: string;
  onCitationSuggestionsUpdate?: (suggestions: CitationSuggestion[]) => void;
  onCitationConnectionChange?: (connected: boolean) => void;
  onRegisterCitationInsert?: (handler: (citation: CitationSuggestion) => void) => void;
}

// Plugin to load initial content
function LoadInitialContentPlugin({ content }: { content?: any }) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (!content) {
      return;
    }
    
    editor.update(() => {
      try {
        let editorStateConfig;
        
        if (typeof content === 'string') {
          try {
            editorStateConfig = JSON.parse(content);
          } catch {
            // If it's not valid JSON, treat it as plain text
            const root = $getRoot();
            root.clear();
            return;
          }
        } else {
          editorStateConfig = content;
        }
        
        // Only parse if we have valid content
        if (editorStateConfig && editorStateConfig.root) {
          const parsedState = editor.parseEditorState(editorStateConfig);
          editor.setEditorState(parsedState);
        }
      } catch (e) {
        console.error('Failed to load initial content:', e);
        // If parsing fails, start with empty editor
        const root = $getRoot();
        root.clear();
      }
    });
  }, [content, editor]);

  return null;
}

// Simple error boundary component
function LexicalErrorBoundaryComponent({ children, onError }: { children: React.ReactNode; onError: (error: Error) => void }) {
  return <>{children}</>;
}

const Editor: React.FC<EditorProps> = ({
  documentId,
  initialContent,
  onSave,
  autoSaveDelay = 2000,
  userId = 'default-user',
  onCitationSuggestionsUpdate,
  onCitationConnectionChange,
  onRegisterCitationInsert,
}) => {
  // const [isLoading, setIsLoading] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [hasContentChanged, setHasContentChanged] = useState(false);
  const [isNewDocument] = useState(!initialContent);
  const [wordCount, setWordCount] = useState(0);
  const [characterCount, setCharacterCount] = useState(0);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Create debounced save function
  const debouncedSave = useCallback(
    debounce(async (editorState: EditorState) => {
      if (!documentId) return;

      setIsSaving(true);
      try {
        const content = editorState.toJSON();
        await documentService.update(documentId, { content });
        setLastSaved(new Date());
        
        if (onSave) {
          onSave(content, editorState);
        }
      } catch (error) {
        console.error('Failed to auto-save:', error);
      } finally {
        setIsSaving(false);
      }
    }, autoSaveDelay),
    [documentId, onSave, autoSaveDelay]
  );

  const handleChange = useCallback((editorState: EditorState) => {
    // Only start auto-saving after the user has made changes
    if (!hasContentChanged) {
      setHasContentChanged(true);
    }
    
    // Only auto-save if we have a document ID and content has been changed
    if (documentId && hasContentChanged) {
      debouncedSave(editorState);
    }
  }, [documentId, hasContentChanged, debouncedSave]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      debouncedSave.cancel();
    };
  }, [debouncedSave]);

  return (
    <div className="h-full flex flex-col bg-white">
      <LexicalComposer initialConfig={editorConfig}>
        <div className="flex-1 flex flex-col">
          <Toolbar />
          
          <div className="flex-1 relative">
            <RichTextPlugin
              contentEditable={
                <ContentEditable className="min-h-[500px] p-8 focus:outline-none prose max-w-none" />
              }
              placeholder={
                <div className="absolute top-8 left-8 text-gray-400 pointer-events-none">
                  Start writing...
                </div>
              }
              ErrorBoundary={LexicalErrorBoundaryComponent}
            />
            <OnChangePlugin onChange={handleChange} />
            <HistoryPlugin />
            <ListPlugin />
            <LinkPlugin />
            <TablePlugin />
            {/* <MarkdownShortcutPlugin /> */}
            <TabIndentationPlugin />
            <AutoFocusPlugin />
            <LoadInitialContentPlugin content={initialContent} />
            <WordCountPlugin 
              onWordCountChange={(words, chars) => {
                setWordCount(words);
                setCharacterCount(chars);
              }} 
            />
            <KeyboardShortcutsPlugin 
              onSave={() => {
                // Trigger manual save
                if (documentId) {
                  debouncedSave.flush();
                }
              }}
            />
            {onCitationSuggestionsUpdate && (
              <CitationSuggestionPlugin
                userId={userId}
                onSuggestionsUpdate={onCitationSuggestionsUpdate}
                onConnectionChange={onCitationConnectionChange}
              />
            )}
            {onRegisterCitationInsert && (
              <CitationInsertPlugin
                onRegisterInsertHandler={onRegisterCitationInsert}
              />
            )}
          </div>

          {/* Status bar */}
          <StatusBar
            wordCount={wordCount}
            characterCount={characterCount}
            lastSaved={lastSaved}
            isSaving={isSaving}
          />
        </div>
      </LexicalComposer>
    </div>
  );
};

export default Editor;