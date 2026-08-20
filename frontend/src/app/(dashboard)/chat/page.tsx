'use client';

import { useState } from 'react';
import { MessageSquare, Send, Sparkles, User } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'ai',
      text: 'Hello! I am your AI Career Coach. I have loaded your target career (Software Developer), current skill matrix, resume ATS score (82%), and interview history. How can I assist your career progression today?',
      timestamp: '11:30 AM',
    },
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: input,
      timestamp: 'Just now',
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    // Simulated AI contextual response
    setTimeout(() => {
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: `Based on your target role (Software Developer) and weak area in Docker/Containers, I recommend reviewing Module 3 in your personalized roadmap before your upcoming interview. Would you like me to generate 3 targeted interview questions on backend containerization?`,
        timestamp: 'Just now',
      };
      setMessages((prev) => [...prev, aiMsg]);
    }, 800);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-white">Contextual AI Career Coach</h1>
            <p className="text-xs text-slate-400">Understands your full Digital Twin, target role, and interview history</p>
          </div>
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'ai' && (
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-1">
                <Sparkles className="w-4 h-4" />
              </div>
            )}
            <div
              className={`max-w-xl p-4 rounded-2xl text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-none'
                  : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}
            >
              <p>{msg.text}</p>
              <span className="block text-[10px] text-slate-400 mt-2 text-right">{msg.timestamp}</span>
            </div>
            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input Box */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center space-x-3 shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask your coach anything (e.g. 'I have an interview tomorrow', 'How do I improve my resume?')..."
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-all placeholder:text-slate-500"
        />
        <button
          onClick={handleSend}
          className="p-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-500/25"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
