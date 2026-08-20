import { TrendingUp, ShieldCheck, Award, FileText, Mic } from 'lucide-react';

export default function ProgressPage() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h1 className="text-2xl font-extrabold text-white mb-1">Progress Tracking & Job Readiness Score</h1>
        <p className="text-xs text-slate-400">Weighted composition of verified skills, resume ATS score, projects, and interview performance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-32 h-32 rounded-full border-8 border-indigo-500/20 border-t-indigo-500 flex items-center justify-center">
            <span className="text-4xl font-extrabold text-white">74</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">Composite Job Readiness Score</h3>
            <p className="text-xs text-emerald-400 font-semibold mt-1">Ready for Mid-level Software Developer Applications</p>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white mb-2">Health Breakdown</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400 flex items-center gap-2"><FileText className="w-4 h-4 text-purple-400" /> Resume ATS Score</span>
              <span className="font-bold text-slate-200">82%</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400 flex items-center gap-2"><Award className="w-4 h-4 text-indigo-400" /> Verified Skill Coverage</span>
              <span className="font-bold text-slate-200">70%</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400 flex items-center gap-2"><Mic className="w-4 h-4 text-pink-400" /> Interview STAR Average</span>
              <span className="font-bold text-slate-200">76%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
