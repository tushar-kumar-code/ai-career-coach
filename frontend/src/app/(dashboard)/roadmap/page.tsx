import { MapPin, CheckCircle2, Clock, BookOpen, Code } from 'lucide-react';

export default function RoadmapPage() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h1 className="text-2xl font-extrabold text-white mb-1">Personalized Learning Roadmap</h1>
        <p className="text-xs text-slate-400">Adaptive curriculum tailored to your target career role & current verified skills.</p>
      </div>

      <div className="space-y-6">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <span className="px-2.5 py-1 rounded text-xs font-bold bg-indigo-500/20 text-indigo-400 uppercase">
              Phase 1: Backend Architecture & APIs
            </span>
            <span className="text-xs text-slate-400 font-medium">Progress: 66%</span>
          </div>

          <div className="space-y-3 pt-2">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">Async FastAPI & Pydantic V2 Schemas</h4>
                  <p className="text-xs text-slate-400">Completed on August 15</p>
                </div>
              </div>
              <span className="px-2 py-1 rounded bg-slate-900 text-[11px] text-emerald-400 font-medium">Verified</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-indigo-500/30 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Clock className="w-5 h-5 text-indigo-400" />
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">PostgreSQL Async SQLAlchemy 2.0 Integration</h4>
                  <p className="text-xs text-slate-400">In Progress • Estimated time: 2 hours</p>
                </div>
              </div>
              <button className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all">
                Continue Task
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
