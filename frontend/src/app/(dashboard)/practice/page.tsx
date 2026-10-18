'use client';

import { Suspense, useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
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
  Layers,
  Lock,
  Unlock,
  Trophy,
  Award,
  Check,
  X,
  Code2,
  Copy,
  Clock,
  Compass,
  Tent,
  Trees,
  Mountain,
  Swords,
  Shield,
  Flag
} from 'lucide-react';
import {
  getPracticeContext,
  generatePracticeDrill,
  evaluatePracticeDrillQuestion,
  generateLevelTest,
  submitLevelTest,
  startMicroPractice,
  submitInterviewAnswer,
  nextInterviewQuestion,
  completeInterviewSession
} from '@/lib/api-client';
import {
  PracticeContextData,
  InteractiveDrillQuestion,
  DrillEvaluationData,
  LevelTestResponse,
  LevelTestQuestion,
  LevelTestSubmitResponse,
  InterviewSessionData,
  InterviewEvaluationData,
  InterviewFinalReportData
} from '@/lib/types';

export default function PracticePage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center max-w-4xl mx-auto">
          <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading Skill Practice Engine...</p>
        </div>
      }
    >
      <SkillPracticeEngine />
    </Suspense>
  );
}

function SkillPracticeEngine() {
  const searchParams = useSearchParams();
  const initialTopic = searchParams.get('topic');

  // Active view: 'hub' | 'drill' | 'level_test' | 'interview'
  const [activeTab, setActiveTab] = useState<'levels' | 'drills' | 'interview'>('levels');
  const [context, setContext] = useState<PracticeContextData | null>(null);
  const [loadingContext, setLoadingContext] = useState(true);

  // Drill States
  const [drillTopic, setDrillTopic] = useState('');
  const [drillLoading, setDrillLoading] = useState(false);
  const [drillQuestions, setDrillQuestions] = useState<InteractiveDrillQuestion[]>([]);
  const [drillIndex, setDrillIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [evaluatingAnswer, setEvaluatingAnswer] = useState(false);
  const [drillEvaluations, setDrillEvaluations] = useState<Record<number, DrillEvaluationData>>({});
  const [drillComplete, setDrillComplete] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  // Level Test States
  const [testActivePhaseId, setTestActivePhaseId] = useState<string | null>(null);
  const [testActivePhaseNumber, setTestActivePhaseNumber] = useState<number>(1);
  const [testLevelName, setTestLevelName] = useState('Spawn Point');
  const [testLoading, setTestLoading] = useState(false);
  const [testData, setTestData] = useState<LevelTestResponse | null>(null);
  const [testAnswers, setTestAnswers] = useState<Record<string, string>>({});
  const [testCurrentIndex, setTestCurrentIndex] = useState(0);
  const [flaggedQuestions, setFlaggedQuestions] = useState<Record<string, boolean>>({});
  const [testSubmitting, setTestSubmitting] = useState(false);
  const [testResult, setTestResult] = useState<LevelTestSubmitResponse | null>(null);
  const [testTimeRemaining, setTestTimeRemaining] = useState(600); // 10 minutes

  // Mock Interview Fallback States
  const [interviewSession, setInterviewSession] = useState<InterviewSessionData | null>(null);
  const [interviewAnswer, setInterviewAnswer] = useState('');
  const [interviewEvaluating, setInterviewEvaluating] = useState(false);
  const [interviewEvaluation, setInterviewEvaluation] = useState<InterviewEvaluationData | null>(null);
  const [interviewReport, setInterviewReport] = useState<InterviewFinalReportData | null>(null);

  // Custom Topic Form State
  const [customTopicInput, setCustomTopicInput] = useState('');

  // Confetti Canvas
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    loadContext();
  }, []);

  // Timer countdown for active test
  useEffect(() => {
    if (!testData || testLoading || testResult || testTimeRemaining <= 0) return;
    const interval = setInterval(() => {
      setTestTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [testData, testLoading, testResult, testTimeRemaining]);

  const loadContext = async () => {
    setLoadingContext(true);
    try {
      const data = await getPracticeContext();
      setContext(data);
      if (initialTopic) {
        setActiveTab('drills');
        startDrill(initialTopic);
      }
    } catch (err) {
      console.error('Failed to load practice context:', err);
    } finally {
      setLoadingContext(false);
    }
  };

  const triggerConfetti = useCallback(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles: Array<{
      x: number;
      y: number;
      r: number;
      d: number;
      color: string;
      tilt: number;
      tiltAngle: number;
      tiltAngleIncremental: number;
    }> = [];

    const colors = ['#10B981', '#38BDF8', '#F59E0B', '#EC4899', '#8B5CF6', '#FCD34D'];
    for (let i = 0; i < 90; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height - canvas.height,
        r: Math.random() * 6 + 3,
        d: Math.random() * 20 + 10,
        color: colors[Math.floor(Math.random() * colors.length)],
        tilt: Math.floor(Math.random() * 10) - 10,
        tiltAngle: 0,
        tiltAngleIncremental: Math.random() * 0.07 + 0.05
      });
    }

    let animationFrameId: number;
    let frameCount = 0;
    function render() {
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      frameCount++;

      particles.forEach((p) => {
        p.tiltAngle += p.tiltAngleIncremental;
        p.y += (Math.cos(p.d) + 3 + p.r / 2) * 0.7;
        p.tilt = Math.sin(p.tiltAngle - frameCount / 3) * 15;

        ctx.beginPath();
        ctx.lineWidth = p.r / 2;
        ctx.strokeStyle = p.color;
        ctx.moveTo(p.x + p.tilt + p.r / 4, p.y);
        ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r / 4);
        ctx.stroke();
      });

      if (frameCount < 160) {
        animationFrameId = requestAnimationFrame(render);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  // ----------------------------------------------------
  // Level Gate Test Handlers
  // ----------------------------------------------------
  const handleStartLevelTest = async (phaseId: string, phaseNum: number, levelName: string) => {
    setTestActivePhaseId(phaseId);
    setTestActivePhaseNumber(phaseNum);
    setTestLevelName(levelName);
    setTestLoading(true);
    setTestData(null);
    setTestAnswers({});
    setTestCurrentIndex(0);
    setFlaggedQuestions({});
    setTestResult(null);
    setTestTimeRemaining(600);

    try {
      const data = await generateLevelTest(phaseId);
      setTestData(data);
    } catch (err) {
      console.error('Failed to generate level test:', err);
    } finally {
      setTestLoading(false);
    }
  };

  const handleSelectTestOption = (questionId: string, option: string) => {
    setTestAnswers((prev) => ({
      ...prev,
      [questionId]: option
    }));
  };

  const handleSubmitLevelTest = async () => {
    if (!testActivePhaseId || !testData) return;
    setTestSubmitting(true);
    try {
      const res = await submitLevelTest(testActivePhaseId, testAnswers);
      setTestResult(res);
      if (res.passed) {
        setTimeout(() => triggerConfetti(), 150);
        await loadContext();
      }
    } catch (err) {
      console.error('Failed to submit level test:', err);
    } finally {
      setTestSubmitting(false);
    }
  };

  // ----------------------------------------------------
  // Interactive Drill Handlers
  // ----------------------------------------------------
  const startDrill = async (topic: string) => {
    setDrillTopic(topic);
    setDrillLoading(true);
    setDrillQuestions([]);
    setDrillIndex(0);
    setSelectedOption(null);
    setDrillEvaluations({});
    setDrillComplete(false);

    try {
      const qs = await generatePracticeDrill(topic, 'Intermediate', 3);
      setDrillQuestions(qs);
    } catch (err) {
      console.error('Failed to generate drill:', err);
    } finally {
      setDrillLoading(false);
    }
  };

  const handleEvaluateDrill = async () => {
    if (!selectedOption || !drillQuestions[drillIndex]) return;
    setEvaluatingAnswer(true);
    const currQ = drillQuestions[drillIndex];
    try {
      const res = await evaluatePracticeDrillQuestion({
        question_id: currQ.id,
        question_text: currQ.question,
        options: currQ.options,
        correct_answer: currQ.correct_answer,
        explanation: currQ.explanation,
        user_answer: selectedOption,
        topic: currQ.topic || drillTopic
      });
      setDrillEvaluations((prev) => ({
        ...prev,
        [drillIndex]: res
      }));
    } catch (err) {
      console.error('Failed to evaluate drill answer:', err);
    } finally {
      setEvaluatingAnswer(false);
    }
  };

  const handleNextDrillQuestion = () => {
    if (drillIndex + 1 < drillQuestions.length) {
      setDrillIndex((prev) => prev + 1);
      setSelectedOption(null);
    } else {
      setDrillComplete(true);
    }
  };

  // Helper for Level Theme Icons
  const getLevelIcon = (iconName: string) => {
    switch (iconName?.toLowerCase()) {
      case 'tent': return <Tent className="w-5 h-5 text-amber-400" />;
      case 'trees': return <Trees className="w-5 h-5 text-emerald-400" />;
      case 'mountain': return <Mountain className="w-5 h-5 text-sky-400" />;
      case 'swords': return <Swords className="w-5 h-5 text-rose-400" />;
      case 'trophy': return <Trophy className="w-5 h-5 text-amber-300" />;
      default: return <Compass className="w-5 h-5 text-violet-400" />;
    }
  };

  const targetRole = context?.target_role || 'Software Developer';

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16 relative">
      {/* Confetti Overlay */}
      <canvas
        ref={canvasRef}
        className="pointer-events-none fixed inset-0 z-50 w-full h-full"
      />

      {/* Top Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-violet-950/80 via-slate-900 to-indigo-950/80 border border-violet-500/20 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center space-x-2 text-xs font-bold text-violet-400 uppercase tracking-wider">
              <Dumbbell className="w-4 h-4" />
              <span>Skill Practice Engine · Micro Practice Mode</span>
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center space-x-2">
              <span>Interactive Skill & Level Advancement Drills</span>
            </h1>
            <p className="text-xs text-slate-300">
              Target Role: <strong className="text-white font-semibold">{targetRole}</strong> · Dynamic Groq AI interactive questions, code analysis & roadmap level gating.
            </p>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex items-center space-x-1.5 p-1 bg-slate-950/80 border border-slate-800 rounded-xl self-start md:self-auto">
            <button
              onClick={() => { setActiveTab('levels'); setTestActivePhaseId(null); setDrillTopic(''); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'levels'
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Trophy className="w-3.5 h-3.5 text-amber-400" />
              <span>Roadmap Level Tests</span>
            </button>
            <button
              onClick={() => { setActiveTab('drills'); setTestActivePhaseId(null); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'drills'
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-cyan-400" />
              <span>Skill Drills (MCQ & Code)</span>
            </button>
          </div>
        </div>
      </div>

      {/* ==================================================== */}
      {/* TAB 1: ROADMAP LEVEL ADVANCEMENT TESTS (GATED)      */}
      {/* ==================================================== */}
      {activeTab === 'levels' && !testActivePhaseId && (
        <div className="space-y-6">
          {/* Active Level Gating Banner */}
          {context && (
            <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900/80 border border-indigo-500/30 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30 inline-flex items-center space-x-1">
                    <Award className="w-3 h-3" />
                    <span>Level Progression Gating</span>
                  </span>
                  <h2 className="text-xl font-extrabold text-white">
                    Level {context.current_level_number}: {context.current_level_name}
                  </h2>
                  <p className="text-xs text-slate-300">{context.current_level_theme}</p>
                </div>

                <div className="flex items-center space-x-3">
                  {context.current_test_passed ? (
                    <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl text-xs font-bold">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Level Passed ({context.current_test_score ?? 100}%)</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-xl text-xs font-bold">
                      <Lock className="w-4 h-4" />
                      <span>Pass Test to Unlock Level {context.current_level_number + 1}</span>
                    </div>
                  )}

                  <button
                    onClick={() =>
                      handleStartLevelTest(
                        context.current_phase_id,
                        context.current_level_number,
                        context.current_level_name
                      )
                    }
                    className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-2 transition-all shadow-lg shadow-violet-600/30"
                  >
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>{context.current_test_passed ? 'Retake Level Test' : 'Take Level Gate Test (Groq AI) →'}</span>
                  </button>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-3 flex items-center justify-between">
                <span>Rules: 5 interactive questions · Minimum 70% score required to advance · Instant Groq AI verification</span>
                <span className="text-violet-400 font-semibold">+100 to 200 XP per clearance</span>
              </div>
            </div>
          )}

          {/* All Roadmap Levels Grid */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-violet-400" />
                  <span>Roadmap Advancement World Levels</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Each level tests real skills from your curriculum before allowing you to enter the next territory.
                </p>
              </div>
              <Link
                href="/roadmap"
                className="text-xs font-semibold text-violet-400 hover:text-violet-300 flex items-center space-x-1"
              >
                <span>View Full Roadmap Map</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {context?.all_levels.map((lvl) => (
                <div
                  key={lvl.phase_id}
                  className={`p-4 rounded-xl border transition-all flex flex-col justify-between space-y-3 ${
                    lvl.test_passed
                      ? 'bg-slate-950/80 border-emerald-500/30 hover:border-emerald-500/50'
                      : lvl.is_unlocked
                      ? 'bg-slate-950 border-violet-500/30 hover:border-violet-500/60'
                      : 'bg-slate-950/40 border-slate-900 opacity-60'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getLevelIcon(lvl.level_icon)}
                        <span className="text-xs font-extrabold text-white">Level {lvl.phase_number}</span>
                      </div>
                      {lvl.test_passed ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                          <Check className="w-3 h-3" />
                          <span>Cleared {lvl.test_score ? `(${lvl.test_score}%)` : ''}</span>
                        </span>
                      ) : lvl.is_unlocked ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center space-x-1">
                          <Unlock className="w-3 h-3" />
                          <span>Ready for Test</span>
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-500 flex items-center space-x-1">
                          <Lock className="w-3 h-3" />
                          <span>Locked</span>
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-bold text-slate-200">{lvl.level_name}</h4>
                    <p className="text-[11px] text-slate-400 line-clamp-2">{lvl.level_theme}</p>
                  </div>

                  <div className="pt-2 border-t border-slate-900 flex items-center justify-between">
                    <div className="text-[10px] text-slate-500">
                      {lvl.stars > 0 && <span>{'⭐'.repeat(lvl.stars)} · </span>}
                      <span>+{lvl.xp_reward} XP</span>
                    </div>

                    {lvl.is_unlocked ? (
                      <button
                        onClick={() => handleStartLevelTest(lvl.phase_id, lvl.phase_number, lvl.level_name)}
                        className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1 transition-all"
                      >
                        <Play className="w-3 h-3 fill-white" />
                        <span>{lvl.test_passed ? 'Retake' : 'Start Test'}</span>
                      </button>
                    ) : (
                      <span className="text-[10px] text-slate-500 font-medium">Pass Level {lvl.phase_number - 1} first</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* ACTIVE LEVEL TEST MODAL / INTERFACE                  */}
      {/* ==================================================== */}
      {activeTab === 'levels' && testActivePhaseId && (
        <div className="space-y-6">
          {/* Test Header */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 rounded-full bg-violet-500/20 text-violet-300 font-extrabold text-xs border border-violet-500/30">
                Level {testActivePhaseNumber}: {testLevelName}
              </span>
              <span className="text-xs text-slate-400">Target Role: <strong className="text-white">{targetRole}</strong></span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1 text-xs font-semibold text-slate-300 bg-slate-950 px-3 py-1 rounded-lg border border-slate-800">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span>
                  {Math.floor(testTimeRemaining / 60)}:{(testTimeRemaining % 60).toString().padStart(2, '0')}
                </span>
              </div>
              <button
                onClick={() => setTestActivePhaseId(null)}
                className="text-xs font-semibold text-slate-400 hover:text-white border border-slate-700 px-3 py-1 rounded-lg transition-colors"
              >
                Exit Test
              </button>
            </div>
          </div>

          {testLoading ? (
            <div className="p-16 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
              <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <h3 className="text-base font-bold text-white">Groq AI is Generating Your Level Advancement Test…</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Analyzing your level syllabus and creating 5 interactive multiple choice & code challenges.
              </p>
            </div>
          ) : testResult ? (
            /* ==================================================== */
            /* TEST RESULTS & CELEBRATION / FEEDBACK                */
            /* ==================================================== */
            <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
              <div className={`p-6 rounded-2xl border text-center space-y-3 ${
                testResult.passed
                  ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200'
                  : 'bg-rose-950/40 border-rose-500/30 text-rose-200'
              }`}>
                <div className="text-4xl">{testResult.passed ? '🏆' : '📚'}</div>
                <h2 className="text-2xl font-black text-white">
                  {testResult.passed ? 'Level Cleared! Next Level Unlocked!' : 'Needs Practice (Minimum 70% Required)'}
                </h2>
                <div className="text-3xl font-extrabold text-white">
                  {testResult.score_percent}% <span className="text-sm font-normal text-slate-400">({testResult.correct_count}/{testResult.total_questions} correct)</span>
                </div>
                <p className="text-xs max-w-xl mx-auto leading-relaxed">{testResult.feedback}</p>
                {testResult.passed && (
                  <div className="pt-2 flex items-center justify-center space-x-3 text-xs font-bold text-amber-300">
                    <span>{'⭐'.repeat(testResult.stars_awarded)}</span>
                    <span>+{testResult.xp_earned} XP Added</span>
                  </div>
                )}
              </div>

              {/* Detailed Breakdown */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white">Question by Question Review</h3>
                <div className="space-y-3">
                  {testResult.results_detail.map((rd, i) => (
                    <div
                      key={rd.question_id || i}
                      className={`p-4 rounded-xl border text-xs space-y-2 ${
                        rd.is_correct ? 'bg-slate-950/60 border-emerald-500/30' : 'bg-slate-950/60 border-rose-500/30'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-bold text-slate-200">
                          Q{i + 1}: {rd.question}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          rd.is_correct ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {rd.is_correct ? 'Correct ✓' : 'Incorrect ✗'}
                        </span>
                      </div>

                      {rd.code_snippet && (
                        <pre className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto">
                          {rd.code_snippet}
                        </pre>
                      )}

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                        <div>
                          <span className="text-slate-500 font-semibold">Your selection: </span>
                          <span className={rd.is_correct ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {rd.user_answer}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 font-semibold">Correct choice: </span>
                          <span className="text-emerald-400 font-bold">{rd.correct_answer}</span>
                        </div>
                      </div>

                      <p className="text-[11px] text-slate-400 border-t border-slate-900 pt-2 leading-relaxed">
                        <strong className="text-indigo-400">Explanation: </strong>
                        {rd.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                <button
                  onClick={() => handleStartLevelTest(testActivePhaseId, testActivePhaseNumber, testLevelName)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all flex items-center space-x-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retake Test</span>
                </button>
                <button
                  onClick={() => { setTestActivePhaseId(null); loadContext(); }}
                  className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-md shadow-violet-600/30"
                >
                  <span>Return to Practice Hub →</span>
                </button>
              </div>
            </div>
          ) : testData && testData.questions && testData.questions.length > 0 ? (
            /* ==================================================== */
            /* INTERACTIVE TEST QUESTION VIEW                       */
            /* ==================================================== */
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
              {/* Question Navigation Dots */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  {testData.questions.map((q, idx) => {
                    const isAnswered = !!testAnswers[q.id];
                    const isCurrent = testCurrentIndex === idx;
                    const isFlagged = !!flaggedQuestions[q.id];
                    return (
                      <button
                        key={q.id}
                        onClick={() => setTestCurrentIndex(idx)}
                        className={`w-8 h-8 rounded-lg text-xs font-bold transition-all relative ${
                          isCurrent
                            ? 'bg-violet-600 text-white ring-2 ring-violet-400'
                            : isAnswered
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        {idx + 1}
                        {isFlagged && (
                          <span className="w-2 h-2 rounded-full bg-amber-400 absolute -top-1 -right-1" />
                        )}
                      </button>
                    );
                  })}
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => {
                      const qid = testData.questions[testCurrentIndex].id;
                      setFlaggedQuestions((prev) => ({ ...prev, [qid]: !prev[qid] }));
                    }}
                    className={`text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all flex items-center space-x-1 ${
                      flaggedQuestions[testData.questions[testCurrentIndex].id]
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Flag className="w-3 h-3" />
                    <span>Flag</span>
                  </button>
                </div>
              </div>

              {/* Active Question Box */}
              {(() => {
                const q = testData.questions[testCurrentIndex];
                const currentAnswer = testAnswers[q.id];

                return (
                  <div className="space-y-5">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2 text-xs font-bold text-violet-400 uppercase tracking-wider">
                        <span>Question {testCurrentIndex + 1} of {testData.questions.length}</span>
                        <span>·</span>
                        <span>{q.topic}</span>
                      </div>
                      <h3 className="text-base font-extrabold text-white leading-relaxed">{q.question}</h3>
                    </div>

                    {/* Optional Code Snippet Challenge */}
                    {q.code_snippet && (
                      <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 relative">
                        <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
                          <span className="font-mono text-[11px] text-violet-400">Code Analysis Challenge</span>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(q.code_snippet || '');
                              setCopiedCode(true);
                              setTimeout(() => setCopiedCode(false), 2000);
                            }}
                            className="hover:text-white transition-colors flex items-center space-x-1 text-[11px]"
                          >
                            <Copy className="w-3 h-3" />
                            <span>{copiedCode ? 'Copied!' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                          {q.code_snippet}
                        </pre>
                      </div>
                    )}

                    {/* Interactive 4 Options */}
                    <div className="space-y-3 pt-2">
                      {q.options.map((opt, optIdx) => {
                        const isSelected = currentAnswer === opt;
                        const optionPrefix = opt.slice(0, 2); // 'A)', 'B)'...
                        const optionText = opt.slice(3) || opt;

                        return (
                          <div
                            key={optIdx}
                            onClick={() => handleSelectTestOption(q.id, opt)}
                            className={`p-4 rounded-xl border text-xs cursor-pointer transition-all flex items-center space-x-3 group ${
                              isSelected
                                ? 'bg-violet-950/60 border-violet-500 shadow-md shadow-violet-500/20'
                                : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
                            }`}
                          >
                            <div
                              className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 transition-colors ${
                                isSelected
                                  ? 'bg-violet-600 text-white'
                                  : 'bg-slate-900 text-slate-400 group-hover:text-white'
                              }`}
                            >
                              {String.fromCharCode(65 + optIdx)}
                            </div>
                            <span className={`flex-1 font-medium leading-relaxed ${isSelected ? 'text-white font-bold' : ''}`}>
                              {optionText}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Previous / Next / Submit Controls */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                      <button
                        onClick={() => setTestCurrentIndex((prev) => Math.max(0, prev - 1))}
                        disabled={testCurrentIndex === 0}
                        className="px-4 py-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold disabled:opacity-40 transition-all"
                      >
                        ← Previous
                      </button>

                      {testCurrentIndex + 1 < testData.questions.length ? (
                        <button
                          onClick={() => setTestCurrentIndex((prev) => prev + 1)}
                          className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-md shadow-violet-600/30"
                        >
                          <span>Next Question →</span>
                        </button>
                      ) : (
                        <button
                          onClick={handleSubmitLevelTest}
                          disabled={testSubmitting}
                          className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-lg shadow-emerald-600/30 disabled:opacity-50"
                        >
                          <Trophy className="w-4 h-4" />
                          <span>{testSubmitting ? 'Evaluating with Groq AI…' : 'Submit & Check Level Test'}</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400 text-sm">Failed to load level test questions.</div>
          )}
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 2: INTERACTIVE SKILL DRILLS (MCQ & CODE)        */}
      {/* ==================================================== */}
      {activeTab === 'drills' && (
        <div className="space-y-6">
          {!drillTopic ? (
            /* Topic Selection Screen */
            <div className="space-y-6">
              {/* Profile Analysis Recommendations */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center space-x-2">
                      <Target className="w-4 h-4 text-violet-400" />
                      <span>Recommended Practice Drills (Profile Analysis)</span>
                    </h2>
                    <p className="text-xs text-slate-400">
                      Generated by analyzing your verified skills, missing prerequisites for {targetRole}, and weak areas.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {context?.recommended_topics.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-violet-500/40 transition-all flex flex-col justify-between space-y-3 group"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                            {item.topic}
                          </h4>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              item.priority === 'High'
                                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                            }`}
                          >
                            {item.type}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">{item.reason}</p>
                      </div>

                      <button
                        onClick={() => startDrill(item.topic)}
                        disabled={drillLoading}
                        className="w-full py-2 px-3 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs transition-all flex items-center justify-center space-x-1.5 shadow-md shadow-violet-600/20"
                      >
                        <Play className="w-3.5 h-3.5 fill-white" />
                        <span>Start 3-Question Interactive Drill →</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Custom Topic Input */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>Practice Any Custom Topic or Skill</span>
                </h3>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (customTopicInput.trim()) {
                      startDrill(customTopicInput.trim());
                    }
                  }}
                  className="flex flex-col sm:flex-row gap-3"
                >
                  <input
                    type="text"
                    value={customTopicInput}
                    onChange={(e) => setCustomTopicInput(e.target.value)}
                    placeholder="e.g. Python Memory Management, C++ Pointers, Git Rebase, REST API Design..."
                    className="flex-1 p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-violet-500 focus:outline-none placeholder:text-slate-600"
                  />
                  <button
                    type="submit"
                    disabled={!customTopicInput.trim() || drillLoading}
                    className="px-6 py-3.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center justify-center space-x-2 transition-all disabled:opacity-50 shrink-0 shadow-lg shadow-violet-600/20"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Generate AI Drill</span>
                  </button>
                </form>
              </div>
            </div>
          ) : (
            /* Active Drill Question View */
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="flex items-center space-x-3">
                  <span className="px-3 py-1 rounded-full bg-violet-500/20 text-violet-300 font-extrabold text-xs border border-violet-500/30">
                    Drill: {drillTopic}
                  </span>
                  <span className="text-xs text-slate-400">Target Role: <strong className="text-white">{targetRole}</strong></span>
                </div>
                <button
                  onClick={() => setDrillTopic('')}
                  className="text-xs font-semibold text-slate-400 hover:text-white border border-slate-700 px-3 py-1 rounded-lg transition-colors"
                >
                  Choose Different Topic
                </button>
              </div>

              {drillLoading ? (
                <div className="p-16 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
                  <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
                  <h3 className="text-base font-bold text-white">Groq AI is Generating Interactive Questions for '{drillTopic}'…</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Formulating rigorous code snippets and multiple choice options calibrated for {targetRole}.
                  </p>
                </div>
              ) : drillComplete ? (
                /* Drill Complete View */
                <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-5">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto text-2xl font-black border border-emerald-500/30">
                    ✓
                  </div>
                  <h2 className="text-2xl font-black text-white">Skill Drill Completed!</h2>
                  <div className="text-3xl font-extrabold text-emerald-400">
                    {Math.round(
                      (Object.values(drillEvaluations).filter((ev) => ev.is_correct).length /
                        drillQuestions.length) *
                        100
                    )}%
                    <span className="text-xs font-normal text-slate-400"> Accuracy</span>
                  </div>
                  <p className="text-xs text-slate-300 max-w-md mx-auto">
                    You have practiced core concepts in <strong>{drillTopic}</strong>. Every checked question verified against verified engineering principles.
                  </p>
                  <div className="flex items-center justify-center space-x-3 pt-2">
                    <button
                      onClick={() => startDrill(drillTopic)}
                      className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                    >
                      Retry This Drill
                    </button>
                    <button
                      onClick={() => setDrillTopic('')}
                      className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold shadow-md shadow-violet-600/30"
                    >
                      Practice Another Topic →
                    </button>
                  </div>
                </div>
              ) : drillQuestions.length > 0 ? (
                /* Interactive Question Card */
                (() => {
                  const q = drillQuestions[drillIndex];
                  const evaluation = drillEvaluations[drillIndex];

                  return (
                    <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span className="font-bold text-violet-400">Question {drillIndex + 1} of {drillQuestions.length}</span>
                        <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-semibold">{q.difficulty}</span>
                      </div>

                      <h3 className="text-base font-extrabold text-white leading-relaxed">{q.question}</h3>

                      {q.code_snippet && (
                        <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                          <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                            {q.code_snippet}
                          </pre>
                        </div>
                      )}

                      {/* Options */}
                      <div className="space-y-3">
                        {q.options.map((opt, optIdx) => {
                          const isSelected = selectedOption === opt;
                          const hasAnswered = !!evaluation;
                          const isCorrectOption = opt.trim().toLowerCase() === q.correct_answer.trim().toLowerCase() || opt.startsWith(q.correct_answer.slice(0, 2));

                          let borderStyle = 'border-slate-800 hover:border-slate-700 bg-slate-950';
                          if (hasAnswered) {
                            if (isCorrectOption) {
                              borderStyle = 'border-emerald-500 bg-emerald-950/40 text-emerald-200';
                            } else if (isSelected && !evaluation.is_correct) {
                              borderStyle = 'border-rose-500 bg-rose-950/40 text-rose-200';
                            } else {
                              borderStyle = 'border-slate-900 bg-slate-950/40 opacity-50';
                            }
                          } else if (isSelected) {
                            borderStyle = 'border-violet-500 bg-violet-950/60 shadow-md shadow-violet-500/20';
                          }

                          return (
                            <div
                              key={optIdx}
                              onClick={() => {
                                if (!hasAnswered) setSelectedOption(opt);
                              }}
                              className={`p-4 rounded-xl border text-xs transition-all flex items-center space-x-3 cursor-pointer ${borderStyle}`}
                            >
                              <div
                                className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                                  hasAnswered && isCorrectOption
                                    ? 'bg-emerald-500 text-white'
                                    : hasAnswered && isSelected && !evaluation.is_correct
                                    ? 'bg-rose-500 text-white'
                                    : isSelected
                                    ? 'bg-violet-600 text-white'
                                    : 'bg-slate-900 text-slate-400'
                                }`}
                              >
                                {String.fromCharCode(65 + optIdx)}
                              </div>
                              <span className="flex-1 font-medium leading-relaxed">{opt}</span>
                            </div>
                          );
                        })}
                      </div>

                      {/* Feedback after checking */}
                      {evaluation && (
                        <div
                          className={`p-4 rounded-xl border text-xs space-y-2 ${
                            evaluation.is_correct
                              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200'
                              : 'bg-rose-950/30 border-rose-500/30 text-rose-200'
                          }`}
                        >
                          <div className="flex items-center space-x-2 font-bold text-sm">
                            <span>{evaluation.is_correct ? 'Sahi Jawab! 🎉' : 'Galat Jawab! ❌'}</span>
                          </div>
                          <p className="leading-relaxed">{evaluation.feedback}</p>
                          <p className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-2">
                            <strong className="text-white">Explanation: </strong>
                            {evaluation.explanation}
                          </p>
                        </div>
                      )}

                      {/* Bottom Controls */}
                      <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                        <div className="text-xs text-slate-500 font-medium">
                          {selectedOption && !evaluation ? 'Option selected. Click Check Answer to verify with Groq AI.' : ''}
                        </div>

                        {!evaluation ? (
                          <button
                            onClick={handleEvaluateDrill}
                            disabled={!selectedOption || evaluatingAnswer}
                            className="px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-md shadow-violet-600/30 disabled:opacity-50"
                          >
                            <Sparkles className="w-4 h-4" />
                            <span>{evaluatingAnswer ? 'Checking Answer…' : 'Check Answer'}</span>
                          </button>
                        ) : (
                          <button
                            onClick={handleNextDrillQuestion}
                            className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-md shadow-emerald-600/30"
                          >
                            <span>Next Question →</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })()
              ) : null}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
