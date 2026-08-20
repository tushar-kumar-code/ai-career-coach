'use client';

import { useState, useEffect } from 'react';
import { Sparkles, Award, FileText, CheckCircle2, ShieldAlert, Loader2 } from 'lucide-react';
import { getSkillProfile, getAssessmentResult } from '@/lib/api-client';
import { SkillProfileData, AssessmentResultData } from '@/lib/types';

export default function DigitalTwinPage() {
  const [loading, setLoading] = useState(true);
  const [skillsProfile, setSkillsProfile] = useState<SkillProfileData | null>(null);
  const [assessmentData, setAssessmentData] = useState<AssessmentResultData | null>(null);

  useEffect(() => {
    async function loadDigitalTwin() {
      try {
        const [sData, aData] = await Promise.all([
          getSkillProfile(),
          getAssessmentResult()
        ]);
        setSkillsProfile(sData);
        setAssessmentData(aData);
      } catch (err) {
        console.error('Digital twin load error:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDigitalTwin();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Synchronizing Career Digital Twin...</p>
      </div>
    );
  }

  const targetRole = skillsProfile?.target_career || assessmentData?.selected_target_career || 'Software Developer';
  const archetype = assessmentData?.archetype || 'Systems Builder';
  const topMatch = assessmentData?.analysis?.recommended_careers?.[0]?.match_percentage || 85;

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center space-x-3 mb-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white">Career Digital Twin Profile</h1>
            <p className="text-xs text-slate-400">Continuously updated profile backed by verified multi-source evidence</p>
          </div>
        </div>
      </div>

      {/* Target & Archetype Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase">Target Career Role</span>
          <h2 className="text-xl font-bold text-white">{targetRole}</h2>
          <span className="inline-block px-2.5 py-1 rounded text-xs font-semibold bg-indigo-500/20 text-indigo-400">
            {topMatch}% Match Alignment
          </span>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase">Career Archetype</span>
          <h2 className="text-xl font-bold text-purple-400">{archetype}</h2>
          <p className="text-xs text-slate-400">Derived from 12-dimension Career Discovery evaluation.</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase">Verified Skill Signals</span>
          <h2 className="text-3xl font-extrabold text-emerald-400">
            {skillsProfile?.verified_count || 0}<span className="text-sm font-normal text-slate-400">/{skillsProfile?.total_skills_count || 0}</span>
          </h2>
          <p className="text-xs text-slate-400">Multi-source evidence backed skills.</p>
        </div>
      </div>

      {/* Evidence-Backed Skill Matrix */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
        <h3 className="text-lg font-bold text-white flex items-center space-x-2">
          <Award className="w-5 h-5 text-indigo-400" />
          <span>Evidence-Backed Skill Matrix ({skillsProfile?.strong_skills.length || 0} Strong)</span>
        </h3>

        {skillsProfile?.strong_skills && skillsProfile.strong_skills.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {skillsProfile.strong_skills.map((skill) => (
              <div key={skill.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-slate-200 text-sm">{skill.skill_name}</h4>
                  <span className="text-xs text-indigo-400 font-semibold">{skill.proficiency_level} ({skill.proficiency_percent}%)</span>
                </div>
                <p className="text-[11px] text-slate-400">Evidence Sources:</p>
                <div className="flex flex-wrap gap-2">
                  {skill.evidence_sources.map((src, idx) => (
                    <span key={idx} className="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>{src}</span>
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No verified skill matrix data yet. Upload resume or complete assessment.</p>
        )}
      </div>
    </div>
  );
}
