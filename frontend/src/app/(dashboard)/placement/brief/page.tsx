'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Printer,
  ArrowLeft,
  GraduationCap,
  Sparkles,
  ShieldCheck,
  Award,
  FileText,
  Mic,
  MapPin,
  Briefcase,
  Target,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Star,
  Layers,
  Code
} from 'lucide-react';
import { getStudentCareerBrief } from '@/lib/api-client';
import { StudentCareerBriefData } from '@/lib/types';

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

export default function StudentCareerBriefPage() {
  const [brief, setBrief] = useState<StudentCareerBriefData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBrief();
  }, []);

  async function loadBrief() {
    setLoading(true);
    try {
      const data = await getStudentCareerBrief();
      setBrief(data);
    } catch (err) {
      console.error('Failed to load student brief:', err);
    } finally {
      setLoading(false);
    }
  }

  function handlePrint() {
    window.print();
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4 print:hidden">
        <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Generating 1-Page Student Career Brief...</p>
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center max-w-xl mx-auto space-y-4 print:hidden">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
        <h3 className="text-base font-bold text-white">Career Brief Unavailable</h3>
        <p className="text-xs text-slate-400">Complete your initial career assessment to generate your student brief.</p>
        <Link href="/assessment" className="inline-block px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold text-xs">
          Start Assessment →
        </Link>
      </div>
    );
  }

  const subScores = brief.sub_scores || {};
  const dimensions = [
    { label: 'Technical Skills', score: subScores.skill_readiness ?? 0, icon: Award, color: 'text-indigo-400' },
    { label: 'Resume & ATS', score: subScores.resume_readiness ?? 0, icon: FileText, color: 'text-purple-400' },
    { label: 'Interview & STAR', score: subScores.interview_readiness ?? 0, icon: Mic, color: 'text-pink-400' },
    { label: 'Roadmap Tasks', score: subScores.roadmap_progress ?? 0, icon: MapPin, color: 'text-blue-400' },
    { label: 'Job Matching', score: subScores.job_match_readiness ?? 0, icon: Briefcase, color: 'text-emerald-400' },
    { label: 'Portfolio Projects', score: subScores.portfolio_readiness ?? 0, icon: Code, color: 'text-amber-400' },
  ];

  return (
    <div className="max-w-4xl mx-auto pb-16 space-y-6">
      {/* Top Action Bar (Hidden in Print) */}
      <div className="flex items-center justify-between gap-4 print:hidden">
        <Link
          href="/placement"
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Placement Center</span>
        </Link>

        <button
          onClick={handlePrint}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-indigo-500/25 transition-all"
          id="print-brief-btn"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Save as PDF</span>
        </button>
      </div>

      {/* 1-PAGE DOCUMENT CONTAINER (Print-Optimized) */}
      <div className="p-8 md:p-10 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-6 print:p-0 print:border-none print:shadow-none print:bg-white print:text-black">
        {/* Document Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800 print:border-slate-300">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <GraduationCap className="w-5 h-5 text-indigo-400 print:text-indigo-600" />
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider print:text-indigo-600">
                Placement Candidate Career Brief
              </span>
            </div>
            <h1 className="text-2xl font-black text-white print:text-black tracking-tight">
              {brief.student_name}
            </h1>
            <div className="flex items-center space-x-3 text-xs text-slate-400 print:text-slate-600 flex-wrap gap-y-1">
              <span>Target Role: <strong className="text-slate-200 print:text-black font-semibold">{brief.target_career}</strong></span>
              <span>•</span>
              <span>Archetype: <strong className="text-slate-200 print:text-black font-semibold">{brief.primary_archetype}</strong></span>
              <span>•</span>
              <span>Level: <strong className="text-slate-200 print:text-black font-semibold">{brief.experience_level}</strong></span>
            </div>
          </div>

          <div className="flex items-center space-x-3 self-start sm:self-auto flex-shrink-0">
            <div className="text-right">
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-extrabold border ${getTierBadgeClass(brief.readiness_tier)} print:border-slate-400 print:text-black`}>
                {brief.readiness_tier}
              </span>
              <p className="text-[10px] text-slate-500 print:text-slate-600 mt-1">Generated {brief.generated_at}</p>
            </div>
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center font-black text-lg text-indigo-300 print:bg-slate-100 print:text-black print:border-slate-300">
              {brief.overall_readiness_score}%
            </div>
          </div>
        </div>

        {/* Readiness Dimensions Grid */}
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider print:text-slate-700">
            Readiness Dimensions Breakdown
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {dimensions.map((dim, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between print:bg-slate-50 print:border-slate-200"
              >
                <div className="flex items-center space-x-2">
                  <dim.icon className={`w-4 h-4 ${dim.color} print:text-slate-800`} />
                  <span className="text-xs font-semibold text-slate-300 print:text-slate-800">{dim.label}</span>
                </div>
                <span className="text-xs font-extrabold text-white print:text-black">{dim.score}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* 2-Column: Verified Skills vs Priority Gaps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Verified Competencies */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2.5 print:bg-slate-50 print:border-slate-200">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 print:text-black">
                <ShieldCheck className="w-4 h-4 text-emerald-400 print:text-emerald-700" />
                <span>Verified Competencies ({brief.verified_skills_count})</span>
              </h4>
            </div>
            {brief.verified_skills_sample.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {brief.verified_skills_sample.map((sk, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 print:bg-emerald-50 print:text-emerald-900 print:border-emerald-200"
                  >
                    ✓ {sk}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic print:text-slate-600">No skills verified yet.</p>
            )}
          </div>

          {/* Priority Target Gaps */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2.5 print:bg-slate-50 print:border-slate-200">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 print:text-black">
              <AlertTriangle className="w-4 h-4 text-amber-400 print:text-amber-700" />
              <span>Priority Placement Gaps ({brief.critical_missing_skills.length})</span>
            </h4>
            {brief.critical_missing_skills.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {brief.critical_missing_skills.map((sk, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20 print:bg-amber-50 print:text-amber-900 print:border-amber-200"
                  >
                    ⚡ {sk}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-emerald-400 font-semibold print:text-emerald-700">All critical skill gaps closed ✓</p>
            )}
          </div>
        </div>

        {/* 2-Column: Resume & Interview Assessment */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Resume & ATS Status */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2 print:bg-slate-50 print:border-slate-200">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 print:text-black">
              <FileText className="w-4 h-4 text-purple-400 print:text-purple-700" />
              <span>Resume & ATS Readiness</span>
            </h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between text-slate-400 print:text-slate-700">
                <span>ATS Screening Score:</span>
                <strong className="text-slate-200 print:text-black">{brief.latest_resume_ats_score}%</strong>
              </div>
              <div className="flex justify-between text-slate-400 print:text-slate-700">
                <span>Target Career Keyword Match:</span>
                <strong className="text-slate-200 print:text-black">{brief.latest_resume_match_pct}%</strong>
              </div>
              <div className="flex justify-between text-slate-400 print:text-slate-700">
                <span>Resume Document:</span>
                <span className="text-slate-300 print:text-slate-800 truncate max-w-[180px]">{brief.latest_resume_filename || 'Not uploaded'}</span>
              </div>
            </div>
          </div>

          {/* Mock Interview & STAR Assessment */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2 print:bg-slate-50 print:border-slate-200">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 print:text-black">
              <Mic className="w-4 h-4 text-pink-400 print:text-pink-700" />
              <span>Mock Interview & STAR Coaching</span>
            </h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between text-slate-400 print:text-slate-700">
                <span>Completed Mock Sessions:</span>
                <strong className="text-slate-200 print:text-black">{brief.interview_completed_count}</strong>
              </div>
              <div className="flex justify-between text-slate-400 print:text-slate-700">
                <span>Average Interview Score:</span>
                <strong className="text-slate-200 print:text-black">{brief.interview_avg_score}%</strong>
              </div>
              <div className="flex justify-between text-slate-400 print:text-slate-700">
                <span>Behavioral STAR Method:</span>
                <strong className={brief.interview_star_completed ? 'text-emerald-400 print:text-emerald-700' : 'text-amber-400 print:text-amber-700'}>
                  {brief.interview_star_completed ? 'Verified ✓' : 'Needs Practice'}
                </strong>
              </div>
            </div>
          </div>
        </div>

        {/* Portfolio & Completed Projects */}
        <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2 print:bg-slate-50 print:border-slate-200">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 print:text-black">
            <Code className="w-4 h-4 text-amber-400 print:text-amber-700" />
            <span>Capstone & Portfolio Projects ({brief.completed_projects.length})</span>
          </h4>
          {brief.completed_projects.length > 0 ? (
            <div className="space-y-2">
              {brief.completed_projects.map((proj, idx) => (
                <div key={idx} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 print:bg-white print:border-slate-200 text-xs">
                  <div className="flex justify-between font-semibold text-slate-200 print:text-black">
                    <span>{proj.title}</span>
                    <span className="text-[10px] text-indigo-400 font-bold print:text-indigo-700">{proj.difficulty}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 print:text-slate-600 mt-0.5">{proj.resume_relevance}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic print:text-slate-600">
              No capstone projects completed yet. (Roadmap progress: {brief.roadmap_progress_percent}%)
            </p>
          )}
        </div>

        {/* Next Best Action Footer Box */}
        {brief.next_action && brief.next_action.title && (
          <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-slate-900 to-purple-950/40 border border-indigo-500/20 space-y-1 print:bg-slate-100 print:border-slate-300">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-indigo-400 print:text-indigo-700 uppercase">
              <Zap className="w-3.5 h-3.5" />
              <span>Recommended Next Step for Candidate</span>
            </div>
            <p className="text-xs font-semibold text-white print:text-black">{brief.next_action.title}</p>
            <p className="text-[11px] text-slate-400 print:text-slate-600">{brief.next_action.description}</p>
          </div>
        )}
      </div>
    </div>
  );
}
