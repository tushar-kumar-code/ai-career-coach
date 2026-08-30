'use client';

import { useState, useEffect, useRef } from 'react';
import {
  Send,
  Sparkles,
  User,
  Loader2,
  Key,
  AlertCircle,
  Lightbulb,
  Bot,
  RefreshCw,
  Copy,
  Check,
  Trash2,
  Zap,
  Volume2,
  VolumeX,
  FileText,
  Terminal,
  Layers,
  Briefcase,
  DollarSign,
  HelpCircle
} from 'lucide-react';
import { sendChatMessage, getSavedAIConfig } from '@/lib/api-client';
import ApiKeyModal from '@/components/common/ApiKeyModal';
import ChatMarkdown from '@/components/chat/ChatMarkdown';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  provider?: string;
  isError?: boolean;
}

const CATEGORY_PROMPTS = [
  {
    category: 'Resume & ATS',
    icon: FileText,
    items: [
      {
        label: 'ATS Optimization',
        text: 'How do I optimize my resume bullet points using the Google XYZ formula for high-tier tech roles?'
      },
      {
        label: 'Skill Gap Analysis',
        text: 'What are the most in-demand technologies to highlight on my profile for a Software Engineer role?'
      }
    ]
  },
  {
    category: 'Coding & DSA',
    icon: Terminal,
    items: [
      {
        label: 'Core Data Structures',
        text: 'What are the top patterns (e.g. Two Pointers, Sliding Window, DP) asked in Coding rounds?'
      },
      {
        label: 'Time & Space Complexity',
        text: 'How can I quickly analyze and explain Big-O Time & Space Complexity during a live technical interview?'
      }
    ]
  },
  {
    category: 'System Design',
    icon: Layers,
    items: [
      {
        label: 'Caching & Scaling',
        text: 'Can you explain the key concepts of System Design: Redis Caching, Sharding, and Load Balancing simply?'
      },
      {
        label: 'Database Selection',
        text: 'When should I choose SQL vs NoSQL in system architecture interviews?'
      }
    ]
  },
  {
    category: 'Behavioral & STAR',
    icon: Briefcase,
    items: [
      {
        label: 'STAR Framework',
        text: 'What is the best way to structure behavioral answers using the STAR (Situation, Task, Action, Result) method?'
      },
      {
        label: 'Conflict Resolution',
        text: 'How do I answer: "Tell me about a time you disagreed with an engineering decision or teammate"?'
      }
    ]
  },
  {
    category: 'Salary & Career',
    icon: DollarSign,
    items: [
      {
        label: 'Offer Negotiation',
        text: 'What is the most professional script to negotiate a higher base salary or sign-on bonus for a tech job?'
      }
    ]
  }
];

