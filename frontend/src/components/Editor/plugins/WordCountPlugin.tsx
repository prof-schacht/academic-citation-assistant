import { useEffect, useState } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot, $isTextNode } from 'lexical';

interface WordCountPluginProps {
  onWordCountChange: (wordCount: number, charCount: number) => void;
}

export default function WordCountPlugin({ onWordCountChange }: WordCountPluginProps) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const updateWordCount = () => {
      editor.getEditorState().read(() => {
        const root = $getRoot();
        let wordCount = 0;
        let charCount = 0;

        const textContent = root.getTextContent();
        charCount = textContent.length;
        
        // Count words (simple implementation)
        const words = textContent.trim().split(/\s+/);
        wordCount = textContent.trim() === '' ? 0 : words.length;

        onWordCountChange(wordCount, charCount);
      });
    };

    // Initial count
    updateWordCount();

    // Listen for changes
    const removeListener = editor.registerUpdateListener(() => {
      updateWordCount();
    });

    return () => {
      removeListener();
    };
  }, [editor, onWordCountChange]);

  return null;
}