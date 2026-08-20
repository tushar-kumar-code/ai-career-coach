'use client';

import { useState } from 'react';
import { Mic, Send, Sparkles, AlertCircle, Play } from 'lucide-react';

export default function InterviewPage() {
  const [answerText, setAnswerText] = useState('');

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h1 className="text-2xl font-extrabold text-white mb-1">STAR Method Mock Interview System</h1>
        <p className="text-xs text-slate-400">Questions dynamically generated based on your target role and resume background.</p>
      </div>

      <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-semibold">
            Behavioral / Technical STAR Question
          </span>
          <span className="text-xs text-slate-400">Role: Software Developer</span>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
          <h2 className="text-base font-bold text-slate-100 leading-relaxed">
            "Describe a complex technical challenge you faced when integrating an external API into your application. How did you structure your solution and handle failures?"
          </h2>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-300">Your STAR Answer (Situation, Task, Action, Result):</label>
          <textarea
            rows={5}
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
            placeholder="Structure your answer clearly: 
1. Situation: Set the context.
2. Task: Describe your goal.
3. Action: Detail your specific steps and technical choices.
4. Result: Share outcomes and lessons learned."
            className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:border-indigo-500 focus:outline-none transition-all placeholder:text-slate-600"
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          <button className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300 flex items-center space-x-2">
            <Mic className="w-4 h-4 text-pink-400" />
            <span>Enable Voice Input</span>
          </button>

          <button className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-lg shadow-indigo-500/25 flex items-center space-x-2">
            <Sparkles className="w-4 h-4" />
            <span>Evaluate Answer</span>
          </button>
        </div>
      </div>
    </div>
  );
}
