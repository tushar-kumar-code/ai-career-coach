'use client';

import { Suspense, useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Dumbbell,
  Sparkles,
  Play,
  ChevronRight,
  CheckCircle2,
  TrendingUp,
  Target,
  Zap,
  ArrowRight,
  RotateCcw,
  HelpCircle,
  AlertCircle,
  Star,
  Layers
} from 'lucide-react';
import {
  getPracticeSuggestions,
  startMicroPractice,
  submitInterviewAnswer,
  nextInterviewQuestion,
  completeInterviewSession,
  getInterviewReadiness
} from '@/lib/api-client';
import {
  PracticeSuggestion,
  InterviewSessionData,
  InterviewEvaluationData,
  InterviewFinalReportData,
  STARAnalysisData
} from '@/lib/types';

type PracticeView = 'suggestions' | 'session' | 'complete';

export default function PracticePage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center max-w-4xl mx-auto">
          <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading practice session...</p>
        </div>
      }
    >
      <PracticeContent />
    </Suspense>
  );
}

function PracticeContent() {
  const searchParams = useSearchParams();
  const topicParam = searchParams.get('topic');

  const [view, setView] = useState<PracticeView>('suggestions');
  const [suggestions, setSuggestions] = useState<PracticeSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingTopic, setStartingTopic] = useState<string | null>(null);

  // Session states
  const [session, setSession] = useState<InterviewSessionData | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluating, setEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState<InterviewEvaluationData | null>(null);
  const [finalReport, setFinalReport] = useState<InterviewFinalReportData | null>(null);
  const [activeTopic, setActiveTopic] = useState('');

  useEffect(() => {
    loadSuggestions();
  }, []);

  // Auto-start if topic query param is provided
  useEffect(() => {
    if (topicParam && suggestions.length === 0 && !loading) {
      handleStartPractice(topicParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicParam, loading]);

  async function loadSuggestions() {
    setLoading(true);
    try {
      const s = await getPracticeSuggestions();
      setSuggestions(s);
    } finally {
      setLoading(false);
    }
  }

  async function handleStartPractice(topic: string) {
    setStartingTopic(topic);
    setActiveTopic(topic);
    try {
      const newSession = await startMicroPractice(topic);
      setSession(newSession);
      setUserAnswer('');
      setEvaluation(null);
      setView('session');
    } catch (err) {
      console.error('Failed to start micro practice:', err);
    } finally {
      setStartingTopic(null);
    }
  }

  async function handleSubmitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!session || !userAnswer.trim()) return;
    setEvaluating(true);
    try {
      const ev = await submitInterviewAnswer(session.id, userAnswer);
      setEvaluation(ev);
    } catch (err) {
      console.error('Failed to evaluate:', err);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleNext() {
    if (!session) return;
    setEvaluating(true);
    try {
      const updated = await nextInterviewQuestion(session.id);
      if (updated.is_completed) {
        const report = await completeInterviewSession(session.id);
        setFinalReport(report);
        setView('complete');
      } else {
        setSession(updated);
        setUserAnswer('');
        setEvaluation(null);
      }
    } catch (err) {
      console.error('Failed to advance:', err);
    } finally {
      setEvaluating(false);
    }
  }

  function getStarStatusColor(status?: string) {
    switch (status) {
      case 'Good': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'Needs Clarity': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'Missing': return 'text-red-400 bg-red-500/10 border-red-500/30';
      default: return 'text-slate-500 bg-slate-800 border-slate-700';
    }
  }

  function getStarStatusIcon(status?: string) {
    switch (status) {
      case 'Good': return '✓';
      case 'Needs Clarity': return '⚠';
      case 'Missing': return '✗';
      default: return '—';
    }
  }

  function getPriorityColor(priority: string) {
    switch (priority) {
      case 'High': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'Medium': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default: return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  }

  function getSourceLabel(source: string) {
    switch (source) {
      case 'interview_weakness': return '🎯 Interview Weak Area';
      case 'skill_gap': return '📊 Skill Gap';
      case 'roadmap_task': return '🗺 Roadmap Task';
      default: return source;
    }
  }

  const hasStar = (ev: InterviewEvaluationData) =>
    ev.star_analysis && ev.star_analysis.situation_status && ev.star_analysis.situation_status !== 'Not Applicable';

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-12">
      {/* Page Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-violet-950/60 via-slate-900 to-indigo-950/60 border border-violet-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <Dumbbell className="w-5 h-5 text-violet-400" />
              <span className="text-xs font-bold text-violet-400 uppercase tracking-wider">Micro Practice Mode</span>
            </div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Skill Practice Engine</h1>
            <p className="text-xs text-slate-400 mt-1">
              3 focused questions per session · Instant AI evaluation · STAR coaching for behavioral answers
            </p>
          </div>
          {view !== 'suggestions' && (
            <button
              onClick={() => { setView('suggestions'); setSession(null); setEvaluation(null); setFinalReport(null); }}
              className="text-xs font-semibold text-slate-400 hover:text-white flex items-center space-x-1 border border-slate-700 px-3 py-1.5 rounded-lg hover:border-slate-500 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Choose Different Topic</span>
            </button>
          )}
        </div>
      </div>

      {/* ===== VIEW 1: Topic Suggestions ===== */}
      {view === 'suggestions' && (
        <div className="space-y-6">
          {loading ? (
            <div className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
              <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-slate-400 text-sm">Analyzing your skill gaps & recent interview performance…</p>
            </div>
          ) : (
            <>
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold text-white flex items-center space-x-2">
                    <Target className="w-4 h-4 text-violet-400" />
                    <span>Recommended Practice Topics</span>
                  </h2>
                  <span className="text-[11px] text-slate-500">Based on your skill profile & interview history</span>
                </div>

                {suggestions.length === 0 ? (
                  <div className="p-6 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    <p>No personalized suggestions yet.</p>
                    <p className="text-xs mt-1">Complete your skill assessment or a mock interview to get recommendations.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {suggestions.map((s, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-violet-500/40 transition-all group flex flex-col justify-between space-y-3"
                      >
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <h3 className="text-sm font-bold text-white leading-tight">{s.topic}</h3>
                            <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded border ${getPriorityColor(s.priority)}`}>
                              {s.priority}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 leading-relaxed">{s.reason}</p>
                          <div className="mt-2 text-[10px] text-slate-600 font-medium">{getSourceLabel(s.source)}</div>
                        </div>

                        <button
                          onClick={() => handleStartPractice(s.topic)}
                          disabled={startingTopic === s.topic}
                          id={`practice-btn-${idx}`}
                          className="w-full py-2 px-4 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs transition-all flex items-center justify-center space-x-1.5 disabled:opacity-60 shadow-md shadow-violet-500/20"
                        >
                          {startingTopic === s.topic ? (
                            <>
                              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                              <span>Starting…</span>
                            </>
                          ) : (
                            <>
                              <Play className="w-3.5 h-3.5 fill-white" />
                              <span>Practice {s.topic} →</span>
                            </>
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Custom topic input */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>Practice Any Topic</span>
                </h2>
                <CustomTopicForm onStart={handleStartPractice} loading={!!startingTopic} />
              </div>
            </>
          )}
        </div>
      )}

      {/* ===== VIEW 2: Practice Session ===== */}
      {view === 'session' && session && session.current_question && (
        <div className="space-y-6">
          {/* Session Progress */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center space-x-3">
              <span className="px-2.5 py-1 rounded-full bg-violet-500/20 text-violet-300 text-xs font-bold border border-violet-500/30">
                Q {session.current_question_index + 1} / {session.question_count}
              </span>
              <span className="text-xs text-slate-400 font-medium">Topic: <strong className="text-white">{activeTopic}</strong></span>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-800 text-slate-300">{session.current_question.category}</span>
            </div>
            <div className="flex items-center space-x-2">
              {[...Array(session.question_count)].map((_, i) => (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full ${i < session.current_question_index ? 'bg-emerald-400' : i === session.current_question_index ? 'bg-violet-400' : 'bg-slate-700'}`}
                />
              ))}
            </div>
          </div>

          {/* Question Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
              <h2 className="text-base font-bold text-white leading-relaxed">
                "{session.current_question.question_text}"
              </h2>
              {session.current_question.context_tip && (
                <p className="text-xs text-violet-400 font-medium flex items-center space-x-1.5 pt-2">
                  <HelpCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>Tip: {session.current_question.context_tip}</span>
                </p>
              )}
              {/* STAR tip for Behavioral */}
              {session.current_question.category === 'Behavioral' && !evaluation && (
                <div className="mt-3 p-3 rounded-lg bg-violet-950/40 border border-violet-500/20 text-[11px] text-violet-300">
                  <strong>STAR Structure:</strong> Start with the <em>Situation</em>, your <em>Task</em>, what <em>Actions</em> YOU took, and the <em>Result</em>.
                </div>
              )}
            </div>

            {/* Answer form */}
            {!evaluation && (
              <form onSubmit={handleSubmitAnswer} className="space-y-4">
                <textarea
                  rows={5}
                  value={userAnswer}
                  onChange={e => setUserAnswer(e.target.value)}
                  placeholder="Type your answer here. Be specific and include concrete examples…"
                  className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:border-violet-500 focus:outline-none transition-all placeholder:text-slate-600 resize-none"
                />
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={evaluating || !userAnswer.trim()}
                    className="px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-2 transition-all disabled:opacity-50 shadow-lg shadow-violet-500/20"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{evaluating ? 'Evaluating with AI…' : 'Submit & Get Feedback'}</span>
                  </button>
                </div>
              </form>
            )}

            {/* Evaluation Feedback */}
            {evaluation && (
              <div className="space-y-5">
                {/* Score Banner */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-violet-500/30">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl font-extrabold text-white">{evaluation.score}%</div>
                    <div className="text-xs text-slate-400">Overall Score</div>
                  </div>
                  <div className="grid grid-cols-5 gap-2 text-center">
                    {[
                      { label: 'Tech', val: evaluation.technical_score },
                      { label: 'Comm', val: evaluation.communication_score },
                      { label: 'P.S.', val: evaluation.problem_solving_score },
                      { label: 'Behav', val: evaluation.behavioral_score },
                      { label: 'Resume', val: evaluation.resume_knowledge_score }
                    ].map(({ label, val }) => (
                      <div key={label} className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                        <div className="text-[9px] text-slate-500 uppercase font-semibold">{label}</div>
                        <div className="text-xs font-bold text-white">{val}%</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ===== STAR Coaching Section ===== */}
                {hasStar(evaluation) && evaluation.star_analysis && (
                  <div className="p-5 rounded-xl bg-violet-950/30 border border-violet-500/25 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                        <Star className="w-4 h-4 text-violet-400" />
                        <span>STAR Method Breakdown</span>
                      </h3>
                      <div className="flex items-center space-x-1.5">
                        <span className="text-[10px] text-slate-400">Score:</span>
                        <span className="text-xs font-extrabold text-violet-300">{evaluation.star_analysis.star_score ?? 0}%</span>
                        {evaluation.star_analysis.star_complete && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 font-bold">Complete ✓</span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[
                        { key: 'S', label: 'Situation', status: evaluation.star_analysis.situation_status, feedback: evaluation.star_analysis.situation_feedback },
                        { key: 'T', label: 'Task', status: evaluation.star_analysis.task_status, feedback: evaluation.star_analysis.task_feedback },
                        { key: 'A', label: 'Action', status: evaluation.star_analysis.action_status, feedback: evaluation.star_analysis.action_feedback },
                        { key: 'R', label: 'Result', status: evaluation.star_analysis.result_status, feedback: evaluation.star_analysis.result_feedback },
                      ].map(comp => (
                        <div key={comp.key} className="space-y-1.5">
                          <div className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-bold ${getStarStatusColor(comp.status ?? undefined)}`}>
                            <span>{comp.key} — {comp.label}</span>
                            <span className="text-sm">{getStarStatusIcon(comp.status ?? undefined)}</span>
                          </div>
                          {comp.feedback && (
                            <p className="text-[10px] text-slate-400 leading-relaxed px-0.5">{comp.feedback}</p>
                          )}
                        </div>
                      ))}
                    </div>

                    {!evaluation.star_analysis.star_complete && (
                      <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-500/20 text-[11px] text-amber-300">
                        <strong>💡 Next time:</strong> Make sure your answer includes all 4 STAR components — especially the <strong>Result</strong>. Even a brief outcome like "the bug was resolved" or "load time improved by 30%" counts!
                      </div>
                    )}
                  </div>
                )}

                {/* Strengths & Weaknesses */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {evaluation.strengths.length > 0 && (
                    <div className="space-y-1.5">
                      <h4 className="font-bold text-emerald-400 uppercase tracking-wider text-[10px]">✓ What You Did Well</h4>
                      {evaluation.strengths.map((s, i) => (
                        <p key={i} className="text-slate-300 leading-relaxed">• {s}</p>
                      ))}
                    </div>
                  )}
                  {evaluation.weaknesses.length > 0 && (
                    <div className="space-y-1.5">
                      <h4 className="font-bold text-amber-400 uppercase tracking-wider text-[10px]">⚠ What to Improve</h4>
                      {evaluation.weaknesses.map((w, i) => (
                        <p key={i} className="text-slate-300 leading-relaxed">• {w}</p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Coach Recommendation */}
                <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-300">
                  <strong>Coach Says:</strong> {evaluation.suggested_improvement}
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleNext}
                    disabled={evaluating}
                    className="px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-2 transition-all disabled:opacity-50"
                  >
                    <span>Next Question</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ===== VIEW 3: Completion Report ===== */}
      {view === 'complete' && finalReport && (
        <div className="space-y-6">
          {/* Score Banner */}
          <div className="p-8 rounded-2xl bg-gradient-to-r from-violet-950/60 via-slate-900 to-indigo-950/60 border border-violet-500/20 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-violet-400" />
            </div>
            <div>
              <p className="text-xs font-bold text-violet-400 uppercase tracking-wider">Practice Session Complete</p>
              <h2 className="text-3xl font-extrabold text-white mt-1">{finalReport.overall_score}%</h2>
              <p className="text-sm text-slate-400 mt-1">Topic: <strong className="text-white">{activeTopic}</strong></p>
            </div>
            <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl border border-slate-700 bg-slate-900/60">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-semibold text-slate-300">{finalReport.readiness_status}</span>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* What you did well */}
            <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/20 space-y-3">
              <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>What You Did Well</span>
              </h3>
              <ul className="space-y-1.5">
                {finalReport.strong_areas.slice(0, 3).map((s, i) => (
                  <li key={i} className="text-xs text-slate-300">✓ {s}</li>
                ))}
                {finalReport.strong_areas.length === 0 && (
                  <li className="text-xs text-slate-500 italic">Complete more questions to surface strengths.</li>
                )}
              </ul>
            </div>

            {/* What to improve */}
            <div className="p-5 rounded-2xl bg-amber-950/30 border border-amber-500/20 space-y-3">
              <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                <Target className="w-3.5 h-3.5" />
                <span>What to Improve</span>
              </h3>
              <ul className="space-y-1.5">
                {finalReport.weak_areas.slice(0, 3).map((w, i) => (
                  <li key={i} className="text-xs text-slate-300">⚠ {w}</li>
                ))}
                {finalReport.weak_areas.length === 0 && (
                  <li className="text-xs text-slate-500 italic">Great session — no major weak areas found!</li>
                )}
              </ul>
            </div>

            {/* What's next */}
            <div className="p-5 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 space-y-3">
              <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center space-x-1.5">
                <ArrowRight className="w-3.5 h-3.5" />
                <span>What's Next</span>
              </h3>
              <ul className="space-y-1.5">
                {finalReport.recommended_roadmap_topics.slice(0, 3).map((t, i) => (
                  <li key={i} className="text-xs text-slate-300">→ {t}</li>
                ))}
                {finalReport.recommended_roadmap_topics.length === 0 && (
                  <li className="text-xs text-slate-300">→ Try a full Mock Interview session to validate your skills</li>
                )}
              </ul>
            </div>
          </div>

          {/* Q&A Review */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-slate-400" />
              <span>Question-by-Question Review</span>
            </h3>
            <div className="space-y-3">
              {finalReport.questions_review.map((q, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200 text-sm">Q{idx + 1}: {q.question_text}</span>
                    <span className={`text-xs font-extrabold ${(q.score || 0) >= 75 ? 'text-emerald-400' : (q.score || 0) >= 55 ? 'text-amber-400' : 'text-red-400'}`}>
                      {q.score || 0}%
                    </span>
                  </div>
                  {q.user_answer && (
                    <p className="text-slate-500 italic text-[11px]">Your answer: "{q.user_answer.slice(0, 120)}{q.user_answer.length > 120 ? '…' : ''}"</p>
                  )}
                  {q.evaluation && (
                    <p className="text-indigo-300 font-medium text-[11px]">💡 {q.evaluation.suggested_improvement}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => handleStartPractice(activeTopic)}
              className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-lg shadow-violet-500/20"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Practice Again ({activeTopic})</span>
            </button>
            <button
              onClick={() => { setView('suggestions'); setFinalReport(null); setSession(null); }}
              className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center space-x-2 transition-all border border-slate-700"
            >
              <Dumbbell className="w-4 h-4" />
              <span>Choose Different Topic</span>
            </button>
            <a
              href="/roadmap"
              className="px-6 py-3 rounded-xl bg-indigo-800/60 hover:bg-indigo-700/60 text-indigo-200 font-bold text-sm flex items-center justify-center space-x-2 transition-all border border-indigo-500/30"
            >
              <ArrowRight className="w-4 h-4" />
              <span>Continue Roadmap Tasks</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

// Custom Topic Input sub-component
function CustomTopicForm({ onStart, loading }: { onStart: (topic: string) => void; loading: boolean }) {
  const [topic, setTopic] = useState('');
  return (
    <form
      onSubmit={e => {
        e.preventDefault();
        if (topic.trim()) onStart(topic.trim());
      }}
      className="flex flex-col sm:flex-row gap-3"
    >
      <input
        type="text"
        value={topic}
        onChange={e => setTopic(e.target.value)}
        placeholder="Enter any topic (e.g. SQL Joins, REST API Design, Python Decorators…)"
        className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:border-violet-500 focus:outline-none transition-all placeholder:text-slate-600"
        id="practice-custom-topic"
      />
      <button
        type="submit"
        disabled={!topic.trim() || loading}
        className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5 disabled:opacity-50 transition-all"
      >
        <Play className="w-3.5 h-3.5 fill-white" />
        <span>Start Practice</span>
      </button>
    </form>
  );
}
