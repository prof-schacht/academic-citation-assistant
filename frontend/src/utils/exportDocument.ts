import { $generateHtmlFromNodes } from '@lexical/html';
import type { EditorState } from 'lexical';

export interface ExportOptions {
  title: string;
  format: 'markdown' | 'html' | 'txt' | 'json';
}

export async function exportDocument(
  editorState: EditorState,
  options: ExportOptions
): Promise<Blob> {
  let content = '';
  let mimeType = '';

  switch (options.format) {
    case 'markdown': {
      // Convert to markdown
      content = await convertToMarkdown(editorState, options.title);
      mimeType = 'text/markdown';
      // filename = `${options.title}.md`;
      break;
    }
    
    case 'html': {
      // Convert to HTML
      content = await convertToHtml(editorState, options.title);
      mimeType = 'text/html';
      // filename = `${options.title}.html`;
      break;
    }
    
    case 'txt': {
      // Plain text
      content = editorState.read(() => {
        const root = editorState._nodeMap.get('root');
        const text = root?.getTextContent() || '';
        return `${options.title}\n${'='.repeat(options.title.length)}\n\n${text}`;
      });
      mimeType = 'text/plain';
      // filename = `${options.title}.txt`;
      break;
    }
    
    case 'json': {
      // Lexical JSON format
      content = JSON.stringify({
        title: options.title,
        content: editorState.toJSON(),
        exportDate: new Date().toISOString(),
      }, null, 2);
      mimeType = 'application/json';
      // filename = `${options.title}.json`;
      break;
    }
  }

  return new Blob([content], { type: mimeType });
}

async function convertToMarkdown(editorState: EditorState, title: string): Promise<string> {
  return editorState.read(() => {
    let markdown = `# ${title}\n\n`;
    
    // Simple conversion - this would need to be more sophisticated
    // to handle all node types properly
    const root = editorState._nodeMap.get('root');
    if (!root) return markdown;

    const children = (root as any).getChildren ? (root as any).getChildren() : [];
    children.forEach((node: any) => {
      const type = node.getType();
      const text = node.getTextContent();
      
      switch (type) {
        case 'heading':
          const tag = (node as any).getTag();
          const level = tag === 'h1' ? '#' : tag === 'h2' ? '##' : '###';
          markdown += `${level} ${text}\n\n`;
          break;
        case 'list':
          const listType = (node as any).getListType();
          const listChildren = node.getChildren ? node.getChildren() : [];
          listChildren.forEach((item: any, index: number) => {
            const prefix = listType === 'bullet' ? '-' : `${index + 1}.`;
            markdown += `${prefix} ${item.getTextContent()}\n`;
          });
          markdown += '\n';
          break;
        case 'quote':
          markdown += `> ${text}\n\n`;
          break;
        case 'code':
          markdown += `\`\`\`\n${text}\n\`\`\`\n\n`;
          break;
        default:
          if (text.trim()) {
            markdown += `${text}\n\n`;
          }
      }
    });
    
    return markdown;
  });
}

async function convertToHtml(editorState: EditorState, title: string): Promise<string> {
  const bodyHtml = await editorState.read(() => {
    return $generateHtmlFromNodes((editorState as any)._editor || editorState);
  });
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        h1, h2, h3 { margin-top: 2rem; }
        blockquote { 
            border-left: 4px solid #e5e7eb; 
            padding-left: 1rem;
            margin-left: 0;
            font-style: italic;
        }
        code { 
            background: #f3f4f6; 
            padding: 0.2rem 0.4rem; 
            border-radius: 0.25rem; 
        }
        pre { 
            background: #f3f4f6; 
            padding: 1rem; 
            border-radius: 0.5rem; 
            overflow-x: auto; 
        }
    </style>
</head>
<body>
    <h1>${title}</h1>
    ${bodyHtml}
</body>
</html>`;
}

export function downloadFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}