'use client';

import { useState, useEffect } from 'react';
import {
  Sparkles, Award, FileText, CheckCircle2, AlertTriangle, ShieldCheck,
  Target, Briefcase, Mic, MapPin, Zap, ArrowRight, Loader2, Star, TrendingUp
} from 'lucide-react';
import Link from 'next/link';
import { getDigitalTwinProfile } from '@/lib/digital-twin-api';
import { getSkillProfile, getAssessmentResult } from '@/lib/api-client';
import {
  CareerDigitalTwinData,
  SkillProfileData,
  AssessmentResultData
} from '@/lib/types';

export default function DigitalTwinProfilePage() {
  const [loading, setLoading] = useState(true);
  const [twin, setTwin] = useState<CareerDigitalTwinData | null>(null);
  const [skillsProfile, setSkillsProfile] = useState<SkillProfileData | null>(null);
  const [assessmentData, setAssessmentData] = useState<AssessmentResultData | null>(null);

  useEffect(() => {
    async function loadAll() {
      try {
        const [twinRes, sData, aData] = await Promise.allSettled([
          getDigitalTwinProfile(),
          getSkillProfile(),
          getAssessmentResult()
        ]);
        if (twinRes.status === 'fulfilled') setTwin(twinRes.value);
        if (sData.status === 'fulfilled') setSkillsProfile(sData.value);
        if (aData.status === 'fulfilled') setAssessmentData(aData.value);
      } catch (err) {
        console.error('Digital twin load error:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAll();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Synchronizing Career Digital Twin...</p>
      </div>
    );
  }

  const targetRole = twin?.target_career || skillsProfile?.target_career || assessmentData?.selected_target_career || 'Software Developer';
  const archetype = twin?.primary_archetype || assessmentData?.archetype || 'Systems Builder';
  const readinessScore = twin?.overall_readiness_score ?? 0;
  const readinessLabel = twin?.readiness_label ?? 'In Progress';
  const subScores = twin?.sub_scores;
  const nextAction = twin?.next_action;
  const strengths = twin?.top_strengths || [];
  const gaps = twin?.priority_gaps || [];
  const criticalSkills = twin?.critical_missing_skills || [];
  const achievements = twin?.achievements || [];

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/80 via-slate-900 to-purple-950/80 border border-indigo-500/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-white">Career Digital Twin</h1>
              <p className="text-xs text-slate-400">
                Unified live profile combining Career Discovery, Resume ATS, Skill Matrix, Roadmap, Job Matches & Interview signals.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="px-4 py-2 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Readiness Score</p>
                <p className="text-xl font-black text-white">{readinessScore}<span className="text-xs font-normal text-slate-400">/100</span></p>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-bold ${
                readinessScore >= 75 ? 'bg-emerald-500/20 text-emerald-400' :
                readinessScore >= 50 ? 'bg-indigo-500/20 text-indigo-400' :
                readinessScore >= 25 ? 'bg-amber-500/20 text-amber-400' :
                'bg-red-500/20 text-red-400'
              }`}>{readinessLabel}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Target & Archetype Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-indigo-400" /> Target Career
          </span>
          <h2 className="text-lg font-bold text-white truncate">{targetRole}</h2>
          <p className="text-xs text-indigo-400 font-medium">Active Selection</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Archetype
          </span>
          <h2 className="text-lg font-bold text-purple-300 truncate">{archetype}</h2>
          <p className="text-xs text-slate-400">Discovery Engine Fit</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-emerald-400" /> Verified Skills
          </span>
          <h2 className="text-2xl font-extrabold text-emerald-400">
            {skillsProfile?.verified_count || 0}<span className="text-xs font-normal text-slate-400">/{skillsProfile?.total_skills_count || 0}</span>
          </h2>
          <p className="text-xs text-slate-400">Evidence Verified</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1.5">
            <Star className="w-3.5 h-3.5 text-amber-400" /> Achievements
          </span>
          <h2 className="text-2xl font-extrabold text-amber-400">
            {achievements.length}
          </h2>
          <p className="text-xs text-slate-400">Evidence Badges</p>
        </div>
      </div>

      {/* Next Best Action Card */}
      {nextAction && nextAction.title && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-500/30">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-amber-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Recommended Next Step</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold">{nextAction.related_goal}</span>
              </div>
              <h3 className="text-lg font-bold text-white">{nextAction.title}</h3>
              <p className="text-xs text-slate-300">{nextAction.why_it_matters}</p>
              <p className="text-[11px] text-emerald-400 font-medium">{nextAction.expected_impact}</p>
            </div>
            <Link
              href={nextAction.action_link}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center space-x-2 shrink-0 transition-colors shadow-lg shadow-indigo-600/30"
            >
              <span>Take Action</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Multi-Module Sub-Scores */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            <span>Digital Twin Evidence Dimensions</span>
          </h3>
          <Link href="/progress" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1">
            <span>Detailed Progress View</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[11px] text-slate-400 flex items-center gap-1"><Award className="w-3 h-3 text-indigo-400" /> Skills</span>
            <p className="text-lg font-bold text-white">{subScores?.skill_readiness ?? 0}%</p>
            <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
              <div className="bg-indigo-500 h-full" style={{ width: `${subScores?.skill_readiness ?? 0}%` }} />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[11px] text-slate-400 flex items-center gap-1"><FileText className="w-3 h-3 text-purple-400" /> ATS Resume</span>
            <p className="text-lg font-bold text-white">{subScores?.resume_readiness ?? 0}%</p>
            <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
              <div className="bg-purple-500 h-full" style={{ width: `${subScores?.resume_readiness ?? 0}%` }} />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[11px] text-slate-400 flex items-center gap-1"><Mic className="w-3 h-3 text-pink-400" /> Interview</span>
            <p className="text-lg font-bold text-white">{subScores?.interview_readiness ?? 0}%</p>
            <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
              <div className="bg-pink-500 h-full" style={{ width: `${subScores?.interview_readiness ?? 0}%` }} />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[11px] text-slate-400 flex items-center gap-1"><MapPin className="w-3 h-3 text-blue-400" /> Roadmap</span>
            <p className="text-lg font-bold text-white">{subScores?.roadmap_progress ?? 0}%</p>
            <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
              <div className="bg-blue-500 h-full" style={{ width: `${subScores?.roadmap_progress ?? 0}%` }} />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[11px] text-slate-400 flex items-center gap-1"><Briefcase className="w-3 h-3 text-emerald-400" /> Job Match</span>
            <p className="text-lg font-bold text-white">{subScores?.job_match_readiness ?? 0}%</p>
            <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full" style={{ width: `${subScores?.job_match_readiness ?? 0}%` }} />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[11px] text-slate-400 flex items-center gap-1"><Star className="w-3 h-3 text-amber-400" /> Portfolio</span>
            <p className="text-lg font-bold text-white">{subScores?.portfolio_readiness ?? 0}%</p>
            <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
              <div className="bg-amber-500 h-full" style={{ width: `${subScores?.portfolio_readiness ?? 0}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Strengths & Gaps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Verified Strengths */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Top Verified Strengths</span>
          </h3>

          {strengths.length > 0 ? (
            <div className="space-y-3">
              {strengths.slice(0, 4).map((str, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-200 text-sm">{str.name}</span>
                      {str.verified && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                    </div>
                    <p className="text-[11px] text-slate-500">{str.category} ? {str.level}</p>
                  </div>
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                    {str.proficiency}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic p-4 text-center">Complete skills assessment or upload resume to extract strengths.</p>
          )}
        </div>

        {/* Priority Gaps */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span>Priority Target Gaps</span>
          </h3>

          {gaps.length > 0 ? (
            <div className="space-y-3">
              {gaps.slice(0, 4).map((gap, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 text-sm">{gap.name}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      gap.priority === 'Critical' ? 'bg-red-500/20 text-red-400' :
                      gap.priority === 'High' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {gap.priority}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{gap.reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic p-4 text-center">No critical gaps recorded. Profile fully aligned.</p>
          )}
        </div>
      </div>

      {/* Critical Missing Skills Bar */}
      {criticalSkills.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Critical Skills to Acquire for {targetRole}</h3>
          <div className="flex flex-wrap gap-2">
            {criticalSkills.map((sk, i) => (
              <span key={i} className="px-3 py-1 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-semibold">
                {sk}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
