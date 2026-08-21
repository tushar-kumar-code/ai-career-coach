'use client';

import Link from 'next/link';


import { useState, useEffect } from 'react';
import { 
  Award, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  Loader2, 
  Target, 
  ShieldAlert, 
  TrendingUp, 
  RefreshCw,
  Info,
  X,
  FileText,
  Compass,
  ArrowRight
} from 'lucide-react';
import { getSkillProfile, recalculateSkills, getSkillDetails,
  focusSkillOnRoadmap
} from '@/lib/api-client';
import { SkillProfileData, UserSkill, SkillGap, SkillDetailData } from '@/lib/types';

export default function SkillsPage() {
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [profile, setProfile] = useState<SkillProfileData | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedSkillModal, setSelectedSkillModal] = useState<SkillDetailData | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  const [focusingSkill, setFocusingSkill] = useState<string | null>(null);
  const [focusFeedback, setFocusFeedback] = useState<{ skill: string; msg: string; status: string } | null>(null);

  const handleAddToTodayFocus = async (skillName: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setFocusingSkill(skillName);
    try {
      const res = await focusSkillOnRoadmap(skillName);
      setFocusFeedback({
        skill: skillName,
        msg: res.message || `Added ${skillName} to Today's Focus!`,
        status: res.status
      });
      setTimeout(() => setFocusFeedback(null), 5000);
    } catch (err: any) {
      console.error('Failed to focus skill:', err);
    } finally {
      setFocusingSkill(null);
    }
  };


  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await getSkillProfile();
      setProfile(data);
    } catch (err) {
      console.error('Failed to load skill profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    try {
      const updated = await recalculateSkills();
      setProfile(updated);
    } catch (err) {
      console.error('Recalculate error:', err);
    } finally {
      setRecalculating(false);
    }
  };

  const handleOpenSkillModal = async (skill: UserSkill) => {
    setModalLoading(true);
    try {
      const detail = await getSkillDetails(skill.id);
      setSelectedSkillModal(detail);
    } catch (err) {
      console.error('Skill details error:', err);
    } finally {
      setModalLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Evaluating Evidence-Based Skill Profile...</p>
      </div>
    );
  }

  const categories = [
    'All',
    'Programming Languages',
    'Web Development',
    'Databases',
    'AI/ML',
    'Cloud & DevOps',
    'Problem Solving & Analytical',
    'Professional & Leadership',
    'Technical'
  ];

  const filterByCat = (items: UserSkill[]) => {
    if (selectedCategory === 'All') return items;
    return items.filter(s => s.category.toLowerCase().includes(selectedCategory.toLowerCase()));
  };

  const filteredStrong = filterByCat(profile?.strong_skills || []);
  const filteredImprove = filterByCat(profile?.skills_to_improve || []);

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      
        {/* Focus Feedback Toast Alert */}
        {focusFeedback && (
          <div className="p-4 rounded-xl bg-indigo-950/80 border border-indigo-500/40 text-xs text-indigo-200 flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
              <span><strong>{focusFeedback.skill}:</strong> {focusFeedback.msg}</span>
            </div>
            <Link
              href="/roadmap"
              className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center space-x-1 shrink-0 ml-4 transition-colors"
            >
              <span>Open Roadmap Focus ?</span>
            </Link>
          </div>
        )}

        {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
            <Award className="w-4 h-4" />
            <span>Evidence-Based Skill Intelligence</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">Skill Matrix & Target Role Gap Analysis</h1>
          <p className="text-xs text-slate-400 mt-1">
            Target Career: <strong className="text-white font-semibold">{profile?.target_career || 'Software Developer'}</strong>
          </p>
        </div>
        <button
          onClick={handleRecalculate}
          disabled={recalculating}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/25 transition-all flex items-center space-x-2 shrink-0 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${recalculating ? 'animate-spin' : ''}`} />
          <span>{recalculating ? 'Syncing...' : 'Recalculate Profile'}</span>
        </button>
      </div>

      {/* Summary Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Profile Skills</span>
          <div className="text-3xl font-extrabold text-white">{profile?.total_skills_count || 0}</div>
          <p className="text-xs text-slate-400">Aggregated across all evidence</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Verified Confidence</span>
          <div className="text-3xl font-extrabold text-emerald-400">{profile?.verified_count || 0}</div>
          <p className="text-xs text-emerald-400/80 font-medium">Multi-source evidence backed</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Supported / Claimed</span>
          <div className="text-3xl font-extrabold text-indigo-400">
            {(profile?.supported_count || 0) + (profile?.claimed_count || 0)}
          </div>
          <p className="text-xs text-indigo-400/80 font-medium">Assessment & Resume claims</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Missing Target Skills</span>
          <div className="text-3xl font-extrabold text-amber-400">{profile?.missing_skills.length || 0}</div>
          <p className="text-xs text-amber-400/80 font-medium">Required for target role</p>
        </div>
      </div>

      {/* Category Pills Filter */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
              selectedCategory === cat
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Section 1: Strong Skills (Matched) */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span>Strong Skills (Matched Prerequisites)</span>
        </h2>

        {filteredStrong.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredStrong.map((skill) => (
              <div
                key={skill.id}
                onClick={() => handleOpenSkillModal(skill)}
                className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/40 transition-all cursor-pointer space-y-3 group"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-slate-200 text-sm group-hover:text-indigo-400 transition-colors">
                      {skill.skill_name}
                    </h3>
                    <span className="text-[11px] text-slate-400">{skill.category}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {skill.confidence_status}
                  </span>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Proficiency ({skill.proficiency_level})</span>
                    <span className="text-slate-200 font-semibold">{skill.proficiency_percent}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full" style={{ width: `${skill.proficiency_percent}%` }}></div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-900 pt-2">
                  <span>Target: {skill.target_required_level || 'Required'}</span>
                  <span className="text-indigo-400 font-medium group-hover:underline flex items-center space-x-1">
                    <span>View Evidence</span>
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No matched skills found for this category filter.</p>
        )}
      </div>

      {/* Section 2: Skills to Improve */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-indigo-400" />
          <span>Skills to Improve (Partially Matched / Weak)</span>
        </h2>

        {filteredImprove.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredImprove.map((skill) => (
              <div
                key={skill.id}
                onClick={() => handleOpenSkillModal(skill)}
                className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/40 transition-all cursor-pointer space-y-3 group"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-slate-200 text-sm group-hover:text-indigo-400 transition-colors">
                      {skill.skill_name}
                    </h3>
                    <span className="text-[11px] text-slate-400">{skill.category}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                    skill.priority === 'High'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                  }`}>
                    {skill.priority} Priority
                  </span>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Current ({skill.proficiency_level})</span>
                    <span className="text-slate-200 font-semibold">{skill.proficiency_percent}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full" style={{ width: `${skill.proficiency_percent}%` }}></div>
                  </div>
                </div>

                <p className="text-[11px] text-slate-400 line-clamp-1">{skill.priority_reason}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No skills to improve in this category.</p>
        )}
      </div>

      {/* Section 3: Missing Target Career Skills */}
      {profile?.missing_skills && profile.missing_skills.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span>Missing Target Career Skills ({profile.target_career})</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profile.missing_skills.map((gap, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-amber-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-200 text-sm">{gap.skill_name}</h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                    gap.priority === 'High' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {gap.priority} Priority Gap
                  </span>
                </div>
                <p className="text-xs text-slate-400">{gap.priority_reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Detail Modal */}
      {selectedSkillModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 relative shadow-2xl">
            <button
              onClick={() => setSelectedSkillModal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <div className="inline-flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
                <span>{selectedSkillModal.skill.category}</span>
              </div>
              <h2 className="text-xl font-bold text-white">{selectedSkillModal.skill.skill_name}</h2>
            </div>

            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div>
                <span className="text-[11px] text-slate-400 uppercase font-semibold">Proficiency</span>
                <div className="text-lg font-bold text-white">{selectedSkillModal.skill.proficiency_level}</div>
                <span className="text-xs text-slate-400">{selectedSkillModal.skill.proficiency_percent}% Score</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 uppercase font-semibold">System Confidence</span>
                <div className="text-lg font-bold text-indigo-400">{selectedSkillModal.skill.confidence_status}</div>
                <span className="text-xs text-slate-400">{selectedSkillModal.skill.confidence_score}% Confidence</span>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-200">Supporting Evidence Records</h3>
              {selectedSkillModal.evidence_records.length > 0 ? (
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {selectedSkillModal.evidence_records.map((ev) => (
                    <div key={ev.id} className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-xs space-y-1">
                      <div className="flex items-center justify-between text-indigo-400 font-semibold">
                        <span>Source: {ev.source}</span>
                        <span className="text-slate-500 font-normal">{ev.confidence_weight}% Weight</span>
                      </div>
                      <p className="text-slate-300">{ev.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No formal evidence records logged yet.</p>
              )}
            </div>

            <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 space-y-3">
              <div className="space-y-1">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Recommended Next Action</span>
                <p className="text-xs text-indigo-200 leading-relaxed">
                  {selectedSkillModal.recommended_next_action}
                </p>
              </div>
              <div className="pt-2 border-t border-indigo-500/20 flex items-center justify-between">
                <button
                  onClick={() => handleAddToTodayFocus(selectedSkillModal.skill.skill_name)}
                  disabled={focusingSkill === selectedSkillModal.skill.skill_name}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center space-x-1.5 disabled:opacity-50"
                >
                  <Target className="w-3.5 h-3.5" />
                  <span>{focusFeedback?.skill === selectedSkillModal.skill.skill_name ? focusFeedback.msg : "Add to Today's Focus ?"}</span>
                </button>
                <Link
                  href="/roadmap"
                  className="text-xs text-indigo-300 hover:text-white font-semibold flex items-center space-x-1"
                >
                  <span>View Roadmap</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}