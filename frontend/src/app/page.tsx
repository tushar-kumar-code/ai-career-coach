import Link from 'next/link';
import { Compass, ShieldCheck, Target, ArrowRight, Award } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#FAF8F3] dark:bg-[#0F172A] text-[#273444] dark:text-[#F1F5F9] flex flex-col justify-between selection:bg-[#B89B72] selection:text-white">
      {/* Header Navigation */}
      <header className="px-6 sm:px-8 py-5 flex items-center justify-between border-b border-[#E7E2D8] dark:border-[#334155] bg-white/95 dark:bg-[#172235]/95 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-[#17324D] dark:bg-[#102A43] border border-[#B89B72]/40 flex items-center justify-center shadow-sm">
            <Compass className="w-5 h-5 text-[#B89B72]" />
          </div>
          <div>
            <span className="font-bold text-lg sm:text-xl text-[#17324D] dark:text-[#F1F5F9] tracking-tight">AI Career Coach</span>
            <span className="hidden sm:inline-block ml-2 text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-[#B89B72]/15 text-[#17324D] dark:text-[#D9C19A] border border-[#B89B72]/30">
              Career Platform
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/login"
            className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-white hover:bg-[#F5F1E8] dark:hover:bg-[#1E2D44] transition"
          >
            Sign In
          </Link>
          <Link
            href="/login"
            className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-[#17324D] hover:bg-[#102A43] text-white transition-all shadow-sm flex items-center space-x-2"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 py-16 sm:py-20 text-center flex flex-col items-center">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#B89B72]/15 border border-[#B89B72]/35 text-[#17324D] dark:text-[#D9C19A] text-xs font-semibold uppercase tracking-wider mb-6">
          <ShieldCheck className="w-3.5 h-3.5 text-[#B89B72]" />
          <span>Evidence-Based Career Development</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-[#17324D] dark:text-[#F1F5F9] tracking-tight leading-tight mb-6 max-w-4xl">
          Discover Your Ideal Career with a Proven <span className="text-[#B89B72]">AI Career Coach</span> & Digital Twin
        </h1>

        <p className="text-base sm:text-lg text-[#64748B] dark:text-[#A8B3C2] max-w-2xl leading-relaxed mb-10">
          A trustworthy career intelligence platform that analyzes your natural strengths, verifies your skills with real evidence, optimizes your resume for ATS, builds custom roadmaps, and conducts interactive mock interviews.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
          <Link
            href="/assessment"
            className="w-full sm:w-auto px-8 py-3.5 sm:py-4 rounded-xl font-bold bg-[#17324D] hover:bg-[#102A43] text-white shadow-sm transition-all flex items-center justify-center space-x-2.5 text-sm sm:text-base"
          >
            <Compass className="w-5 h-5 text-[#B89B72]" />
            <span>Take Career Discovery Assessment</span>
          </Link>
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-3.5 sm:py-4 rounded-xl font-semibold bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] hover:bg-[#F5F1E8] dark:hover:bg-[#1E2D44] text-[#17324D] dark:text-[#F1F5F9] transition-all flex items-center justify-center space-x-2 text-sm sm:text-base shadow-sm"
          >
            <span>Explore Dashboard</span>
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 sm:mt-20 text-left w-full">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] shadow-sm hover:border-[#B89B72]/60 transition-all">
            <div className="w-12 h-12 rounded-xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] flex items-center justify-center text-[#B89B72] mb-4">
              <Compass className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-[#17324D] dark:text-[#F1F5F9] mb-2">Adaptive Career Discovery</h3>
            <p className="text-sm text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">
              Don&apos;t know your career path yet? Our 12-dimension adaptive assessment evaluates your strengths, reasoning, and problem solving to identify verified role matches.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] shadow-sm hover:border-[#B89B72]/60 transition-all">
            <div className="w-12 h-12 rounded-xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] flex items-center justify-center text-[#B89B72] mb-4">
              <Award className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-[#17324D] dark:text-[#F1F5F9] mb-2">Career Digital Twin</h3>
            <p className="text-sm text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">
              Continuously tracks verified skills, confidence metrics, resume ATS scores, and real STAR interview performance with complete auditability.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] shadow-sm hover:border-[#B89B72]/60 transition-all">
            <div className="w-12 h-12 rounded-xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] flex items-center justify-center text-[#B89B72] mb-4">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-[#17324D] dark:text-[#F1F5F9] mb-2">Structured Roadmap & Practice</h3>
            <p className="text-sm text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">
              Receive prioritized daily learning tasks, interactive STAR mock interviews, and tailored resume optimization built for genuine job applications.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-[#E7E2D8] dark:border-[#334155] text-center text-xs text-[#64748B] dark:text-[#A8B3C2] bg-white/50 dark:bg-transparent">
        © 2026 AI Career Coach Platform. All Rights Reserved.
      </footer>
    </div>
  );
}
