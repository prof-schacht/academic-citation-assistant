/**
 * Custom Lexical node for citations with LaTeX-style citation keys
 */

import {
  $applyNodeReplacement,
  DecoratorNode,
} from 'lexical';
import type {
  EditorConfig,
  LexicalNode,
  NodeKey,
  SerializedLexicalNode,
  Spread,
} from 'lexical';
import React, { Suspense } from 'react';
import type { CitationSuggestion } from '../../../types';

export type SerializedCitationNode = Spread<
  {
    citationKey: string;
    paperId: string;
    title: string;
    authors: string[];
    year?: number;
    type: 'citation';
    version: 1;
  },
  SerializedLexicalNode
>;

export class CitationNode extends DecoratorNode<React.JSX.Element> {
  __citationKey: string;
  __paperId: string;
  __title: string;
  __authors: string[];
  __year?: number;

  static getType(): string {
    return 'citation';
  }

  static clone(node: CitationNode): CitationNode {
    return new CitationNode(
      node.__citationKey,
      node.__paperId,
      node.__title,
      node.__authors,
      node.__year,
      node.__key
    );
  }

  constructor(
    citationKey: string,
    paperId: string,
    title: string,
    authors: string[],
    year?: number,
    key?: NodeKey
  ) {
    super(key);
    this.__citationKey = citationKey;
    this.__paperId = paperId;
    this.__title = title;
    this.__authors = authors;
    this.__year = year;
  }

  static importJSON(serializedNode: SerializedCitationNode): CitationNode {
    const { citationKey, paperId, title, authors, year } = serializedNode;
    return $createCitationNode(citationKey, paperId, title, authors, year);
  }

  exportJSON(): SerializedCitationNode {
    return {
      citationKey: this.__citationKey,
      paperId: this.__paperId,
      title: this.__title,
      authors: this.__authors,
      year: this.__year,
      type: 'citation',
      version: 1,
    };
  }

  createDOM(_config: EditorConfig): HTMLElement {
    const span = document.createElement('span');
    span.className = 'citation-node';
    return span;
  }

  updateDOM(): false {
    return false;
  }

  getCitationKey(): string {
    return this.__citationKey;
  }

  setCitationKey(citationKey: string): void {
    const writable = this.getWritable();
    writable.__citationKey = citationKey;
  }

  getCitationData(): CitationSuggestion {
    return {
      paperId: this.__paperId,
      title: this.__title,
      authors: this.__authors,
      year: this.__year || new Date().getFullYear(),
      abstract: '',
      confidence: 1.0,
      citationStyle: 'inline',
      displayText: `\\cite{${this.__citationKey}}`,
    };
  }

  getTextContent(): string {
    // Return LaTeX citation format for export
    return `\\cite{${this.__citationKey}}`;
  }

  decorate(): React.JSX.Element {
    return (
      <Suspense fallback={null}>
        <CitationComponent
          citationKey={this.__citationKey}
          paperId={this.__paperId}
          title={this.__title}
          authors={this.__authors}
          year={this.__year}
        />
      </Suspense>
    );
  }
}

export function $createCitationNode(
  citationKey: string,
  paperId: string,
  title: string,
  authors: string[],
  year?: number
): CitationNode {
  return $applyNodeReplacement(
    new CitationNode(citationKey, paperId, title, authors, year)
  );
}

export function $isCitationNode(
  node: LexicalNode | null | undefined
): node is CitationNode {
  return node instanceof CitationNode;
}

// Component for rendering the citation
interface CitationComponentProps {
  citationKey: string;
  paperId: string;
  title: string;
  authors: string[];
  year?: number;
}

function CitationComponent({
  citationKey,
  title,
  authors,
  year,
}: CitationComponentProps) {
  // Format author display for tooltip
  const formatAuthors = () => {
    if (!authors || authors.length === 0) return 'Unknown';
    if (authors.length === 1) return authors[0];
    if (authors.length === 2) return `${authors[0]} & ${authors[1]}`;
    return `${authors[0]} et al.`;
  };

  return (
    <span
      className="inline-flex items-center mx-0.5 group relative"
      contentEditable={false}
      data-lexical-decorator="true"
    >
      {/* Citation icon */}
      <span className="inline-flex items-center px-1 py-0.5 rounded text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 cursor-help">
        <svg
          className="w-3 h-3 mr-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span className="font-mono text-xs">{citationKey}</span>
      </span>

      {/* Tooltip */}
      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50">
        <div className="bg-gray-900 text-white text-sm rounded-lg px-3 py-2 max-w-xs">
          <div className="font-semibold">{title}</div>
          <div className="text-gray-300 text-xs mt-1">
            {formatAuthors()} {year ? `(${year})` : ''}
          </div>
          <div className="absolute top-full left-4 transform -translate-x-1/2">
            <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      </div>

      {/* Hidden LaTeX citation for copy/export */}
      <span className="sr-only">{`\\cite{${citationKey}}`}</span>
    </span>
  );
}