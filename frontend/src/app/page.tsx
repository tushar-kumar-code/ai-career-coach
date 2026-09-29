import Link from 'next/link';
import { Compass, ShieldCheck, Target, ArrowRight, Award } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] text-slate-900 dark:text-slate-100 flex flex-col justify-between selection:bg-blue-600 selection:text-white">
      {/* Header Navigation */}
      <header className="px-6 sm:px-8 py-5 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-[#1E293B]/95 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 dark:bg-blue-600/20 border border-blue-500/40 flex items-center justify-center shadow-sm">
            <Compass className="w-5 h-5 text-white dark:text-sky-400" />
          </div>
          <div>
            <span className="font-bold text-lg sm:text-xl text-slate-900 dark:text-white tracking-tight">AI Career Coach</span>
            <span className="hidden sm:inline-block ml-2 text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
              Career Platform
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/login"
            className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            Sign In
          </Link>
          <Link
            href="/login"
            className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-sm flex items-center space-x-2"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 py-16 sm:py-20 text-center flex flex-col items-center">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 text-xs font-semibold uppercase tracking-wider mb-6">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-600 dark:text-sky-400" />
          <span>Evidence-Based Career Development</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight mb-6 max-w-4xl">
          Discover Your Ideal Career with a Proven <span className="text-blue-600 dark:text-sky-400">AI Career Coach</span> & Digital Twin
        </h1>

        <p className="text-base sm:text-lg text-slate-700 dark:text-slate-300 max-w-2xl leading-relaxed mb-10 font-normal">
          A trustworthy career intelligence platform that analyzes your natural strengths, verifies your skills with real evidence, optimizes your resume for ATS, builds custom roadmaps, and conducts interactive mock interviews.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
          <Link
            href="/assessment"
            className="w-full sm:w-auto px-8 py-3.5 sm:py-4 rounded-xl font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md transition-all flex items-center justify-center space-x-2.5 text-sm sm:text-base"
          >
            <Compass className="w-5 h-5 text-white" />
            <span>Take Career Discovery Assessment</span>
          </Link>
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-3.5 sm:py-4 rounded-xl font-semibold bg-white dark:bg-[#1E293B] border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 transition-all flex items-center justify-center space-x-2 text-sm sm:text-base shadow-sm"
          >
            <span>Explore Dashboard</span>
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 sm:mt-20 text-left w-full">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#1E293B] border border-slate-200 dark:border-slate-800 shadow-sm hover:border-blue-500/50 transition-all">
            <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-sky-400 mb-4">
              <Compass className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Adaptive Career Discovery</h3>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
              Don&apos;t know your career path yet? Our 12-dimension adaptive assessment evaluates your strengths, reasoning, and problem solving to identify verified role matches.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-[#1E293B] border border-slate-200 dark:border-slate-800 shadow-sm hover:border-blue-500/50 transition-all">
            <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-sky-400 mb-4">
              <Award className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Career Digital Twin</h3>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
              Continuously tracks verified skills, confidence metrics, resume ATS scores, and real STAR interview performance with complete auditability.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-[#1E293B] border border-slate-200 dark:border-slate-800 shadow-sm hover:border-blue-500/50 transition-all">
            <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-sky-400 mb-4">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Structured Roadmap & Practice</h3>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
              Receive prioritized daily learning tasks, interactive STAR mock interviews, and tailored resume optimization built for genuine job applications.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-200 dark:border-slate-800 text-center text-xs text-slate-600 dark:text-slate-400 bg-white/50 dark:bg-transparent">
        © 2026 AI Career Coach Platform. All Rights Reserved.
      </footer>
    </div>
  );
}
