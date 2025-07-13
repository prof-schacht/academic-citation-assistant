import React, { useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  FORMAT_ELEMENT_COMMAND,
  UNDO_COMMAND,
  REDO_COMMAND,
} from 'lexical';
import { $createHeadingNode } from '@lexical/rich-text';
import { INSERT_ORDERED_LIST_COMMAND, INSERT_UNORDERED_LIST_COMMAND } from '@lexical/list';
import { $setBlocksType } from '@lexical/selection';

const Toolbar: React.FC = () => {
  const [editor] = useLexicalComposerContext();

  const formatText = useCallback(
    (format: 'bold' | 'italic' | 'underline') => {
      editor.dispatchCommand(FORMAT_TEXT_COMMAND, format);
    },
    [editor]
  );

  const formatHeading = useCallback(
    (headingSize: 'h1' | 'h2' | 'h3') => {
      editor.update(() => {
        const selection = $getSelection();
        if ($isRangeSelection(selection)) {
          $setBlocksType(selection, () => $createHeadingNode(headingSize));
        }
      });
    },
    [editor]
  );

  const formatAlign = useCallback(
    (align: 'left' | 'center' | 'right' | 'justify') => {
      editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, align);
    },
    [editor]
  );

  return (
    <div className="border-b border-gray-200 p-2 flex items-center space-x-2 bg-white sticky top-0 z-10">
      {/* Undo/Redo */}
      <button
        onClick={() => editor.dispatchCommand(UNDO_COMMAND, undefined)}
        className="p-2 hover:bg-gray-100 rounded"
        title="Undo"
      >
        ↶
      </button>
      <button
        onClick={() => editor.dispatchCommand(REDO_COMMAND, undefined)}
        className="p-2 hover:bg-gray-100 rounded"
        title="Redo"
      >
        ↷
      </button>

      <div className="w-px h-6 bg-gray-300" />

      {/* Headings */}
      <select
        onChange={(e) => {
          const value = e.target.value;
          if (value === 'paragraph') {
            // TODO: Format as paragraph
          } else {
            formatHeading(value as 'h1' | 'h2' | 'h3');
          }
        }}
        className="px-2 py-1 border border-gray-300 rounded"
      >
        <option value="paragraph">Normal</option>
        <option value="h1">Heading 1</option>
        <option value="h2">Heading 2</option>
        <option value="h3">Heading 3</option>
      </select>

      <div className="w-px h-6 bg-gray-300" />

      {/* Text formatting */}
      <button
        onClick={() => formatText('bold')}
        className="p-2 hover:bg-gray-100 rounded font-bold"
        title="Bold"
      >
        B
      </button>
      <button
        onClick={() => formatText('italic')}
        className="p-2 hover:bg-gray-100 rounded italic"
        title="Italic"
      >
        I
      </button>
      <button
        onClick={() => formatText('underline')}
        className="p-2 hover:bg-gray-100 rounded underline"
        title="Underline"
      >
        U
      </button>

      <div className="w-px h-6 bg-gray-300" />

      {/* Lists */}
      <button
        onClick={() => editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined)}
        className="p-2 hover:bg-gray-100 rounded"
        title="Bullet List"
      >
        • List
      </button>
      <button
        onClick={() => editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined)}
        className="p-2 hover:bg-gray-100 rounded"
        title="Numbered List"
      >
        1. List
      </button>

      <div className="w-px h-6 bg-gray-300" />

      {/* Alignment */}
      <button
        onClick={() => formatAlign('left')}
        className="p-2 hover:bg-gray-100 rounded"
        title="Align Left"
      >
        ⬅
      </button>
      <button
        onClick={() => formatAlign('center')}
        className="p-2 hover:bg-gray-100 rounded"
        title="Align Center"
      >
        ⬌
      </button>
      <button
        onClick={() => formatAlign('right')}
        className="p-2 hover:bg-gray-100 rounded"
        title="Align Right"
      >
        ➡
      </button>
    </div>
  );
};

export default Toolbar;