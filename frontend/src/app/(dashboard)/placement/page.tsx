'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  GraduationCap,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  Sparkles,
  Award,
  FileText,
  Briefcase,
  Target,
  Zap,
  Printer,
  ChevronRight,
  Filter,
  Layers,
  TrendingUp,
  ShieldCheck,
  Code
} from 'lucide-react';
import { getPlacementChecklist } from '@/lib/api-client';
import { getDigitalTwinProfile } from '@/lib/digital-twin-api';
import {
  PlacementChecklistData,
  PlacementChecklistItem,
  CareerDigitalTwinData
} from '@/lib/types';

// Category color mappings
const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Career Strategy': { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  'Resume & ATS': { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
  'Skill Mastery': { bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/20' },
  'Interview & Practice': { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20' },
  'Portfolio': { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  'Application Pipeline': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
};

function getTierBadgeClass(tier: string) {
  switch (tier) {
    case 'Placement Ready':
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    case 'Targeted Ready':
      return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
    case 'In Preparation':
      return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    default:
      return 'bg-slate-700/40 text-slate-300 border-slate-600/40';
  }
}

export default function PlacementReadinessPage() {
  const [checklistData, setChecklistData] = useState<PlacementChecklistData | null>(null);
  const [twinData, setTwinData] = useState<CareerDigitalTwinData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<'all' | 'pending' | 'completed'>('all');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [chk, twin] = await Promise.allSettled([
        getPlacementChecklist(),
        getDigitalTwinProfile()
      ]);
      if (chk.status === 'fulfilled') setChecklistData(chk.value);
      if (twin.status === 'fulfilled') setTwinData(twin.value);
    } catch (err) {
      console.error('Failed to load placement data:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Evaluating College Placement Readiness...</p>
      </div>
    );
  }

  const score = checklistData?.overall_readiness_score ?? twinData?.overall_readiness_score ?? 0;
  const tier = checklistData?.readiness_tier ?? 'Early Foundation';
  const tierDesc = checklistData?.tier_description ?? 'Start verifying your skills to track placement readiness.';
  const completedCount = checklistData?.completed_count ?? 0;
  const totalCount = checklistData?.total_count ?? 10;
  const completionPct = checklistData?.checklist_completion_percent ?? Math.round((completedCount / totalCount) * 100);
  const allItems = checklistData?.items ?? [];

  const filteredItems = allItems.filter(item => {
    if (activeFilter === 'pending') return !item.completed;
    if (activeFilter === 'completed') return item.completed;
    return true;
  });

  const nextAction = twinData?.next_action;

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Hero Header & Placement Readiness Tier Banner */}
      <div className="p-6 md:p-8 rounded-3xl bg-gradient-to-br from-indigo-950/90 via-slate-900 to-purple-950/90 border border-indigo-500/20 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold uppercase tracking-wider">
              <GraduationCap className="w-3.5 h-3.5" />
              <span>Campus Placement Command Center</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Placement Readiness & Audit
            </h1>
            <p className="text-xs md:text-sm text-slate-300 max-w-2xl leading-relaxed">
              {tierDesc}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 flex-shrink-0">
            {/* Score & Tier Card */}
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex items-center space-x-4 shadow-lg">
              <div className="relative flex items-center justify-center">
                <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-slate-800"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className={score >= 75 ? 'text-emerald-400' : score >= 50 ? 'text-indigo-400' : 'text-amber-400'}
                    strokeDasharray={`${score}, 100`}
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <span className="absolute text-sm font-black text-white">{score}%</span>
              </div>
              <div>
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${getTierBadgeClass(tier)}`}>
                  {tier}
                </span>
                <p className="text-[11px] text-slate-400 mt-1">
                  {completedCount}/{totalCount} Checklist Goals
                </p>
              </div>
            </div>

            {/* View 1-Page Brief CTA */}
            <Link
              href="/placement/brief"
              className="px-5 py-3.5 rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-indigo-500/25 transition-all transform hover:scale-[1.02]"
              id="view-student-brief-btn"
            >
              <FileText className="w-4 h-4" />
              <span>1-Page Student Brief →</span>
            </Link>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300">Checklist Completion Rate</span>
            <span className="font-bold text-indigo-400">{completionPct}% ({completedCount}/{totalCount} items completed)</span>
          </div>
          <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 h-full transition-all duration-500"
              style={{ width: `${completionPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Placement Action Center — Next Best Action (Hero Card) */}
      {nextAction && nextAction.title && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-violet-950/60 via-slate-900 to-slate-900 border border-violet-500/30 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-violet-400 text-xs font-bold uppercase tracking-wider">
              <Zap className="w-4 h-4" />
              <span>Placement Action Center • Highest Impact Focus</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30 font-bold uppercase">
              Priority Action
            </span>
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-white tracking-tight">{nextAction.title}</h3>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">{nextAction.description}</p>
              {nextAction.why_it_matters && (
                <p className="text-[11px] text-violet-300/80 italic pt-1">💡 Why it matters: {nextAction.why_it_matters}</p>
              )}
            </div>

            <Link
              href={nextAction.action_link || '/skills'}
              className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-extrabold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-violet-600/30 transition-all flex-shrink-0"
              id="placement-action-center-primary-cta"
            >
              <span>{nextAction.title || 'Take Action Now'}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* 10-Point Deterministic Placement Checklist */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-indigo-400" />
              <span>10-Point Real-Data Placement Checklist</span>
            </h2>
            <p className="text-xs text-slate-400">
              Evaluated strictly from real database evidence. Complete each milestone to maximize drive eligibility.
            </p>
          </div>

          {/* Filter pills */}
          <div className="flex items-center space-x-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 self-start sm:self-auto">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeFilter === 'all' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => setActiveFilter('pending')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeFilter === 'pending' ? 'bg-amber-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Pending ({totalCount - completedCount})
            </button>
            <button
              onClick={() => setActiveFilter('completed')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeFilter === 'completed' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Done ({completedCount})
            </button>
          </div>
        </div>

        {/* Checklist items list */}
        <div className="grid grid-cols-1 gap-3.5">
          {filteredItems.map((item, idx) => {
            const catStyle = CATEGORY_COLORS[item.category] || {
              bg: 'bg-slate-800/40',
              text: 'text-slate-400',
              border: 'border-slate-700'
            };

            return (
              <div
                key={item.key || idx}
                className={`p-4 md:p-5 rounded-2xl border transition-all ${
                  item.completed
                    ? 'bg-slate-900/50 border-emerald-500/20 hover:border-emerald-500/40'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start space-x-3.5">
                    {/* Status Icon */}
                    <div className="mt-0.5 flex-shrink-0">
                      {item.completed ? (
                        <div className="w-7 h-7 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                          <CheckCircle2 className="w-4 h-4" />
                        </div>
                      ) : (
                        <div className="w-7 h-7 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500">
                          <Clock className="w-4 h-4" />
                        </div>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        <h4 className={`text-sm font-bold ${item.completed ? 'text-slate-100' : 'text-slate-200'}`}>
                          {item.title}
                        </h4>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${catStyle.bg} ${catStyle.text} ${catStyle.border}`}>
                          {item.category}
                        </span>
                        {item.completed && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 font-bold">
                            Complete ✓
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
                      
                      <div className="flex items-center space-x-4 text-[11px] pt-0.5 text-slate-500">
                        <span>Current: <strong className="text-slate-300 font-semibold">{item.current_value || 'None'}</strong></span>
                        <span>•</span>
                        <span>Goal: <strong className="text-slate-400 font-medium">{item.target_value}</strong></span>
                      </div>
                    </div>
                  </div>

                  {/* 1-Click Action CTA */}
                  <div className="flex-shrink-0 self-end sm:self-center">
                    <Link
                      href={item.action_route}
                      className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition-all ${
                        item.completed
                          ? 'bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20'
                      }`}
                      id={`checklist-cta-${item.key}`}
                    >
                      <span>{item.action_title}</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Student Career Brief Banner CTA */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="space-y-1">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Printer className="w-4 h-4 text-indigo-400" />
            <span>Ready for Placement Review?</span>
          </h3>
          <p className="text-xs text-slate-400 max-w-xl">
            Generate and export your 1-Page Student Career Brief for campus placement cells, faculty mentors, or mock interviewers.
          </p>
        </div>
        <Link
          href="/placement/brief"
          className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 text-xs font-bold flex items-center space-x-2 transition-all flex-shrink-0"
        >
          <span>Open Career Brief</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
