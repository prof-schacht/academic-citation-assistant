import type { InitialConfigType } from '@lexical/react/LexicalComposer';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { HorizontalRuleNode } from '@lexical/react/LexicalHorizontalRuleNode';
import { ListItemNode, ListNode } from '@lexical/list';
import { CodeNode } from '@lexical/code';
import { AutoLinkNode, LinkNode } from '@lexical/link';
import { TableNode, TableCellNode, TableRowNode } from '@lexical/table';

const theme = {
  paragraph: 'mb-4',
  heading: {
    h1: 'text-3xl font-bold mb-6',
    h2: 'text-2xl font-bold mb-4',
    h3: 'text-xl font-bold mb-3',
  },
  list: {
    ul: 'list-disc list-inside mb-4',
    ol: 'list-decimal list-inside mb-4',
    listitem: 'ml-6',
  },
  quote: 'border-l-4 border-gray-300 pl-4 italic my-4',
  code: 'bg-gray-100 rounded px-1 py-0.5 font-mono text-sm',
  link: 'text-blue-600 hover:text-blue-800 underline',
  text: {
    bold: 'font-bold',
    italic: 'italic',
    underline: 'underline',
    strikethrough: 'line-through',
    subscript: 'subscript',
    superscript: 'superscript',
  },
};

const editorConfig: InitialConfigType = {
  namespace: 'CitationEditor',
  theme,
  onError: (error: Error) => {
    console.error('Lexical error:', error);
  },
  nodes: [
    HeadingNode,
    QuoteNode,
    ListNode,
    ListItemNode,
    CodeNode,
    AutoLinkNode,
    LinkNode,
    TableNode,
    TableCellNode,
    TableRowNode,
    HorizontalRuleNode,
  ],
};

export default editorConfig;