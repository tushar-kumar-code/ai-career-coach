'use client';

import Link from 'next/link';


import { useState, useEffect } from 'react';
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
  RotateCcw
} from 'lucide-react';
import { 
  startAssessment, 
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
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active Session State
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

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
          // Start or resume session
          const activeSession = await startAssessment();
          setSession(activeSession);
          if (activeSession.is_completed) {
            handleCompleteAssessment(activeSession.session_id);
          }
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

  // Handle single question answer submission
  const handleAnswerSubmit = async () => {
    if (!session || !session.current_question || !selectedOption || submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      const updatedSession = await submitAnswer(
        session.session_id,
        session.current_question.id,
        selectedOption
      );

      setSelectedOption(null);
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

  // Restart Assessment Flow
  const handleRestart = async () => {
    setLoading(true);
    setResult(null);
    setCompareMatch(null);
    setSelectedOption(null);
    try {
      const newSession = await startAssessment();
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
              {analysis.interest_profile.map((interest, idx) => (
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
            {analysis.top_strengths.map((str, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <h4 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{str.strength_name}</span>
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed pl-6">{str.evidence_reason}</p>
              </div>
            ))}
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
                        {match.why_recommended.map((reason, rIdx) => (
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
  const currentQ = session?.current_question;
  const currentStep = session?.current_step || 1;
  const totalQ = session?.total_questions || 16;
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
            <span>Interactive Career Discovery Assessment</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            Question {currentStep} of {totalQ}: {currentQ?.dimension || 'General Discovery'}
          </h1>
        </div>
        <div className="sm:text-right shrink-0">
          <span className="text-xs text-slate-400 font-semibold">{progressPct}% Complete</span>
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
                Select the option that best matches your natural intuition and technical instincts.
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
                  onClick={() => setSelectedOption(option.id)}
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
          </div>

          {/* Action Footer */}
          <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Your response will calibrate your Career Digital Twin profile.
            </p>
            <button
              disabled={!selectedOption || submitting}
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
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <span>Next Question</span>
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