const FOLLOW_UP_SUGGESTIONS = [
  { label: '💡 Practical Example', prompt: 'Can you show me a concrete practical example or code snippet for this?' },
  { label: '🎯 Step-by-Step Breakdown', prompt: 'Can you break this down into simple, actionable steps?' },
  { label: '📝 Mock Interview Question', prompt: 'Give me a mock interview question based on this topic and explain how to answer it.' },
  { label: '🔍 Explain Simply', prompt: 'Could you explain this in simpler terms with a real-world analogy?' },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'ai',
      text: '### 👋 Welcome to your **Contextual AI Career Coach**!\n\nI am synchronized with your **Digital Twin Profile**, **ATS Resume analysis**, and **personalized learning roadmap**.\n\n### 🎯 How I Can Accelerate Your Career:\n- **Technical Mastery**: Deep dive into Coding, DSA, System Design, and Backend/Frontend architectures.\n- **Resume & ATS Strategy**: Tailor your accomplishments into high-impact bullet points.\n- **Mock Interview Drills**: Master behavioral (STAR method) and technical interview challenges.\n- **Offer & Negotiation**: Strategies for landing top-tier compensation.\n\n*Feel free to ask any question or click a starter topic below to begin!*',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      provider: 'Live Career Coach',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasApiKey, setHasApiKey] = useState(false);
  const [activeProvider, setActiveProvider] = useState('groq');
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('All');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const checkConfig = () => {
    const cfg = getSavedAIConfig();
    setHasApiKey(!!cfg.apiKey);
    setActiveProvider(cfg.provider || 'groq');
  };

  useEffect(() => {
    checkConfig();
    const handleUpdate = () => checkConfig();
    window.addEventListener('ai-config-updated', handleUpdate);
    return () => window.removeEventListener('ai-config-updated', handleUpdate);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Clean up speech synthesis when component unmounts
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSpeak = (id: string, text: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    if (speakingId === id) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    // Clean markdown symbols for cleaner TTS speech
    const cleanText = text
      .replace(/###/g, '')
      .replace(/\*\*/g, '')
      .replace(/`/g, '')
      .replace(/>/g, '')
      .replace(/#/g, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(id);
    window.speechSynthesis.speak(utterance);
  };

  const handleClearChat = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setSpeakingId(null);
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'ai',
        text: '### 🚀 New Coaching Session Started\n\nWhat career topic, technical concept, or interview scenario would you like to explore?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: 'AI Coach',
      },
    ]);
  };

  const handleSend = async (customText?: string) => {
    const textToSend = (customText || input).trim();
    if (!textToSend || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Prepare history payload
    const historyPayload = messages
      .filter((m) => !m.isError)
      .map((m) => ({
        role: m.sender === 'user' ? ('user' as const) : ('assistant' as const),
        content: m.text,
      }));

    try {
      const response = await sendChatMessage(textToSend, historyPayload);
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: response.response,
        timestamp: response.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: response.provider || 'AI Coach',
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text:
          err.message ||
          'Could not reach AI provider. Please make sure your AI API Key is configured in AI Settings.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetryLast = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.sender === 'user');
    if (lastUserMsg) {
      setMessages((prev) => prev.filter((m) => !m.isError));
      handleSend(lastUserMsg.text);
    }
  };

  const allPrompts =
    activeCategory === 'All'
      ? CATEGORY_PROMPTS.flatMap((c) => c.items)
      : CATEGORY_PROMPTS.find((c) => c.category === activeCategory)?.items || [];

  return (
    <div className="space-y-3.5 max-w-4xl mx-auto h-[calc(100vh-7.5rem)] flex flex-col">
      {/* Header Bar */}
      <div className="p-3.5 sm:p-4 rounded-2xl bg-slate-900/80 border border-slate-800/90 flex items-center justify-between shrink-0 shadow-sm backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-extrabold text-white flex items-center gap-2">
              Contextual AI Career Coach
              <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full">
                <Zap className="w-3 h-3 text-amber-400" />
                Live LLM Engine
              </span>
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">
              Structured, easy-to-read career guidance synced with your profile & roadmap
            </p>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center space-x-2">
          {messages.length > 1 && (
            <button
              onClick={handleClearChat}
              title="Start New Chat"
              className="px-2.5 py-1.5 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-slate-800 hover:border-rose-500/30 transition text-xs flex items-center gap-1.5 font-medium"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          )}

          <button
            onClick={() => setIsKeyModalOpen(true)}
            className={`flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-xl border transition font-medium ${
              hasApiKey
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20'
            }`}
          >
            <Key className="w-3.5 h-3.5 text-amber-400" />
            <span>
              {hasApiKey ? `${activeProvider.toUpperCase()} Active` : 'Set AI Key'}
            </span>
          </button>
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-5 scrollbar-thin scrollbar-thumb-slate-800">
        {messages.map((msg, index) => {
          const isLastAiMessage = msg.sender === 'ai' && !msg.isError && index === messages.length - 1;

          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${
                msg.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.sender === 'ai' && (
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-1 shadow-sm ${
                    msg.isError
                      ? 'bg-rose-500/20 border border-rose-500/30 text-rose-400'
                      : 'bg-indigo-500/20 border border-indigo-500/30 text-indigo-400'
                  }`}
                >
                  {msg.isError ? <AlertCircle className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                </div>
              )}

              <div
                className={`max-w-2xl p-4 sm:p-5 rounded-2xl text-sm leading-relaxed relative group transition-all ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-tr-none shadow-md shadow-indigo-600/20 font-medium'
                    : msg.isError
                    ? 'bg-rose-950/40 border border-rose-800/60 text-rose-200 rounded-tl-none'
                    : 'bg-slate-950/95 border border-slate-800/90 text-slate-200 rounded-tl-none shadow-md shadow-black/20'
                }`}
              >
                {/* Content Renderer */}
                {msg.sender === 'ai' && !msg.isError ? (
                  <ChatMarkdown content={msg.text} />
                ) : (
                  <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                )}

                {/* Follow-up Quick Action Chips (shown on latest AI response) */}
                {isLastAiMessage && !isLoading && (
                  <div className="mt-4 pt-3 border-t border-slate-800/80">
                    <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                      Suggested Follow-Ups:
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {FOLLOW_UP_SUGGESTIONS.map((item, sIdx) => (
                        <button
                          key={sIdx}
                          onClick={() => handleSend(item.prompt)}
                          className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-500/40 text-slate-300 hover:text-indigo-200 transition font-medium flex items-center gap-1"
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error actions */}
                {msg.isError && (
                  <div className="mt-3 pt-2.5 border-t border-rose-800/40 flex items-center gap-2">
                    <button
                      onClick={handleRetryLast}
                      className="text-xs px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 rounded-lg transition flex items-center gap-1.5 font-medium"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Retry
                    </button>
                    <button
                      onClick={() => setIsKeyModalOpen(true)}
                      className="text-xs px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 rounded-lg transition flex items-center gap-1.5"
                    >
                      <Key className="w-3.5 h-3.5 text-amber-400" />
                      Check AI Key
                    </button>
                  </div>
                )}

                {/* Meta row */}
                <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/60 text-[10px] text-slate-400">
                  <div className="flex items-center space-x-2">
                    {msg.provider && (
                      <span className="font-mono text-indigo-400/90 flex items-center gap-1 font-medium">
                        <Zap className="w-2.5 h-2.5 text-amber-400" />
                        {msg.provider}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2.5">
                    <span>{msg.timestamp}</span>

                    {msg.sender === 'ai' && !msg.isError && (
                      <>
                        {/* Audio Listen */}
                        <button
                          onClick={() => handleSpeak(msg.id, msg.text)}
                          title={speakingId === msg.id ? 'Stop listening' : 'Listen to answer'}
                          className={`p-1 rounded transition ${
                            speakingId === msg.id
                              ? 'text-indigo-400 bg-indigo-500/20'
                              : 'text-slate-400 hover:text-indigo-300'
                          }`}
                        >
                          {speakingId === msg.id ? (
                            <VolumeX className="w-3.5 h-3.5" />
                          ) : (
                            <Volume2 className="w-3.5 h-3.5" />
                          )}
                        </button>

                        {/* Copy Whole Message */}
                        <button
                          onClick={() => handleCopy(msg.id, msg.text)}
                          title="Copy response"
                          className="p-1 rounded text-slate-400 hover:text-indigo-300 transition"
                        >
                          {copiedId === msg.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0 mt-1 shadow-sm">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {/* Typing / Loading indicator */}
        {isLoading && (
          <div className="flex items-start space-x-3 justify-start">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-1 animate-pulse">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-slate-300 rounded-tl-none flex items-center space-x-2.5 text-xs shadow-sm">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span>AI Coach is structuring your personalized career answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Category Pills & Suggested Prompts (if conversation is starting) */}
      {messages.length <= 3 && (
        <div className="space-y-2 shrink-0">
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
            {['All', 'Resume & ATS', 'Coding & DSA', 'System Design', 'Behavioral & STAR', 'Salary & Career'].map(
              (cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1 rounded-lg font-medium whitespace-nowrap transition ${
                    activeCategory === cat
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                      : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
                  }`}
                >
                  {cat}
                </button>
              )
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {allPrompts.slice(0, 4).map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(item.text)}
                disabled={isLoading}
                className="text-xs p-2.5 rounded-xl bg-slate-900/80 hover:bg-indigo-950/40 border border-slate-800 hover:border-indigo-500/40 text-slate-300 hover:text-white transition text-left flex items-start space-x-2 group"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 mt-0.5 shrink-0 group-hover:text-indigo-300" />
                <div className="flex-1">
                  <span className="font-semibold text-indigo-300 block text-[11px] mb-0.5">
                    {item.label}
                  </span>
                  <span className="text-slate-400 group-hover:text-slate-200 line-clamp-1 text-[11px]">
                    {item.text}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Box with Auto-Expanding Multi-line Support */}
      <div className="p-2.5 sm:p-3 rounded-2xl bg-slate-900/90 border border-slate-800/90 flex items-end space-x-2.5 shrink-0 shadow-xl shadow-black/40 backdrop-blur-md">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            // auto resize up to 120px
            e.target.style.height = 'auto';
            e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={isLoading}
          placeholder="Ask your coach anything (e.g. 'Explain caching strategies', 'Review my tech stack')... [Enter to send]"
          className="flex-1 bg-slate-950/90 border border-slate-800/90 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-500 disabled:opacity-50 resize-none max-h-[120px] scrollbar-thin scrollbar-thumb-slate-700"
        />

        <button
          onClick={() => handleSend()}
          disabled={isLoading || !input.trim()}
          className="p-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white transition-all shadow-md shadow-indigo-600/30 disabled:shadow-none disabled:text-slate-500 flex items-center justify-center shrink-0 mb-0.5"
          title="Send message"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>

      {/* Key Modal */}
      <ApiKeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        onSaved={checkConfig}
      />
    </div>
  );
}
