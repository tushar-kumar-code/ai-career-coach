'use client';

import { useEffect, useState } from 'react';
import { 
  Mic, 
  MicOff, 
  Send, 
  Sparkles, 
  AlertCircle, 
  Play, 
  CheckCircle2, 
  Award, 
  TrendingUp, 
  Clock, 
  Layers, 
  RotateCcw, 
  Briefcase, 
  ChevronRight, 
  ChevronDown, 
  ChevronUp, 
  HelpCircle, 
  FileText,
  Target,
  ArrowRight,
  Zap,
  X
} from 'lucide-react';
import { 
  startInterviewSession, 
  getInterviewSession, 
  submitInterviewAnswer, 
  nextInterviewQuestion, 
  completeInterviewSession, 
  getInterviewHistory, 
  getInterviewReadiness, 
  getSavedJobs 
} from '@/lib/api-client';
import { 
  InterviewSessionData, 
  InterviewEvaluationData, 
  InterviewFinalReportData, 
  InterviewReadinessData, 
  SavedJobData 
} from '@/lib/types';

export default function InterviewPage() {
  const [viewState, setViewState] = useState<'setup' | 'room' | 'report'>('setup');
  
  // Setup parameters
  const [selectedMode, setSelectedMode] = useState('Mixed');
  const [selectedDifficulty, setSelectedDifficulty] = useState('Beginner');
  const [questionCount, setQuestionCount] = useState(5);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [savedJobs, setSavedJobs] = useState<SavedJobData[]>([]);

  // Session & Room states
  const [currentSession, setCurrentSession] = useState<InterviewSessionData | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluating, setEvaluating] = useState(false);
  const [currentEvaluation, setCurrentEvaluation] = useState<InterviewEvaluationData | null>(null);

  // Report & History states
  const [finalReport, setFinalReport] = useState<InterviewFinalReportData | null>(null);
  const [historySessions, setHistorySessions] = useState<InterviewSessionData[]>([]);
  const [readinessData, setReadinessData] = useState<InterviewReadinessData | null>(null);

  // Audio / Speech UI toggle placeholder
  const [isVoiceActive, setIsVoiceActive] = useState(false);

  useEffect(() => {
    loadSetupData();
  }, []);

  async function loadSetupData() {
    try {
      const [hist, read, jobs] = await Promise.all([
        getInterviewHistory().catch(() => []),
        getInterviewReadiness().catch(() => null),
        getSavedJobs().catch(() => [])
      ]);
      setHistorySessions(hist);
      setReadinessData(read);
      setSavedJobs(jobs);
    } catch (err) {
      console.error('Failed to load setup data:', err);
    }
  }

  async function handleStartInterview(e: React.FormEvent) {
    e.preventDefault();
    setEvaluating(true);
    try {
      const session = await startInterviewSession({
        mode: selectedMode,
        difficulty: selectedDifficulty,
        question_count: questionCount,
        job_id: selectedJobId || undefined
      });
      setCurrentSession(session);
      setUserAnswer('');
      setCurrentEvaluation(null);
      setViewState('room');
    } catch (err) {
      console.error('Failed to start interview:', err);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleSubmitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!currentSession || !userAnswer.trim()) return;
    setEvaluating(true);
    try {
      const evaluation = await submitInterviewAnswer(currentSession.id, userAnswer);
      setCurrentEvaluation(evaluation);
    } catch (err) {
      console.error('Failed to evaluate answer:', err);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleNextQuestion() {
    if (!currentSession) return;
    setEvaluating(true);
    try {
      const updatedSession = await nextInterviewQuestion(currentSession.id);
      if (updatedSession.is_completed) {
        const report = await completeInterviewSession(currentSession.id);
        setFinalReport(report);
        setViewState('report');
      } else {
        setCurrentSession(updatedSession);
        setUserAnswer('');
        setCurrentEvaluation(null);
      }
    } catch (err) {
      console.error('Failed to advance question:', err);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleCompleteEarly() {
    if (!currentSession) return;
    setEvaluating(true);
    try {
      const report = await completeInterviewSession(currentSession.id);
      setFinalReport(report);
      setViewState('report');
    } catch (err) {
      console.error('Failed to complete session:', err);
    } finally {
      setEvaluating(false);
    }
  }

  const INTERVIEW_MODES = [
    { id: 'Mixed', title: 'Mixed Mock Interview', desc: 'Dynamic blend of technical, behavioral, and HR questions.' },
    { id: 'Technical', title: 'Technical Deep-Dive', desc: 'Core fundamentals, system design, and coding reasoning.' },
    { id: 'Resume-Based', title: 'Resume Project Defense', desc: 'Questions directly targeting your projects and experience.' },
    { id: 'Behavioral', title: 'Behavioral & STAR', desc: 'STAR methodology questions focusing on problem-solving.' },
    { id: 'HR', title: 'HR & Culture Alignment', desc: 'Career goals, motivation, work style, and teamwork.' },
    { id: 'Job-Specific', title: 'Job-Specific Simulator', desc: 'Tailored to a saved job posting and required skills.' },
  ];

  function getReadinessBadge(status: string) {
    switch (status) {
      case 'EXCELLENT':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">EXCELLENT</span>;
      case 'READY':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">READY</span>;
      case 'NEARLY READY':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">NEARLY READY</span>;
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">NEEDS PRACTICE</span>;
    }
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Top Banner Header */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">AI Mock Interview Simulator & Adaptive Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Adaptive interview simulator evaluating Technical, Behavioral, STAR, and Resume Knowledge with direct Skill & Roadmap feedback loops.
          </p>
        </div>

        {readinessData && (
          <div className="flex items-center space-x-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
            <Award className="w-5 h-5 text-indigo-400" />
            <div>
              <div className="text-xs font-bold text-white flex items-center space-x-2">
                <span>Overall Readiness:</span>
                {getReadinessBadge(readinessData.overall_readiness_status)}
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">{readinessData.total_interviews_completed} Interviews Completed • Avg Score: {readinessData.average_score}%</p>
            </div>
          </div>
        )}
      </div>

      {/* VIEW 1: SETUP WORKSPACE */}
      {viewState === 'setup' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <form onSubmit={handleStartInterview} className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <span>Configure Mock Interview Session</span>
            </h2>

            {/* Mode Cards */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Select Interview Mode</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {INTERVIEW_MODES.map((mode) => (
                  <div
                    key={mode.id}
                    onClick={() => setSelectedMode(mode.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedMode === mode.id ? 'bg-indigo-950/50 border-indigo-500/50 ring-1 ring-indigo-500/50' : 'bg-slate-950 border-slate-800 hover:border-slate-700'}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-bold text-white">{mode.title}</h3>
                      {selectedMode === mode.id && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                    </div>
                    <p className="text-xs text-slate-400">{mode.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Controls Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Starting Difficulty</label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="Beginner">Beginner (Adaptive)</option>
                  <option value="Intermediate">Intermediate (Adaptive)</option>
                  <option value="Advanced">Advanced (Adaptive)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Question Count</label>
                <select
                  value={questionCount}
                  onChange={(e) => setQuestionCount(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value={3}>3 Questions (Quick Practice)</option>
                  <option value={5}>5 Questions (Standard)</option>
                  <option value={7}>7 Questions (Comprehensive)</option>
                  <option value={10}>10 Questions (Full Assessment)</option>
                </select>
              </div>

              {selectedMode === 'Job-Specific' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Target Saved Job</label>
                  <select
                    value={selectedJobId}
                    onChange={(e) => setSelectedJobId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">-- Select Saved Job --</option>
                    {savedJobs.map((sj) => (
                      <option key={sj.job_id} value={sj.job_id}>
                        {sj.job.title} ({sj.job.company})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="pt-4 flex items-center justify-end">
              <button
                type="submit"
                disabled={evaluating}
                className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 flex items-center space-x-2 transition-all"
              >
                <span>Start Mock Interview</span>
                <Play className="w-4 h-4 fill-white" />
              </button>
            </div>
          </form>

          {/* Past History Column */}
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                <Clock className="w-5 h-5 text-indigo-400" />
                <span>Previous Interview History</span>
              </h2>

              {historySessions.length > 0 ? (
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
                  {historySessions.map((s) => (
                    <div key={s.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                      <div className="flex items-center justify-between font-bold text-white">
                        <span>{s.mode} Mode ({s.target_role})</span>
                        <span className="text-indigo-400">{s.overall_score}%</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400 text-[11px]">
                        <span>{s.question_count} Questions • {s.difficulty}</span>
                        <span>{new Date(s.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-xs text-slate-500 italic border border-dashed border-slate-800 rounded-xl">
                  No previous mock interviews. Start your first session above.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: INTERACTIVE INTERVIEW ROOM */}
      {viewState === 'room' && currentSession && currentSession.current_question && (
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          {/* Progress Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-bold border border-indigo-500/30">
                Question {currentSession.current_question_index + 1} of {currentSession.question_count}
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-slate-800 text-slate-300">
                {currentSession.current_question.category}
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Adaptive Difficulty: {currentSession.difficulty}
              </span>
            </div>

            <button
              onClick={handleCompleteEarly}
              className="text-xs text-slate-400 hover:text-white font-semibold"
            >
              Exit & Generate Report Early
            </button>
          </div>

          {/* Question Text Box */}
          <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <h2 className="text-lg font-bold text-white leading-relaxed">
              "{currentSession.current_question.question_text}"
            </h2>
            {currentSession.current_question.context_tip && (
              <p className="text-xs text-indigo-400 font-medium flex items-center space-x-1.5 pt-1">
                <HelpCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Coach Tip: {currentSession.current_question.context_tip}</span>
              </p>
            )}
          </div>

          {/* Answer Input */}
          <form onSubmit={handleSubmitAnswer} className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">Your Structured Response:</label>
                <button
                  type="button"
                  onClick={() => setIsVoiceActive(!isVoiceActive)}
                  className={`text-xs font-semibold flex items-center space-x-1 px-2.5 py-1 rounded-lg border ${isVoiceActive ? 'bg-pink-500/20 text-pink-400 border-pink-500/30' : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'}`}
                >
                  {isVoiceActive ? <Mic className="w-3.5 h-3.5" /> : <MicOff className="w-3.5 h-3.5" />}
                  <span>{isVoiceActive ? 'Voice Input Listening...' : 'Speech Architecture (Ready)'}</span>
                </button>
              </div>

              <textarea
                rows={6}
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Type your response clearly. Include technical specifics, architectural trade-offs, and measurable outcomes..."
                className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:border-indigo-500 focus:outline-none transition-all placeholder:text-slate-600"
              />
            </div>

            {!currentEvaluation && (
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={evaluating || !userAnswer.trim()}
                  className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 flex items-center space-x-2 transition-all"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{evaluating ? 'Evaluating with AI...' : 'Submit & Evaluate Answer'}</span>
                </button>
              </div>
            )}
          </form>

          {/* Immediate Evaluation Feedback Modal/Drawer */}
          {currentEvaluation && (
            <div className="p-6 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-4 text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    Evaluation Score: {currentEvaluation.score}%
                  </span>
                  <span className="text-slate-400 font-medium">Multi-Category AI Breakdown</span>
                </div>
              </div>

              {/* Sub-score Gauges */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Technical</span>
                  <div className="text-base font-bold text-white mt-0.5">{currentEvaluation.technical_score}%</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Communication</span>
                  <div className="text-base font-bold text-white mt-0.5">{currentEvaluation.communication_score}%</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Problem Solving</span>
                  <div className="text-base font-bold text-white mt-0.5">{currentEvaluation.problem_solving_score}%</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Behavioral</span>
                  <div className="text-base font-bold text-white mt-0.5">{currentEvaluation.behavioral_score}%</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Resume Knowledge</span>
                  <div className="text-base font-bold text-white mt-0.5">{currentEvaluation.resume_knowledge_score}%</div>
                </div>
              </div>

              {/* Strengths & Weaknesses */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <h4 className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">Strengths</h4>
                  {currentEvaluation.strengths.map((s, idx) => (
                    <p key={idx} className="text-slate-300">✓ {s}</p>
                  ))}
                </div>
                <div className="space-y-1">
                  <h4 className="font-bold text-amber-400 uppercase tracking-wider text-[11px]">Missing / Weak Points</h4>
                  {currentEvaluation.weaknesses.map((w, idx) => (
                    <p key={idx} className="text-slate-300">⚠ {w}</p>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-indigo-300">
                <strong>Coach Recommendation:</strong> {currentEvaluation.suggested_improvement}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={handleNextQuestion}
                  disabled={evaluating}
                  className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 flex items-center space-x-2"
                >
                  <span>Next Adaptive Question</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW 3: COMPREHENSIVE FINAL REPORT */}
      {viewState === 'report' && finalReport && (
        <div className="space-y-8">
          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
              <div>
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Final Interview Evaluation Report</span>
                <h2 className="text-2xl font-extrabold text-white mt-1">{finalReport.target_role} ({finalReport.mode} Mode)</h2>
                <p className="text-xs text-slate-400 mt-1">{finalReport.readiness_explanation}</p>
              </div>

              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-3xl font-extrabold text-white">{finalReport.overall_score}%</div>
                  <span className="text-[11px] text-slate-400 font-semibold">Overall Score</span>
                </div>
                {getReadinessBadge(finalReport.readiness_status)}
              </div>
            </div>

            {/* Sub-scores Row */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-xs font-semibold text-slate-400 uppercase">Technical</span>
                <div className="text-xl font-bold text-white mt-1">{finalReport.technical_score}%</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-xs font-semibold text-slate-400 uppercase">Communication</span>
                <div className="text-xl font-bold text-white mt-1">{finalReport.communication_score}%</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-xs font-semibold text-slate-400 uppercase">Problem Solving</span>
                <div className="text-xl font-bold text-white mt-1">{finalReport.problem_solving_score}%</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-xs font-semibold text-slate-400 uppercase">Behavioral</span>
                <div className="text-xl font-bold text-white mt-1">{finalReport.behavioral_score}%</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span className="text-xs font-semibold text-slate-400 uppercase">Resume Knowledge</span>
                <div className="text-xl font-bold text-white mt-1">{finalReport.resume_knowledge_score}%</div>
              </div>
            </div>

            {/* Roadmap Recommendations Box */}
            {finalReport.recommended_roadmap_topics && finalReport.recommended_roadmap_topics.length > 0 && (
              <div className="p-5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 space-y-3 text-xs">
                <h3 className="font-bold text-indigo-300 flex items-center space-x-2 text-sm">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <span>Roadmap Topics Recommended to Revisit</span>
                </h3>
                <div className="space-y-1.5">
                  {finalReport.recommended_roadmap_topics.map((topic, idx) => (
                    <div key={idx} className="flex items-center space-x-2 text-slate-200 font-medium">
                      <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span>{topic}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Q&A Itemized Accordion */}
            <div className="space-y-4 pt-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Itemized Question & Answer Review</h3>
              <div className="space-y-3 text-xs">
                {finalReport.questions_review.map((q, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between font-bold text-slate-200">
                      <span>Q{idx + 1}: {q.question_text}</span>
                      <span className="text-indigo-400 font-extrabold">{q.score}% Score</span>
                    </div>
                    {q.user_answer && (
                      <p className="text-slate-400 italic">" {q.user_answer} "</p>
                    )}
                    {q.evaluation && (
                      <p className="text-indigo-300 font-medium pt-1">Coach Note: {q.evaluation.suggested_improvement}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={() => setViewState('setup')}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all flex items-center space-x-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Start Another Session</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
