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
import { SelectionCitationPlugin } from './plugins/SelectionCitationPlugin';
import { documentService } from '../../services/documentService';
import { debounce } from 'lodash';
import type { CitationSuggestion, CitationWebSocketClient, CitationConfig } from '../../services/websocketService';

interface EditorProps {
  documentId?: string;
  initialContent?: any;
  onSave?: (content: any, editorState?: EditorState) => void;
  autoSaveDelay?: number;
  userId?: string;
  citationConfig?: CitationConfig;
  onCitationSuggestionsUpdate?: (suggestions: CitationSuggestion[]) => void;
  onCitationConnectionChange?: (connected: boolean) => void;
  onRegisterCitationInsert?: (handler: (citation: CitationSuggestion) => void) => void;
  onEditorReady?: (saveFunction: () => void) => void;
  onCitationInserted?: (citation: CitationSuggestion) => void;
}

// Plugin to load initial content
function LoadInitialContentPlugin({ content }: { content?: any }) {
  const [editor] = useLexicalComposerContext();
  const [hasLoadedInitialContent, setHasLoadedInitialContent] = useState(false);
  const contentRef = useRef<any>(null);

  useEffect(() => {
    // Check if content has actually changed (not just the reference)
    const contentChanged = JSON.stringify(content) !== JSON.stringify(contentRef.current);
    
    if (!content || (!contentChanged && hasLoadedInitialContent)) {
      return;
    }
    
    console.log('[LoadInitialContentPlugin] Loading content, contentChanged:', contentChanged);
    contentRef.current = content;
    
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
          setHasLoadedInitialContent(true);
        }
      } catch (e) {
        console.error('Failed to load initial content:', e);
        // If parsing fails, start with empty editor
        const root = $getRoot();
        root.clear();
      }
    });
  }, [content, editor, hasLoadedInitialContent]);

  return null;
}

// Simple error boundary component
function LexicalErrorBoundaryComponent({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

const Editor: React.FC<EditorProps> = ({
  documentId,
  initialContent,
  onSave,
  autoSaveDelay = 2000,
  userId = 'default-user',
  citationConfig,
  onCitationSuggestionsUpdate,
  onCitationConnectionChange,
  onRegisterCitationInsert,
  onEditorReady,
  onCitationInserted,
}) => {
  // const [isLoading, setIsLoading] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [hasContentChanged, setHasContentChanged] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [characterCount, setCharacterCount] = useState(0);
  const wsClientRef = useRef<CitationWebSocketClient | null>(null);
  const currentEditorStateRef = useRef<EditorState | null>(null);

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
    console.log('[Editor] onChange triggered, hasContentChanged:', hasContentChanged);
    
    // Store current editor state
    currentEditorStateRef.current = editorState;
    
    // Mark that content has changed
    if (!hasContentChanged) {
      setHasContentChanged(true);
    }
    
    // Auto-save if we have a document ID
    // Remove the hasContentChanged check to ensure saves happen from the first change
    if (documentId) {
      console.log('[Editor] Triggering auto-save');
      debouncedSave(editorState);
    }
  }, [documentId, hasContentChanged, debouncedSave]);

  // Create immediate save function
  const saveImmediately = useCallback(async () => {
    console.log('[Editor] Immediate save requested');
    if (!documentId || !currentEditorStateRef.current) {
      console.log('[Editor] Cannot save - no documentId or editorState');
      return;
    }

    setIsSaving(true);
    try {
      const content = currentEditorStateRef.current.toJSON();
      console.log('[Editor] Saving content immediately');
      await documentService.update(documentId, { content });
      setLastSaved(new Date());
      
      if (onSave) {
        onSave(content, currentEditorStateRef.current);
      }
      console.log('[Editor] Immediate save completed');
    } catch (error) {
      console.error('Failed to save immediately:', error);
    } finally {
      setIsSaving(false);
    }
  }, [documentId, onSave]);

  // Expose save function to parent
  useEffect(() => {
    if (onEditorReady) {
      onEditorReady(() => {
        console.log('[Editor] Manual save triggered');
        // First try immediate save if we have content
        if (currentEditorStateRef.current) {
          saveImmediately();
        } else {
          // Fallback to flush
          debouncedSave.flush();
        }
      });
    }
  }, [onEditorReady, debouncedSave, saveImmediately]);

  // Save on unmount instead of canceling
  useEffect(() => {
    return () => {
      // Flush any pending saves when component unmounts
      debouncedSave.flush();
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
                <ContentEditable className="lexical-editor min-h-[500px] p-8 focus:outline-none prose max-w-none" />
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
              <>
                <CitationSuggestionPlugin
                  userId={userId}
                  citationConfig={citationConfig}
                  onSuggestionsUpdate={onCitationSuggestionsUpdate}
                  onConnectionChange={onCitationConnectionChange}
                  onWsClientReady={(client) => {
                    wsClientRef.current = client;
                  }}
                />
                <SelectionCitationPlugin
                  wsClient={wsClientRef.current}
                  onSelectionChange={(text) => {
                    console.log('[Editor] Text selected for citation search:', text);
                  }}
                />
              </>
            )}
            {onRegisterCitationInsert && (
              <CitationInsertPlugin
                onRegisterInsertHandler={onRegisterCitationInsert}
                onCitationInserted={onCitationInserted}
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