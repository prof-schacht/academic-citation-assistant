import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  COMMAND_PRIORITY_HIGH,
  KEY_MODIFIER_COMMAND,
  $getSelection,
  $isRangeSelection,
} from 'lexical';
import { $createLinkNode } from '@lexical/link';
import { INSERT_ORDERED_LIST_COMMAND, INSERT_UNORDERED_LIST_COMMAND } from '@lexical/list';

interface KeyboardShortcutsPluginProps {
  onSave?: () => void;
  onToggleCitationPanel?: () => void;
}

export default function KeyboardShortcutsPlugin({ 
  onSave, 
  onToggleCitationPanel 
}: KeyboardShortcutsPluginProps) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const removeListener = editor.registerCommand(
      KEY_MODIFIER_COMMAND,
      (payload) => {
        const event = payload as KeyboardEvent;
        
        // Ctrl/Cmd + S: Save
        if (event.key === 's') {
          event.preventDefault();
          onSave?.();
          return true;
        }
        
        // Ctrl/Cmd + K: Insert link
        if (event.key === 'k') {
          event.preventDefault();
          editor.update(() => {
            const selection = $getSelection();
            if ($isRangeSelection(selection)) {
              const url = prompt('Enter URL:');
              if (url) {
                const linkNode = $createLinkNode(url);
                selection.insertNodes([linkNode]);
              }
            }
          });
          return true;
        }
        
        // Ctrl/Cmd + Shift + 7: Ordered list
        if (event.key === '7' && event.shiftKey) {
          event.preventDefault();
          editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
          return true;
        }
        
        // Ctrl/Cmd + Shift + 8: Unordered list
        if (event.key === '8' && event.shiftKey) {
          event.preventDefault();
          editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
          return true;
        }
        
        return false;
      },
      COMMAND_PRIORITY_HIGH
    );

    // Escape key handler
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onToggleCitationPanel?.();
      }
    };

    window.addEventListener('keydown', handleEscape);

    return () => {
      removeListener();
      window.removeEventListener('keydown', handleEscape);
    };
  }, [editor, onSave, onToggleCitationPanel]);

  return null;
}