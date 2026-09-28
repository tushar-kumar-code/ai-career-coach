'use client';

import React, { useState, useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  Sparkles,
  MessageSquare,
  Send,
  X,
  Maximize2,
  Loader2,
  Bot,
  User,
  RefreshCw,
  FileText,
  Award,
  MapPin,
  Dumbbell,
  Mic,
  Briefcase,
  LayoutDashboard,
  Zap,
  ArrowRight
} from 'lucide-react';
import { sendChatMessage } from '@/lib/api-client';
import { useAuth } from '@/context/AuthContext';
import ChatMarkdown from '@/components/chat/ChatMarkdown';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  isError?: boolean;
}

interface ContextConfig {
  title: string;
  badge: string;
  subtitle: string;
  icon: React.ElementType;
  initialGreeting: string;
  quickPrompts: string[];
}

export default function GlobalAIAssistant() {
  const pathname = usePathname();
  const router = useRouter();
  const { hasCompletedAssessment } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Determine current contextual guidance based on route pathname
  const getContextConfig = (path: string): ContextConfig => {
    if (path.startsWith('/resume')) {
      return {
        title: 'Resume & ATS Coach',
        badge: 'Resume Context',
        subtitle: 'Optimizing bullet points, ATS keywords & technical impact',
        icon: FileText,
        initialGreeting:
          "👋 **Welcome to your Resume & ATS Coach!**\n\nI can analyze your resume bullet points using the Google XYZ formula, suggest missing keywords to pass ATS filters, and highlight projects that impress recruiters. How can I help with your resume today?",
        quickPrompts: [
          'How do I rewrite my project bullet points with measurable impact?',
          'What high-frequency ATS keywords should I add for tech roles?',
          'How should I structure my work experience to pass automated screening?',
        ],
      };
    }
    if (path.startsWith('/skills')) {
      return {
        title: 'Skill Gap & Matrix Coach',
        badge: 'Skills Context',
        subtitle: 'Identifying high-priority gaps and skill verification paths',
        icon: Award,
        initialGreeting:
          "👋 **Welcome to your Skill Matrix Coach!**\n\nI can help you prioritize which technical skills to learn next, analyze industry demand for your target role, and guide you on validating skills with hands-on proof. What skill would you like advice on?",
        quickPrompts: [
          'What are the highest ROI skills to learn for an entry-level role?',
          'How do I verify intermediate proficiency in Python and SQL?',
          'Which secondary frameworks pair best with my current core stack?',
        ],
      };
    }
    if (path.startsWith('/roadmap')) {
      return {
        title: 'Roadmap & Task Coach',
        badge: 'Roadmap Context',
        subtitle: 'Clarifying daily milestones, concepts & pacing',
        icon: MapPin,
        initialGreeting:
          "👋 **Welcome to your Roadmap Coach!**\n\nStuck on a milestone or wondering how to tackle today's study plan? I can explain core concepts, break down complex topics into bite-sized steps, and keep your learning velocity high.",
        quickPrompts: [
          'What should my daily focus be for this phase of the roadmap?',
          'Can you explain the core concepts of this week with real-world examples?',
          'How much time per day should I allocate to complete this milestone?',
        ],
      };
    }
    if (path.startsWith('/practice')) {
      return {
        title: 'Micro Practice & Coding Coach',
        badge: 'Practice Context',
        subtitle: 'Algorithm patterns, debugging help & conceptual breakdowns',
        icon: Dumbbell,
        initialGreeting:
          "👋 **Ready to practice!**\n\nI can break down coding patterns, explain time & space complexity, give you quick technical quizzes, or walk through problem-solving frameworks step-by-step.",
        quickPrompts: [
          'Explain the Two Pointers and Sliding Window patterns simply.',
          'How do I calculate Big-O time and space complexity quickly?',
          'Give me a 3-question conceptual quiz on Data Structures.',
        ],
      };
    }
    if (path.startsWith('/interview')) {
      return {
        title: 'Mock Interview Prep Coach',
        badge: 'Interview Context',
        subtitle: 'STAR behavioral answers, technical questions & HR tips',
        icon: Mic,
        initialGreeting:
          "👋 **Welcome to your Interview Prep Coach!**\n\nNeed help structuring behavioral answers with the STAR method, or rehearsing answers for tough technical and HR questions? Let's practice together!",
        quickPrompts: [
          'How do I answer "Tell me about a difficult engineering challenge" using STAR?',
          'What are top questions recruiters ask in technical phone screens?',
          'How do I answer: "What is your biggest technical weakness?"',
        ],
      };
    }
    if (path.startsWith('/jobs')) {
      return {
        title: 'Job Engine & Career Coach',
        badge: 'Job Engine Context',
        subtitle: 'Application tailoring, recruiter outreach & salary insights',
        icon: Briefcase,
        initialGreeting:
          "👋 **Welcome to your Job Search Coach!**\n\nI can help you write customized cold outreach messages to hiring managers, evaluate job fit scores, and tailor your application to stand out from hundreds of applicants.",
        quickPrompts: [
          'Write a personalized LinkedIn outreach message to a tech recruiter.',
          'How can I tailor my application for a competitive role with 50+ applicants?',
          'What smart questions should I ask the engineering manager at the end?',
        ],
      };
    }

    // Default / Dashboard / Global Context
    return {
      title: 'AI Career Assistant',
      badge: 'Overall Guidance',
      subtitle: 'Holistic career coaching, next steps & readiness guidance',
      icon: LayoutDashboard,
      initialGreeting:
        "👋 **Hello! I'm your unified AI Career Coach.**\n\nI'm with you across your entire journey — from Career Discovery to Resume ATS, Skill Matrix, Roadmaps, Practice, Interviews, and Final Placement. Ask me anything about your career progression!",
      quickPrompts: [
        'What should be my next focus based on my current progress?',
        'How can I increase my overall placement readiness score?',
        'What are the key milestones to complete before applying for jobs?',
      ],
    };
  };

  const contextConfig = getContextConfig(pathname);
  const ContextIcon = contextConfig.icon;

  // Initialize or update initial greeting when route changes if conversation is empty
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'init-greeting',
          sender: 'ai',
          text: contextConfig.initialGreeting,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  }, [pathname]);

  // Auto scroll to bottom of chat
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  // Close drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText ?? inputMessage).trim();
    if (!textToSend || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const historyPayload = messages
        .filter((m) => !m.isError && m.id !== 'init-greeting')
        .slice(-6)
        .map((m) => ({
          role: (m.sender === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
          content: m.text,
        }));

      const res = await sendChatMessage(textToSend, historyPayload);
      const aiReply = res?.reply || "I'm reviewing your profile. How else can I assist your career progression?";

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: aiReply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        sender: 'ai',
        text: `⚠️ **Coach Assistant Notice:** ${
          err?.message || 'Unable to connect to AI Coach service. Please verify your AI provider API key in Settings.'
        }`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        id: `reset-${Date.now()}`,
        sender: 'ai',
        text: contextConfig.initialGreeting,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const openFullChat = () => {
    setIsOpen(false);
    router.push('/chat');
  };

  // If user has not completed assessment or is already on /chat, hide the assistant
  if (!hasCompletedAssessment || pathname === '/chat') {
    return null;
  }

  return (
    <>
      {/* Floating Action Button (FAB) */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          aria-label="Open AI Career Assistant"
          className="group relative flex items-center space-x-2.5 px-4 py-3 rounded-full bg-[#17324D] hover:bg-[#102A43] dark:bg-[#247B7B] dark:hover:bg-[#1D6464] text-white font-semibold text-xs sm:text-sm shadow-xl shadow-slate-900/20 hover:scale-[1.03] active:scale-[0.98] transition-all duration-300 border border-[#247B7B]/40"
        >
          <div className="relative">
            <Sparkles className="w-5 h-5 text-[#247B7B] dark:text-[#5FA8A8]" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[#2E7D5B] rounded-full border-2 border-slate-950 animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[#2E7D5B] rounded-full border-2 border-slate-950" />
          </div>
          <span className="hidden sm:inline font-bold tracking-tight">AI Career Assistant</span>
          <span className="sm:hidden font-bold">Ask AI</span>
          <span className="px-1.5 py-0.5 rounded-full bg-white/20 text-[10px] font-mono font-medium">
            {contextConfig.badge.split(' ')[0]}
          </span>
        </button>
      </div>

      {/* Slide-out Backdrop (Mobile) */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 lg:bg-transparent lg:pointer-events-none transition-opacity"
        />
      )}

      {/* Slide-out Chat Panel */}
      <div
        className={`fixed top-0 right-0 h-full w-full sm:w-[440px] md:w-[480px] bg-white dark:bg-[#162235] border-l border-slate-200 dark:border-[#293548] shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-[#293548] bg-slate-50/90 dark:bg-[#0F172A]/90 backdrop-blur-md flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-[#17324D] dark:bg-[#1E2D44] border border-[#247B7B]/40 flex items-center justify-center text-[#247B7B] dark:text-[#5FA8A8] shadow-sm shrink-0">
              <ContextIcon className="w-5 h-5" />
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-[#17324D] dark:text-white truncate">{contextConfig.title}</h3>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-[#247B7B]/10 text-[#247B7B] dark:text-[#5FA8A8] border border-[#247B7B]/30 whitespace-nowrap">
                  {contextConfig.badge}
                </span>
              </div>
              <p className="text-[11px] text-[#64748B] dark:text-[#94A3B8] truncate">{contextConfig.subtitle}</p>
            </div>
          </div>

          <div className="flex items-center space-x-1.5 shrink-0 ml-2">
            <button
              onClick={openFullChat}
              title="Expand to Full AI Assistant Page"
              className="p-1.5 rounded-lg text-slate-400 hover:text-[#17324D] dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              title="Reset Conversation"
              className="p-1.5 rounded-lg text-slate-400 hover:text-[#17324D] dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              title="Close Panel (Esc)"
              className="p-1.5 rounded-lg text-slate-400 hover:text-[#17324D] dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Context Prompts Bar */}
        <div className="px-4 py-2.5 bg-slate-50 dark:bg-[#0F172A]/50 border-b border-slate-200 dark:border-[#293548] overflow-x-auto scrollbar-none flex items-center gap-2">
          <div className="flex items-center space-x-1 text-[11px] font-semibold text-[#64748B] dark:text-[#94A3B8] shrink-0">
            <Zap className="w-3.5 h-3.5 text-[#C78A20]" />
            <span>Suggested:</span>
          </div>
          {contextConfig.quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-white dark:bg-slate-800/80 hover:bg-[#247B7B]/10 hover:border-[#247B7B]/40 border border-slate-200 dark:border-slate-700/60 text-[#243447] dark:text-slate-300 hover:text-[#247B7B] whitespace-nowrap transition shrink-0 shadow-xs"
            >
              {prompt.length > 38 ? `${prompt.slice(0, 38)}...` : prompt}
            </button>
          ))}
        </div>

        {/* Chat Messages Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-2.5 ${msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                  msg.sender === 'user'
                    ? 'bg-[#17324D] dark:bg-[#247B7B] text-white'
                    : 'bg-[#247B7B]/15 text-[#247B7B] dark:text-[#5FA8A8] border border-[#247B7B]/30'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[85%] rounded-2xl p-3.5 text-xs sm:text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-[#17324D] dark:bg-[#247B7B] text-white rounded-tr-none'
                    : msg.isError
                    ? 'bg-[#C75C5C]/10 border border-[#C75C5C]/30 text-[#C75C5C] rounded-tl-none'
                    : 'bg-slate-100 dark:bg-[#0F172A] border border-slate-200 dark:border-[#293548] text-[#243447] dark:text-slate-200 rounded-tl-none shadow-xs'
                }`}
              >
                {msg.sender === 'ai' ? (
                  <ChatMarkdown content={msg.text} />
                ) : (
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                )}
                <div
                  className={`mt-1.5 text-[10px] ${
                    msg.sender === 'user' ? 'text-slate-300 text-right' : 'text-slate-400 dark:text-slate-500'
                  }`}
                >
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-start space-x-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#247B7B]/15 text-[#247B7B] border border-[#247B7B]/30 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3 rounded-2xl bg-slate-100 dark:bg-[#0F172A] border border-slate-200 dark:border-[#293548] text-[#243447] dark:text-slate-300 rounded-tl-none flex items-center space-x-2 text-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#247B7B]" />
                <span>Coach is analyzing context & crafting guidance...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer */}
        <div className="p-3.5 sm:p-4 border-t border-slate-200 dark:border-[#293548] bg-white dark:bg-[#162235]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Ask Coach for ${contextConfig.badge}...`}
              disabled={isLoading}
              className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-[#243447] dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#247B7B] disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="p-2.5 rounded-xl bg-[#17324D] hover:bg-[#102A43] dark:bg-[#247B7B] dark:hover:bg-[#1D6464] disabled:opacity-40 text-white transition shadow-sm shrink-0"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400 px-1">
            <span>Powered by Groq / Gemini LLM</span>
            <button
              onClick={openFullChat}
              className="hover:text-[#247B7B] transition flex items-center space-x-1"
            >
              <span>Full Screen Coach</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
