'use client';

import React, { useState } from 'react';
import { Copy, Check, Terminal, Sparkles, Lightbulb } from 'lucide-react';

interface ChatMarkdownProps {
  content: string;
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
    <div className="my-3 rounded-xl overflow-hidden border border-slate-700/80 bg-slate-950/90 shadow-lg shadow-black/40">
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
          className="flex items-center space-x-1 px-2 py-0.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition text-[11px]"
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
      <div className="p-3.5 overflow-x-auto font-mono text-xs text-slate-200 leading-relaxed scrollbar-thin scrollbar-thumb-slate-700">
        <pre className="m-0">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

// Inline formatting parser for **bold**, *italic*, `inline code`, and links
function renderInlineElements(text: string): React.ReactNode {
  // Regex to split by bold (**text**), inline code (`code`), and italic (*text*)
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
              className="mx-0.5 px-1.5 py-0.5 rounded-md bg-indigo-950/80 border border-indigo-500/30 text-indigo-200 font-mono text-[12px]"
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

export default function ChatMarkdown({ content }: ChatMarkdownProps) {
  // Normalize line endings
  const normalized = content
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/\r\n/g, '\n');

  // Split into raw blocks (detecting fenced code blocks first)
  const lines = normalized.split('\n');
  const elements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeLang = '';
  let codeBuffer: string[] = [];

  for (let idx = 0; idx < lines.length; idx++) {
    const rawLine = lines[idx];
    const trimmed = rawLine.trim();

    // Check code fence
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // End of code block
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
        // Start of code block
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
          className="my-2 p-3 rounded-xl bg-gradient-to-r from-indigo-950/50 to-purple-950/30 border-l-4 border-indigo-500 text-slate-300 text-[13px] flex items-start gap-2.5 shadow-sm"
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
        <div key={`h3-${idx}`} className="mt-3.5 mb-1.5 flex items-center gap-2">
          <div className="w-1.5 h-4 rounded-full bg-gradient-to-b from-indigo-400 to-purple-500" />
          <h3 className="text-[14px] font-bold text-indigo-200 tracking-wide">
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
        <div key={`h2-${idx}`} className="mt-4 mb-2 pb-1 border-b border-slate-800/80">
          <h2 className="text-[15px] font-extrabold text-white flex items-center gap-2">
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
          className="flex items-start gap-2.5 my-1.5 pl-1 py-1 rounded-lg transition hover:bg-slate-900/30"
        >
          <span className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 font-mono text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
            {num}
          </span>
          <div className="flex-1 text-slate-200 text-[13.5px] leading-relaxed">
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
          className="flex items-start gap-2.5 my-1.5 pl-1.5 py-0.5"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-indigo-400 to-purple-400 mt-2 shrink-0 shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
          <div className="flex-1 text-slate-200 text-[13.5px] leading-relaxed">
            {renderInlineElements(bulletContent)}
          </div>
        </div>
      );
      continue;
    }

    // Standard Paragraph text
    elements.push(
      <div key={`p-${idx}`} className="text-slate-200 text-[13.5px] leading-relaxed my-1">
        {renderInlineElements(rawLine)}
      </div>
    );
  }

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
