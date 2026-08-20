import { Briefcase, Building, CheckCircle2, ArrowUpRight } from 'lucide-react';

export default function JobsPage() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h1 className="text-2xl font-extrabold text-white mb-1">Job Engine & Application Matcher</h1>
        <p className="text-xs text-slate-400">Match score evaluates skills, experience, projects, and target role keywords.</p>
      </div>

      <div className="space-y-4">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className="px-2.5 py-1 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400">
                88% Match
              </span>
              <h3 className="text-lg font-bold text-white">Full-Stack Software Engineer</h3>
            </div>
            <p className="text-xs text-slate-400 flex items-center space-x-2">
              <Building className="w-3.5 h-3.5 text-slate-500" />
              <span>TechCorp Systems • Remote</span>
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300">
                Matched: Python, React, PostgreSQL
              </span>
              <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400">
                Missing: Docker
              </span>
            </div>
          </div>
          <button className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all flex items-center justify-center space-x-2 shrink-0">
            <span>Tailor Resume & Apply</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
