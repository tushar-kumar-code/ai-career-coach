'use client';

import React, { useState } from 'react';
import { Copy, Check, Terminal, Sparkles, Lightbulb } from 'lucide-react';

interface ChatMarkdownProps {
  content: string;
  fontSize?: 'normal' | 'large';
}

// Subcomponent for Code Blocks with language tag and 1-click Copy
function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3.5 rounded-xl overflow-hidden border border-slate-700/80 bg-slate-950/95 shadow-lg shadow-black/40">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900/90 border-b border-slate-800 text-xs text-slate-400">
        <div className="flex items-center space-x-1.5 font-mono text-[11px] text-indigo-300">
          <Terminal className="w-3.5 h-3.5 text-indigo-400" />
          <span className="uppercase tracking-wider font-semibold">
            {language || 'code'}
          </span>
        </div>
        <button
          onClick={handleCopy}
          type="button"
          className="flex items-center space-x-1 px-2.5 py-1 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition text-[11px]"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content */}
      <div className="p-4 overflow-x-auto font-mono text-xs sm:text-sm text-slate-200 leading-relaxed scrollbar-thin scrollbar-thumb-slate-700">
        <pre className="m-0">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

// Subcomponent for Markdown Table
function MarkdownTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="my-4 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60 shadow-md">
      <table className="w-full text-left text-xs sm:text-sm border-collapse">
        <thead>
          <tr className="bg-slate-900/90 border-b border-slate-800 text-indigo-300 font-semibold">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-2.5 whitespace-nowrap">
                {renderInlineElements(h.trim())}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {rows.map((row, rIdx) => (
            <tr
              key={rIdx}
              className={`transition hover:bg-slate-900/40 ${
                rIdx % 2 === 0 ? 'bg-transparent' : 'bg-slate-900/20'
              }`}
            >
              {row.map((cell, cIdx) => (
                <td key={cIdx} className="px-4 py-2.5 text-slate-300 align-top">
                  {renderInlineElements(cell.trim())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Inline formatting parser for **bold**, *italic*, `inline code`, and links
function renderInlineElements(text: string): React.ReactNode {
  const tokens = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);

  return (
    <span>
      {tokens.map((token, i) => {
        if (token.startsWith('**') && token.endsWith('**') && token.length >= 4) {
          return (
            <strong key={i} className="font-bold text-white tracking-wide">
              {token.slice(2, -2)}
            </strong>
          );
        }
        if (token.startsWith('`') && token.endsWith('`') && token.length >= 2) {
          return (
            <code
              key={i}
              className="mx-0.5 px-1.5 py-0.5 rounded-md bg-indigo-950/80 border border-indigo-500/30 text-indigo-200 font-mono text-[12px] sm:text-[13px]"
            >
              {token.slice(1, -1)}
            </code>
          );
        }
        if (token.startsWith('*') && token.endsWith('*') && token.length >= 2 && !token.startsWith('**')) {
          return (
            <em key={i} className="italic text-slate-300">
              {token.slice(1, -1)}
            </em>
          );
        }
        return token;
      })}
    </span>
  );
}

export default function ChatMarkdown({ content, fontSize = 'normal' }: ChatMarkdownProps) {
  // Normalize line endings
  const normalized = content
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/\r\n/g, '\n');

  const lines = normalized.split('\n');
  const elements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeLang = '';
  let codeBuffer: string[] = [];

  let inTable = false;
  let tableHeaders: string[] = [];
  let tableRows: string[][] = [];

  const textSizeClass = fontSize === 'large' ? 'text-base sm:text-[17px]' : 'text-[14.5px] sm:text-[15.5px]';

  const flushTable = () => {
    if (inTable && tableHeaders.length > 0) {
      elements.push(
        <MarkdownTable
          key={`table-${elements.length}`}
          headers={tableHeaders}
          rows={tableRows}
        />
      );
      inTable = false;
      tableHeaders = [];
      tableRows = [];
    }
  };

  for (let idx = 0; idx < lines.length; idx++) {
    const rawLine = lines[idx];
    const trimmed = rawLine.trim();

    // Check code fence
    if (trimmed.startsWith('```')) {
      flushTable();
      if (inCodeBlock) {
        elements.push(
          <CodeBlock
            key={`code-${idx}`}
            language={codeLang}
            code={codeBuffer.join('\n')}
          />
        );
        inCodeBlock = false;
        codeLang = '';
        codeBuffer = [];
      } else {
        inCodeBlock = true;
        codeLang = trimmed.replace(/^```/, '').trim();
        codeBuffer = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(rawLine);
      continue;
    }

    // Markdown Table detection: lines starting and ending with '|'
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.split('|').length > 2) {
      const cells = trimmed
        .slice(1, -1)
        .split('|')
        .map((c) => c.trim());

      // Check if separator line (|---|---|)
      const isSeparator = cells.every((c) => /^:?-+:?$/.test(c));

      if (!inTable) {
        // First line is headers
        inTable = true;
        tableHeaders = cells;
        tableRows = [];
      } else if (isSeparator) {
        // Ignore separator row
        continue;
      } else {
        // Data row
        tableRows.push(cells);
      }
      continue;
    } else if (inTable) {
      flushTable();
    }

    // Horizontal Rule: '---' or '***'
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      elements.push(
        <hr key={`hr-${idx}`} className="my-4 border-t border-slate-800/80" />
      );
      continue;
    }

    // Empty line spacing
    if (!trimmed) {
      elements.push(<div key={`spacer-${idx}`} className="h-2" />);
      continue;
    }

    // Callout / Blockquote detection (> Quote or Tip)
    if (trimmed.startsWith('>')) {
      const quoteText = trimmed.replace(/^>\s*/, '');
      elements.push(
        <div
          key={`quote-${idx}`}
          className="my-3 p-3.5 rounded-xl bg-gradient-to-r from-indigo-950/60 to-purple-950/40 border-l-4 border-indigo-500 text-slate-200 text-sm sm:text-[14.5px] flex items-start gap-3 shadow-sm"
        >
          <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed font-medium">
            {renderInlineElements(quoteText)}
          </div>
        </div>
      );
      continue;
    }

    // Level 3 Heading: ### Title
    if (trimmed.startsWith('### ')) {
      const headingText = trimmed.replace(/^###\s+/, '');
      elements.push(
        <div key={`h3-${idx}`} className="mt-4 mb-2 flex items-center gap-2">
          <div className="w-1.5 h-4.5 rounded-full bg-gradient-to-b from-indigo-400 to-purple-500" />
          <h3 className="text-[15.5px] sm:text-[16.5px] font-bold text-indigo-200 tracking-wide">
            {renderInlineElements(headingText)}
          </h3>
        </div>
      );
      continue;
    }

    // Level 1 or 2 Heading: ## Title or # Title
    if (trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
      const headingText = trimmed.replace(/^#+\s+/, '');
      elements.push(
        <div key={`h2-${idx}`} className="mt-5 mb-2.5 pb-1.5 border-b border-slate-800">
          <h2 className="text-base sm:text-lg font-extrabold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            {renderInlineElements(headingText)}
          </h2>
        </div>
      );
      continue;
    }

    // Numbered List: 1. Item
    if (/^\d+\.\s/.test(trimmed)) {
      const match = trimmed.match(/^(\d+)\.\s*(.*)$/);
      const num = match ? match[1] : '1';
      const itemContent = match ? match[2] : trimmed;

      elements.push(
        <div
          key={`num-${idx}`}
          className="flex items-start gap-3 my-2 pl-1 py-1 rounded-lg transition hover:bg-slate-900/30"
        >
          <span className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 font-mono text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
            {num}
          </span>
          <div className={`flex-1 text-slate-200 ${textSizeClass} leading-relaxed`}>
            {renderInlineElements(itemContent)}
          </div>
        </div>
      );
      continue;
    }

    // Bullet List: - Item or * Item
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const bulletContent = trimmed.substring(2);
      elements.push(
        <div
          key={`bullet-${idx}`}
          className="flex items-start gap-3 my-1.5 pl-1.5 py-0.5"
        >
          <span className="w-2 h-2 rounded-full bg-gradient-to-r from-indigo-400 to-purple-400 mt-2 shrink-0 shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
          <div className={`flex-1 text-slate-200 ${textSizeClass} leading-relaxed`}>
            {renderInlineElements(bulletContent)}
          </div>
        </div>
      );
      continue;
    }

    // Standard Paragraph text
    elements.push(
      <div key={`p-${idx}`} className={`text-slate-200 ${textSizeClass} leading-relaxed my-1.5`}>
        {renderInlineElements(rawLine)}
      </div>
    );
  }

  flushTable();

  // Handle unterminated code buffer if any
  if (inCodeBlock && codeBuffer.length > 0) {
    elements.push(
      <CodeBlock
        key="code-unterminated"
        language={codeLang}
        code={codeBuffer.join('\n')}
      />
    );
  }

  return <div className="space-y-1">{elements}</div>;
}
