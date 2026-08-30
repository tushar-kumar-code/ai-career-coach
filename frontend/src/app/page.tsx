import Link from 'next/link';
import { Sparkles, Compass, ShieldCheck, Target, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Header Navigation */}
      <header className="px-8 py-6 flex items-center justify-between border-b border-slate-800/50 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl text-white tracking-tight">AI Career Coach</span>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/login"
            className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-300 hover:text-white hover:bg-slate-900 transition"
          >
            Sign In
          </Link>
          <Link
            href="/login"
            className="px-5 py-2.5 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-500/25 flex items-center space-x-2"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 py-20 text-center flex flex-col items-center">
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-8">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Generation Career Intelligence</span>
        </div>

        <h1 className="text-5xl md:text-6xl font-extrabold text-white tracking-tight leading-tight mb-6 max-w-4xl">
          Discover Your Ideal Career with an <span className="gradient-text">AI Career Coach</span> & Digital Twin
        </h1>

        <p className="text-lg text-slate-400 max-w-2xl leading-relaxed mb-10">
          An end-to-end guidance platform that analyzes your natural strengths, verifies your skills with real evidence, tailors your resume, generates custom roadmaps, and conducts mock interviews.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/assessment"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white shadow-xl shadow-indigo-500/20 hover:opacity-95 transition-all flex items-center justify-center space-x-3 text-base"
          >
            <Compass className="w-5 h-5" />
            <span>Take Career Discovery Assessment</span>
          </Link>
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-semibold bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 transition-all flex items-center justify-center space-x-2 text-base"
          >
            <span>Explore Dashboard</span>
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 text-left w-full">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/40 transition-all">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
              <Compass className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">No Direction Required</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Don&apos;t know your career path yet? Our 12-dimension adaptive assessment evaluates your strengths, reasoning, and problem solving to find your perfect fit.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-purple-500/40 transition-all">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Career Digital Twin</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Continuously tracks your skills, confidence, verified project evidence, ATS resume match, and STAR interview performance without fake scores.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-pink-500/40 transition-all">
            <div className="w-12 h-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 mb-4">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Daily AI Coach & STAR Interviews</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Receive prioritized daily learning tasks, interactive STAR mock interviews, and tailored resume optimization built for real job applications.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-800/50 text-center text-xs text-slate-500">
        © 2026 AI Career Coach Platform. All Rights Reserved.
      </footer>
    </div>
  );
}
