'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { getLocalizedQuestion } from '@/lib/assessment-translations';
import { 
  Compass, 
  CheckCircle2, 
  ArrowRight, 
  Brain, 
  Sparkles, 
  Loader2, 
  Award, 
  Target, 
  BookOpen, 
  Briefcase, 
  X, 
  ShieldCheck, 
  RotateCcw,
  Pencil,
  GraduationCap,
  Zap,
  Star
} from 'lucide-react';
import { 
  startAssessment,
  startAssessmentRetake,
  submitAnswer, 
  completeAssessment, 
  getAssessmentResult, 
  getCareerCatalog, 
  selectTargetCareer 
} from '@/lib/api-client';
import { 
  AssessmentSession, 
  AssessmentResultData, 
  CareerMatch, 
  CareerRoleCatalogItem 
} from '@/lib/types';

export default function AssessmentPage() {
  const { language, t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Level Selection Screen State
  const [showLevelSelect, setShowLevelSelect] = useState(false);
  const [userLevel, setUserLevel] = useState<string>('beginner');

  // Active Session State
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  // Custom Answer State
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customAnswerText, setCustomAnswerText] = useState('');

  // Result & Profile State
  const [result, setResult] = useState<AssessmentResultData | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [targetSuccessMsg, setTargetSuccessMsg] = useState<string | null>(null);

  // Career Comparison Modal State
  const [catalog, setCatalog] = useState<CareerRoleCatalogItem[]>([]);
  const [compareMatch, setCompareMatch] = useState<CareerMatch | null>(null);

  // Load existing result or initialize active assessment session
  useEffect(() => {
    async function init() {
      setLoading(true);
      setError(null);
      try {
        // Fetch career catalog for comparison modal
        const catData = await getCareerCatalog();
        setCatalog(catData);

        // Check if user already has completed result
        const existingResult = await getAssessmentResult();
        if (existingResult && existingResult.analysis) {
          setResult(existingResult);
          setSelectedTarget(existingResult.selected_target_career || null);
        } else {
          // Show level selection BEFORE starting the assessment
          setShowLevelSelect(true);
        }
      } catch (err: any) {
        console.error('Initialization error:', err);
        setError(err.message || 'Failed to connect to Career Discovery API');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Called after user picks their level
  const handleLevelConfirm = async (level: string) => {
    setUserLevel(level);
    setShowLevelSelect(false);
    setLoading(true);
    try {
      const activeSession = await startAssessment(level);
      setSession(activeSession);
      if (activeSession.is_completed) {
        handleCompleteAssessment(activeSession.session_id);
      }
    } catch (err: any) {
      console.error('Start error:', err);
      setError(err.message || 'Failed to start assessment');
    } finally {
      setLoading(false);
    }
  };

  // Handle single question answer submission
  const handleAnswerSubmit = async () => {
    const isCustom = selectedOption === 'custom';
    if (!session || !session.current_question || submitting) return;
    if (!selectedOption) return;
    if (isCustom && !customAnswerText.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const updatedSession = await submitAnswer(
        session.session_id,
        session.current_question.id,
        selectedOption,
        isCustom ? customAnswerText.trim() : undefined
      );

      setSelectedOption(null);
      setCustomAnswerText('');
      setShowCustomInput(false);
      setSession(updatedSession);

      // If assessment reached completion, trigger AI analysis
      if (updatedSession.is_completed || !updatedSession.current_question) {
        await handleCompleteAssessment(session.session_id);
      }
    } catch (err: any) {
      console.error('Answer submission error:', err);
      setError(err.message || 'Failed to record answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Trigger Gemini AI Discovery Analysis
  const handleCompleteAssessment = async (sessionId: string) => {
    setAnalyzing(true);
    setError(null);
    try {
      await completeAssessment(sessionId);
      const latestResult = await getAssessmentResult();
      if (latestResult) {
        setResult(latestResult);
        setSelectedTarget(latestResult.selected_target_career || null);
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to complete AI Career Analysis.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Restart Assessment Flow — show level picker again
  const handleRestart = async () => {
    setResult(null);
    setCompareMatch(null);
    setSelectedOption(null);
    setCustomAnswerText('');
    setShowCustomInput(false);
    setSession(null);
    setShowLevelSelect(true);
  };

  // Called when retake starts after level pick
  const handleRetakeWithLevel = async (level: string) => {
    setUserLevel(level);
    setShowLevelSelect(false);
    setLoading(true);
    try {
      const newSession = await startAssessmentRetake(level);
      setSession(newSession);
    } catch (err: any) {
      setError(err.message || 'Failed to restart assessment session.');
    } finally {
      setLoading(false);
    }
  };

  // Select and persist Target Career
  const handleSetTargetCareer = async (slug: string) => {
    try {
      const resp = await selectTargetCareer(slug);
      setSelectedTarget(resp.target_career);
      setTargetSuccessMsg(`Target Career set to ${resp.target_career}`);
      setTimeout(() => setTargetSuccessMsg(null), 4000);
    } catch (err: any) {
      console.error('Target career selection error:', err);
      setError(err.message || 'Failed to save target career.');
    }
  };

  // Loading Screen
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Loading Career Discovery Session...</p>
      </div>
    );
  }

  // ────────────────────────────────────────────────────
  // LEVEL SELECTION SCREEN
  // ────────────────────────────────────────────────────
  if (showLevelSelect) {
    const levels = [
      {
        id: 'beginner',
        icon: <GraduationCap className="w-7 h-7" />,
        color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/40',
        activeColor: 'from-emerald-600/30 to-teal-600/20 border-emerald-400 shadow-lg shadow-emerald-500/20',
        iconColor: 'text-emerald-400',
        badge: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30',
        label: '🌱 Beginner',
        sublabel: 'Student ya Fresher',
        desc: 'Maine abhi technology ke baare mein padhna shuru kiya hai ya explore kar raha/rahi hoon. Mujhe zyada technical cheezein nahi pata abhi.',
      },
      {
        id: 'intermediate',
        icon: <Zap className="w-7 h-7" />,
        color: 'from-indigo-500/20 to-purple-500/10 border-indigo-500/40',
        activeColor: 'from-indigo-600/30 to-purple-600/20 border-indigo-400 shadow-lg shadow-indigo-500/20',
        iconColor: 'text-indigo-400',
        badge: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/30',
        label: '⚡ Intermediate',
        sublabel: '1–3 saal ka experience',
        desc: 'Mujhe thodi coding/tech aati hai. Maine kuch projects ya internship kar liye hain. Basic cheezein samajhta/samajhti hoon.',
      },
      {
        id: 'advanced',
        icon: <Star className="w-7 h-7" />,
        color: 'from-amber-500/20 to-orange-500/10 border-amber-500/40',
        activeColor: 'from-amber-600/30 to-orange-600/20 border-amber-400 shadow-lg shadow-amber-500/20',
        iconColor: 'text-amber-400',
        badge: 'text-amber-300 bg-amber-500/10 border-amber-500/30',
        label: '🌟 Advanced',
        sublabel: '3+ saal ka experience',
        desc: 'Main professionally kaam kar raha/rahi hoon ya mujhe tech mein deep knowledge hai. Main technical questions comfortable feel karta/karti hoon.',
      },
    ];

    return (
      <div className="max-w-2xl mx-auto space-y-8 pb-12 pt-4">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold uppercase tracking-widest">
            <Compass className="w-3.5 h-3.5" />
            <span>Career Discovery Assessment</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white leading-tight">
            Aap abhi kahan hain?
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
            Apna current experience level batao taaki hum aapke liye <strong className="text-slate-200">bilkul sahi sawal</strong> taiyaar kar sakein — easy aur relatable.
          </p>
        </div>

        {/* Level Cards */}
        <div className="space-y-4">
          {levels.map((lvl) => {
            const isActive = userLevel === lvl.id;
            return (
              <button
                key={lvl.id}
                onClick={() => setUserLevel(lvl.id)}
                className={`w-full text-left p-5 rounded-2xl border bg-gradient-to-r transition-all duration-200 flex items-start space-x-5 ${
                  isActive ? lvl.activeColor : lvl.color + ' hover:opacity-90'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${isActive ? 'bg-white/10' : 'bg-slate-900/50'} ${lvl.iconColor}`}>
                  {lvl.icon}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-base font-bold text-white">{lvl.label}</span>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${lvl.badge}`}>{lvl.sublabel}</span>
                    {isActive && <CheckCircle2 className="w-4 h-4 text-white ml-auto" />}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{lvl.desc}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Confirm Button */}
        <button
          onClick={() => handleLevelConfirm(userLevel)}
          className="w-full py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-base flex items-center justify-center space-x-3 shadow-xl shadow-indigo-500/25 transition-all"
        >
          <span>Assessment Shuru Karein</span>
          <ArrowRight className="w-5 h-5" />
        </button>

        <p className="text-center text-xs text-slate-600">
          Level baad mein bhi change kiya ja sakta hai — Retake Assessment se.
        </p>
      </div>
    );
  }

  // Gemini AI Analysis Screen
  if (analyzing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 text-center max-w-lg mx-auto p-8 rounded-2xl bg-slate-900/80 border border-slate-800">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
          <Sparkles className="w-8 h-8 animate-pulse text-indigo-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white mb-2">Analyzing Your Career Discovery Profile</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Gemini AI is evaluating your problem solving, logical reasoning, and work style preferences against our 12 structured career role frameworks...
          </p>
        </div>
        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 h-full w-[80%] animate-pulse"></div>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // PHASE 2: RESULTS & CAREER PROFILE VIEW
  // ----------------------------------------------------
  if (result && result.analysis) {
    const { analysis } = result;
    const catalogMap = new Map(catalog.map((c) => [c.slug, c]));
    const matchedCatalogDetails = compareMatch ? catalogMap.get(compareMatch.slug) : null;

    return (
      <div className="max-w-5xl mx-auto space-y-8 pb-12">
        {/* Banner Alert for Target Career Selection */}
        {targetSuccessMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span className="font-semibold">{targetSuccessMsg}</span>
          </div>
        )}

          {/* Transition 1: Assessment -> Resume Action Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-indigo-950/70 border border-emerald-500/30 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div className="space-y-1.5">
              <div className="flex items-center space-x-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Career Discovery Complete ??
                </span>
                {selectedTarget && (
                  <span className="text-xs text-slate-300 font-semibold">
                    Target: <strong className="text-white">{selectedTarget}</strong>
                  </span>
                )}
              </div>
              <h3 className="text-lg font-bold text-white">Next Step: Upload & Scan Your Resume</h3>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                Upload your resume to verify your skills against ATS hiring standards for {selectedTarget || 'your target career'} and synchronize verified evidence with your Digital Twin.
              </p>
            </div>
            <Link
              href="/resume"
              className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm flex items-center justify-center space-x-2 shrink-0 transition-all shadow-lg shadow-emerald-600/30 self-start md:self-auto"
            >
              <span>Upload Resume ?</span>
            </Link>
          </div>


        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
            {error}
          </div>
        )}

        {/* Top Header */}
        <div className="p-8 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900 border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Career Discovery Profile Active</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white">Your AI Career Discovery Profile</h1>
            <p className="text-slate-300 text-xs mt-1">
              Evidence-backed career evaluation powered by Gemini AI. You remain in complete control of your target career selection.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={handleRestart}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-semibold text-xs transition-all flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4 text-slate-400" />
              <span>Retake Assessment</span>
            </button>
          </div>
        </div>

        {/* Career Archetype & Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Career Archetype</span>
            <h2 className="text-2xl font-bold text-indigo-400">{analysis.primary_archetype}</h2>
            <p className="text-xs text-slate-400 leading-relaxed">{analysis.work_style_summary}</p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Motivation & Driver</span>
            <p className="text-sm font-semibold text-slate-200">{analysis.motivation_profile}</p>
            <div className="flex flex-wrap gap-1.5 pt-2">
              {(analysis.interest_profile ?? []).map((interest, idx) => (
                <span key={idx} className="px-2.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300">
                  {interest}
                </span>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Current Selected Target</span>
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-emerald-400 shrink-0" />
              <h2 className="text-xl font-bold text-white">{selectedTarget || 'None Selected'}</h2>
            </div>
            <p className="text-xs text-slate-400">
              {selectedTarget ? 'Persisted in your Career Profile' : 'Select a target career below'}
            </p>
          </div>
        </div>

        {/* Verified Strengths Section */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <Award className="w-5 h-5 text-indigo-400" />
            <span>Top Supporting Strengths</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(analysis.top_strengths ?? []).length > 0 ? (analysis.top_strengths ?? []).map((str, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <h4 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{str.strength_name}</span>
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed pl-6">{str.evidence_reason}</p>
              </div>
            )) : (
              <p className="text-xs text-slate-500 italic">Strengths will be available after full assessment completion.</p>
            )}
          </div>
        </div>

        {/* Top Recommended Career Matches */}
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight">Your Top Career Matches</h2>
            <p className="text-xs text-slate-400 mt-1">
              Ranked recommendations based on your logical reasoning, work style, and technology preferences.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {analysis.recommended_careers.map((match) => {
              const isSelected = selectedTarget === match.title;
              return (
                <div
                  key={match.slug}
                  className={`p-6 rounded-2xl border transition-all space-y-5 flex flex-col justify-between ${
                    isSelected
                      ? 'bg-indigo-950/30 border-indigo-500 shadow-lg shadow-indigo-500/10'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xl font-bold text-white flex items-center space-x-2">
                        <span>{match.title}</span>
                        {isSelected && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 uppercase">
                            Target
                          </span>
                        )}
                      </h3>
                      <div className="text-right">
                        <span className="px-3 py-1 rounded-lg text-sm font-extrabold bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">
                          {match.match_percentage}% Match
                        </span>
                      </div>
                    </div>

                    {/* Progress match bar */}
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full"
                        style={{ width: `${match.match_percentage}%` }}
                      ></div>
                    </div>

                    {/* Supporting Reasons */}
                    <div className="space-y-1.5 pt-2">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Why Recommended:</span>
                      <ul className="space-y-1">
                        {(match.why_recommended ?? []).map((reason: string, rIdx: number) => (
                          <li key={rIdx} className="text-xs text-slate-300 flex items-start space-x-2">
                            <span className="text-indigo-400 font-bold">•</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Card Action Buttons */}
                  <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between gap-3">
                    <button
                      onClick={() => setCompareMatch(match)}
                      className="flex-1 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 transition-all flex items-center justify-center space-x-2"
                    >
                      <BookOpen className="w-4 h-4 text-purple-400" />
                      <span>Explore & Compare</span>
                    </button>

                    <button
                      onClick={() => handleSetTargetCareer(match.slug)}
                      className={`px-4 py-2.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                        isSelected
                          ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/20'
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <ShieldCheck className="w-4 h-4" />
                          <span>Active Target</span>
                        </>
                      ) : (
                        <>
                          <Target className="w-4 h-4" />
                          <span>Set Target</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* CAREER COMPARISON MODAL */}
        {compareMatch && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <span className="text-xs text-indigo-400 font-bold uppercase tracking-wider">Career Role Detailed Comparison</span>
                  <h3 className="text-2xl font-bold text-white flex items-center space-x-3 mt-1">
                    <span>{compareMatch.title}</span>
                    <span className="px-2.5 py-0.5 rounded text-xs font-extrabold bg-indigo-500/20 text-indigo-300">
                      {compareMatch.match_percentage}% Match
                    </span>
                  </h3>
                </div>
                <button
                  onClick={() => setCompareMatch(null)}
                  className="p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {matchedCatalogDetails && (
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-4 rounded-xl border border-slate-800">
                  {matchedCatalogDetails.description}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Required Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(matchedCatalogDetails?.required_skills || compareMatch.supporting_strengths).map((sk, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-slate-200 font-medium">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Target Learning Gaps</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {compareMatch.learning_gaps.map((gap, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 font-medium">
                        {gap}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {matchedCatalogDetails?.responsibilities && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Typical Role Responsibilities</h4>
                  <ul className="space-y-1.5">
                    {matchedCatalogDetails.responsibilities.map((resp, idx) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
                        <span className="text-indigo-400 font-bold">•</span>
                        <span>{resp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-4">
                <button
                  onClick={() => setCompareMatch(null)}
                  className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-all"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    handleSetTargetCareer(compareMatch.slug);
                    setCompareMatch(null);
                  }}
                  className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-lg shadow-indigo-500/25 flex items-center space-x-2"
                >
                  <Target className="w-4 h-4" />
                  <span>Select as My Target Career</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ----------------------------------------------------
  // PHASE 1: INTERACTIVE QUESTION ASSESSMENT FLOW
  // ----------------------------------------------------
  const currentQ = getLocalizedQuestion(session?.current_question, language);
  const currentStep = session?.current_step || 1;
  const totalQ = session?.total_questions || 12;
  const progressPct = Math.min(100, Math.round(((currentStep - 1) / totalQ) * 100));

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-6 rounded-2xl bg-slate-900/60 border border-slate-800 gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
            <Compass className="w-4 h-4" />
            <span>{t('assessment.title', 'Interactive Career Discovery Assessment')}</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            {t('assessment.questionStep', 'Question')} {currentStep} {t('assessment.of', 'of')} {totalQ}: {currentQ?.dimension || 'General Discovery'}
          </h1>
        </div>
        <div className="sm:text-right shrink-0">
          <span className="text-xs text-slate-400 font-semibold">{progressPct}% {t('common.active', 'Complete')}</span>
          <div className="w-44 bg-slate-800 h-2.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 h-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100 leading-relaxed">
                {currentQ.question_text}
              </h2>
              <p className="text-xs text-slate-400 mt-2">
                {t('assessment.instruction', 'Please select the option that best describes your instinctual approach:')}
              </p>
            </div>
          </div>

          {/* Options List */}
          <div className="space-y-3 pt-2">
            {currentQ.options.map((option) => {
              const isSelected = selectedOption === option.id;
              return (
                <button
                  key={option.id}
                  onClick={() => {
                    setSelectedOption(option.id);
                    setShowCustomInput(false);
                    setCustomAnswerText('');
                  }}
                  disabled={submitting}
                  className={`w-full text-left p-4 rounded-xl border transition-all duration-200 flex items-center justify-between ${
                    isSelected
                      ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <span
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                        isSelected ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {option.id}
                    </span>
                    <span className="text-sm font-medium leading-relaxed">{option.text}</span>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="w-5 h-5 text-indigo-400 shrink-0 ml-2" />
                  )}
                </button>
              );
            })}

            {/* Custom Answer Option */}
            <div className="mt-1">
              <button
                onClick={() => {
                  const next = !showCustomInput;
                  setShowCustomInput(next);
                  if (next) {
                    setSelectedOption('custom');
                  } else {
                    setSelectedOption(null);
                    setCustomAnswerText('');
                  }
                }}
                disabled={submitting}
                className={`w-full text-left p-4 rounded-xl border transition-all duration-200 flex items-center space-x-4 ${
                  selectedOption === 'custom'
                    ? 'bg-purple-600/20 border-purple-500 text-white shadow-md shadow-purple-500/10'
                    : 'bg-slate-950/60 border-slate-700 border-dashed text-slate-400 hover:border-slate-500 hover:text-slate-300'
                }`}
              >
                <span className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                  selectedOption === 'custom' ? 'bg-purple-500 text-white' : 'bg-slate-800 text-slate-400'
                }`}>
                  <Pencil className="w-4 h-4" />
                </span>
                <span className="text-sm font-medium">Koi option suit nahi karta? Apna khud ka jawab likhein</span>
                {selectedOption === 'custom' && <CheckCircle2 className="w-5 h-5 text-purple-400 shrink-0 ml-auto" />}
              </button>

              {showCustomInput && (
                <div className="mt-3 space-y-2">
                  <textarea
                    value={customAnswerText}
                    onChange={(e) => setCustomAnswerText(e.target.value)}
                    placeholder="Yahan apna jawab likhein... (jaise: 'Mujhe graphic design mein zyada interest hai' ya 'Main gaming apps banana chahta hoon')"
                    rows={3}
                    disabled={submitting}
                    className="w-full p-4 rounded-xl bg-slate-950 border border-purple-500/40 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-purple-400 resize-none transition-all"
                  />
                  <p className="text-[11px] text-slate-600 pl-1">Aapka jawab AI ko aapke career ko better samajhne mein madad karega.</p>
                </div>
              )}
            </div>
          </div>

          {/* Action Footer */}
          <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Your response will calibrate your Career Digital Twin profile.
            </p>
            <button
              disabled={!selectedOption || (selectedOption === 'custom' && !customAnswerText.trim()) || submitting}
              onClick={handleAnswerSubmit}
              className={`px-6 py-3 rounded-xl font-semibold text-sm flex items-center space-x-2 transition-all ${
                selectedOption && !submitting
                  ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t('assessment.submitting', 'Recording Answer...')}</span>
                </>
              ) : (
                <>
                  <span>
                    {currentStep === totalQ
                      ? t('assessment.submitBtn', 'Complete Assessment & Generate AI Analysis ✨')
                      : t('assessment.nextBtn', 'Next Question →')}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}