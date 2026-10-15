'use client';

import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { 
  MapPin, 
  CheckCircle2, 
  Clock, 
  BookOpen, 
  Code, 
  Sparkles, 
  RefreshCw, 
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Target,
  Award,
  Layers,
  Square,
  ArrowRight,
  ListChecks,
  Lightbulb,
  Lock,
  Unlock,
  Trophy,
  Play,
  Check,
  X,
  RotateCcw,
  HelpCircle,
  GraduationCap,
  Flame,
  Zap,
  Map as MapIcon,
  ChevronRight,
  Star,
  Flag,
  Volume2,
  VolumeX,
  Copy,
  CheckCheck,
  Compass,
  Tent,
  Trees,
  Mountain,
  Swords,
  Shield,
  Activity,
  Eye,
  EyeOff,
  Plus,
  Settings2,
  Sliders
} from 'lucide-react';
import { 
  getCurrentRoadmap, 
  generateRoadmap, 
  getTodayTasks, 
  completeRoadmapTask, 
  uncompleteRoadmapTask, 
  recalculateRoadmap,
  updateRoadmapPreferences,
  addCustomRoadmapPhase,
  generateLevelTest,
  submitLevelTest
} from '@/lib/api-client';
import { 
  RoadmapData, 
  DailyTasksData, 
  RoadmapPhase, 
  RoadmapTask,
  LevelTestResponse,
  LevelTestQuestion,
  LevelTestSubmitResponse
} from '@/lib/types';

// Standard fallback level names
const STANDARD_LEVEL_NAMES = [
  { name: 'Spawn Point', theme: 'Foundations & Setup', icon: 'compass' },
  { name: 'Starter Camp', theme: 'Core Logic & Problem Solving', icon: 'camp' },
  { name: 'Skill Forest', theme: 'Frameworks & Databases', icon: 'forest' },
  { name: 'Challenge Cave', theme: 'Full-Stack & Architecture', icon: 'cave' },
  { name: 'Boss Battle', theme: 'Production Capstone Project', icon: 'boss' },
  { name: 'Interview Arena', theme: 'Technical Mock Interview & System Design', icon: 'swords' },
  { name: 'Mastery Island', theme: 'Placement Verification & Career Launch', icon: 'island' }
];

/**
 * Dynamically computes zigzag coordinates and SVG trail for ANY number of phases N.
 * - Leaves 125px of headroom above Node 1 so badges/pins are NEVER clipped.
 * - Zigzag pattern winds: Left -> Center-Right -> Right -> Center-Left -> Left ...
 * - Appends continuation node "..." at the end.
 */
function computeDynamicZigzagLayout(phasesCount: number) {
  const count = Math.max(1, phasesCount);
  const startY = 125; // Safe headroom so top badge never clips
  const stepY = 135;  // Vertical distance between levels
  const coords: Array<{ x: number; y: number }> = [];

  for (let i = 0; i < count; i++) {
    const rowY = startY + i * stepY;
    const cycle = i % 4;
    let colX = 140; // Left
    if (cycle === 1) colX = 410; // Center going right
    else if (cycle === 2) colX = 660; // Right
    else if (cycle === 3) colX = 370; // Center going left
    coords.push({ x: colX, y: rowY });
  }

  // Final continuation "..." node coordinates
  const lastIndex = count - 1;
  const lastCycle = lastIndex % 4;
  let continuationX = 440;
  if (lastCycle === 0) continuationX = 410;
  else if (lastCycle === 2) continuationX = 410;
  else if (lastCycle === 1) continuationX = 580;
  else if (lastCycle === 3) continuationX = 220;

  const continuationY = startY + count * stepY;
  const continuationCoord = { x: continuationX, y: continuationY };
  coords.push(continuationCoord);

  const totalHeight = continuationY + 115;

  // Build SVG straight-line path connecting all nodes in order
  const pathD = coords.map((pt, idx) => `${idx === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`).join(' ');

  return {
    coordinates: coords.slice(0, count),
    continuationCoord,
    pathD,
    totalHeight,
    viewBox: `0 0 800 ${totalHeight}`
  };
}

// Web Audio API Sound Synthesizer (Zero asset dependency)
function playSound(type: 'select' | 'click' | 'victory' | 'fail' | 'unlock', soundEnabled = true) {
  if (!soundEnabled || typeof window === 'undefined') return;
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;
    const ctx = new AudioContextClass();
    const now = ctx.currentTime;

    if (type === 'select') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === 'click') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(392, now);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.04);
    } else if (type === 'victory') {
      // Harmonic celebratory fanfare: C5, E5, G5, C6
      const notes = [523.25, 659.25, 783.99, 1046.50];
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.09);
        gain.gain.setValueAtTime(0.12, now + idx * 0.09);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.09 + 0.3);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + idx * 0.09);
        osc.stop(now + idx * 0.09 + 0.3);
      });
    } else if (type === 'fail') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(260, now);
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.2);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.2);
    }
  } catch (e) {
    // Ignore audio context exceptions in background tabs
  }
}

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [todayData, setTodayData] = useState<DailyTasksData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'map' | 'curriculum'>('map');
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showFutureMilestonesModal, setShowFutureMilestonesModal] = useState(false);

  // Selected level detail modal
  const [selectedPhase, setSelectedPhase] = useState<RoadmapPhase | null>(null);
  const [activeTab, setActiveTab] = useState<'learn' | 'practice' | 'test'>('learn');
  const [lockedAlertPhase, setLockedAlertPhase] = useState<RoadmapPhase | null>(null);

  // Hovered level preview on map
  const [hoveredPhase, setHoveredPhase] = useState<RoadmapPhase | null>(null);

  // AI Level Test Modal States
  const [testActivePhase, setTestActivePhase] = useState<RoadmapPhase | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testData, setTestData] = useState<LevelTestResponse | null>(null);
  const [testAnswers, setTestAnswers] = useState<Record<string, string>>({});
  const [testCurrentIndex, setTestCurrentIndex] = useState(0);
  const [flaggedQuestions, setFlaggedQuestions] = useState<Record<string, boolean>>({});
  const [testSubmitting, setTestSubmitting] = useState(false);
  const [testResult, setTestResult] = useState<LevelTestSubmitResponse | null>(null);
  const [showTestReview, setShowTestReview] = useState(false);
  const [testTimeRemaining, setTestTimeRemaining] = useState(600); // 10 minutes timer
  const [copiedCode, setCopiedCode] = useState(false);

  // Confetti canvas ref
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Accordion & Syllabus states
  const [openPhaseId, setOpenPhaseId] = useState<string>('phase-1');
  const [showPreferences, setShowPreferences] = useState(false);
  const [openTaskId, setOpenTaskId] = useState<string | null>(null);

  // Setup form states
  const [userLevel, setUserLevel] = useState('Beginner');
  const [hoursPerDay, setHoursPerDay] = useState(1);
  const [daysPerWeek, setDaysPerWeek] = useState(5);
  const [learningStyle, setLearningStyle] = useState('Hands-on');
  const [trackPace, setTrackPace] = useState<'Express' | 'Standard' | 'Comprehensive'>('Standard');
  const [showAddCustomModal, setShowAddCustomModal] = useState(false);
  const [customPhaseTitle, setCustomPhaseTitle] = useState('');
  const [customPhaseDesc, setCustomPhaseDesc] = useState('');
  const [customPhaseTopics, setCustomPhaseTopics] = useState('');
  const [customPhaseLoading, setCustomPhaseLoading] = useState(false);

  useEffect(() => {
    loadRoadmapData();
  }, []);

  // Timer countdown for active test
  useEffect(() => {
    if (!testActivePhase || testLoading || testResult || testTimeRemaining <= 0) return;
    const interval = setInterval(() => {
      setTestTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [testActivePhase, testLoading, testResult, testTimeRemaining]);

  // Confetti effect trigger on test passed
  const triggerConfetti = useCallback(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
    canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;

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

  async function loadRoadmapData() {
    setLoading(true);
    try {
      const [rData, tData] = await Promise.all([
        getCurrentRoadmap(),
        getTodayTasks().catch(() => null)
      ]);
      setRoadmap(rData);
      setTodayData(tData);
      if (rData) {
        setUserLevel(rData.user_level || 'Beginner');
        setHoursPerDay(rData.hours_per_day || 1);
        setDaysPerWeek(rData.days_per_week || 5);
        setLearningStyle(rData.preferred_learning_style || 'Hands-on');
        if (rData.phases && rData.phases.length > 0) {
          const firstId = rData.phases[0].id || (rData.phases[0] as any).phase_id || 'phase-1';
          setOpenPhaseId(firstId);
        }
      }
    } catch (err) {
      console.error('Failed to load roadmap:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateRoadmap(e?: React.FormEvent) {
    if (e) e.preventDefault();
    setActionLoading(true);
    playSound('click', soundEnabled);
    try {
      const newRoadmap = await generateRoadmap({
        user_level: userLevel,
        hours_per_day: hoursPerDay,
        days_per_week: daysPerWeek,
        preferred_learning_style: learningStyle
      });
      setRoadmap(newRoadmap);
      const tData = await getTodayTasks();
      setTodayData(tData);
      setShowPreferences(false);
      playSound('victory', soundEnabled);
    } catch (err) {
      console.error('Failed to generate roadmap:', err);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRecalculate() {
    setActionLoading(true);
    playSound('click', soundEnabled);
    try {
      const newRoadmap = await recalculateRoadmap();
      setRoadmap(newRoadmap);
      const tData = await getTodayTasks();
      setTodayData(tData);
      playSound('victory', soundEnabled);
    } catch (err) {
      console.error('Failed to recalculate roadmap:', err);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleSavePreferences(e?: React.FormEvent) {
    if (e) e.preventDefault();
    setActionLoading(true);
    playSound('click', soundEnabled);
    try {
      const updated = await updateRoadmapPreferences({
        hours_per_day: hoursPerDay,
        days_per_week: daysPerWeek,
        preferred_learning_style: learningStyle,
        user_level: userLevel,
        track_pace: trackPace
      });
      setRoadmap(updated);
      const tData = await getTodayTasks().catch(() => null);
      setTodayData(tData);
      setShowPreferences(false);
      playSound('victory', soundEnabled);
    } catch (err) {
      console.error('Failed to update roadmap preferences:', err);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleAddCustomMilestone(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!customPhaseTitle.trim()) return;
    setCustomPhaseLoading(true);
    playSound('click', soundEnabled);
    try {
      const topicsList = customPhaseTopics
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      const updated = await addCustomRoadmapPhase({
        title: customPhaseTitle.trim(),
        description: customPhaseDesc.trim() || undefined,
        topics: topicsList.length > 0 ? topicsList : undefined
      });
      setRoadmap(updated);
      setCustomPhaseTitle('');
      setCustomPhaseDesc('');
      setCustomPhaseTopics('');
      setShowAddCustomModal(false);
      setShowPreferences(false);
      playSound('victory', soundEnabled);
    } catch (err) {
      console.error('Failed to add custom roadmap level:', err);
    } finally {
      setCustomPhaseLoading(false);
    }
  }

  async function handleToggleTask(taskId: string, isCompleted: boolean) {
    if (!roadmap) return;
    playSound('select', soundEnabled);
    try {
      let progressRes;
      if (isCompleted) {
        progressRes = await uncompleteRoadmapTask(taskId);
      } else {
        progressRes = await completeRoadmapTask(taskId);
      }

      const updatedCompletedIds = isCompleted
        ? roadmap.completed_task_ids.filter((id) => id !== taskId)
        : [...roadmap.completed_task_ids, taskId];

      const updatedPhases = roadmap.phases.map((ph) => ({
        ...ph,
        tasks: (ph as any).tasks?.map((t: any) =>
          t.id === taskId ? { ...t, is_completed: !isCompleted, completed: !isCompleted } : t
        ) || []
      }));

      setRoadmap({
        ...roadmap,
        overall_progress_percent: progressRes.overall_progress_percent,
        completed_task_ids: updatedCompletedIds,
        phases: updatedPhases
      });

      if (selectedPhase) {
        const found = updatedPhases.find(
          (p) => (p.id || p.phase_id) === (selectedPhase.id || selectedPhase.phase_id)
        );
        if (found) setSelectedPhase(found);
      }

      getTodayTasks().then(setTodayData).catch(() => {});
    } catch (err) {
      console.error('Failed to toggle task completion:', err);
    }
  }

  // Handle clicking on a level node in the World Map
  function handleNodeClick(phase: RoadmapPhase, idx: number) {
    const isUnlocked = idx === 0 || phase.is_unlocked;
    if (!isUnlocked) {
      playSound('fail', soundEnabled);
      setLockedAlertPhase(phase);
      return;
    }
    playSound('click', soundEnabled);
    setSelectedPhase(phase);
    setActiveTab('learn');
  }

  // Start AI Level Test
  async function handleStartLevelTest(phase: RoadmapPhase) {
    const pid = phase.id || phase.phase_id || `phase-${phase.phase_number || 1}`;
    setTestActivePhase(phase);
    setTestLoading(true);
    setTestData(null);
    setTestAnswers({});
    setTestCurrentIndex(0);
    setFlaggedQuestions({});
    setTestResult(null);
    setShowTestReview(false);
    setTestTimeRemaining(600);
    playSound('click', soundEnabled);

    try {
      const data = await generateLevelTest(pid);
      setTestData(data);
    } catch (err) {
      console.error('Failed to generate level test:', err);
    } finally {
      setTestLoading(false);
    }
  }

  // Submit AI Level Test
  async function handleSubmitLevelTest() {
    if (!testActivePhase || !testData) return;
    const pid = testActivePhase.id || testActivePhase.phase_id || `phase-${testActivePhase.phase_number || 1}`;
    setTestSubmitting(true);

    try {
      const res = await submitLevelTest(pid, testAnswers);
      setTestResult(res);

      if (res.passed) {
        playSound('victory', soundEnabled);
        setTimeout(() => triggerConfetti(), 150);
        await loadRoadmapData();
      } else {
        playSound('fail', soundEnabled);
      }
    } catch (err) {
      console.error('Failed to submit level test:', err);
    } finally {
      setTestSubmitting(false);
    }
  }

  // Copy code snippet to clipboard helper
  function handleCopySnippet(code: string) {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  }

  // Computed phase levels with names & lock status (Completely flexible to any user's tailored track)
  const mappedPhases = useMemo(() => {
    if (!roadmap || !roadmap.phases) return [];
    
    const basePhases = [...roadmap.phases];
    let prevPassed = true;

    return basePhases.map((ph, idx) => {
      const std = STANDARD_LEVEL_NAMES[idx % STANDARD_LEVEL_NAMES.length];
      const pNum = ph.phase_number || idx + 1;
      const isTestPassed = Boolean(ph.test_passed);
      const isUnlocked = idx === 0 || ph.is_unlocked || prevPassed;
      prevPassed = isTestPassed;

      const pTasks = ph.tasks || [];
      const completedCount = pTasks.filter((t: any) => t.is_completed || t.completed).length;
      const pct = pTasks.length > 0 ? Math.round((completedCount / pTasks.length) * 100) : 0;

      // Status determination
      let status: 'completed' | 'in_progress' | 'locked' = 'locked';
      if (isTestPassed || (isUnlocked && pct === 100)) {
        status = 'completed';
      } else if (isUnlocked) {
        status = 'in_progress';
      }

      // Star calculation
      let stars = ph.stars || 0;
      if (!stars && ph.test_score) {
        stars = ph.test_score >= 95 ? 3 : ph.test_score >= 80 ? 2 : ph.test_score >= 70 ? 1 : 0;
      }

      return {
        ...ph,
        phase_number: pNum,
        level_name: ph.level_name || ph.title || ph.name || std.name,
        level_theme: ph.level_theme || ph.description || std.theme,
        is_unlocked: isUnlocked,
        test_passed: isTestPassed,
        progress_percent: pct,
        status,
        stars,
        xp_reward: ph.xp_reward || (isTestPassed ? 100 : 100),
      };
    });
  }, [roadmap]);

  // Dynamically compute zigzag coordinates & SVG trail for ANY number of phases
  const dynamicLayout = useMemo(() => {
    return computeDynamicZigzagLayout(mappedPhases.length || 1);
  }, [mappedPhases.length]);

  // Find active / highest unlocked level
  const activeLevelPhase = useMemo(() => {
    return (
      mappedPhases.find((p) => p.status === 'in_progress') ||
      mappedPhases[mappedPhases.length - 1] ||
      mappedPhases[0]
    );
  }, [mappedPhases]);

  // Gamification metrics
  const totalXp = roadmap?.total_xp || (mappedPhases.filter((p) => p.test_passed).length * 100 + (roadmap?.completed_task_ids?.length || 0) * 20);
  const adventurerLevel = roadmap?.adventurer_level || Math.max(1, Math.floor(totalXp / 250) + 1);
  const nextLevelXpTarget = adventurerLevel * 250;
  const currentLevelBaseXp = (adventurerLevel - 1) * 250;
  const xpProgressPercent = Math.min(100, Math.max(0, Math.round(((totalXp - currentLevelBaseXp) / 250) * 100)));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-3">
          <RefreshCw className="w-8 h-8 text-[#2563EB] animate-spin" />
          <p className="text-[#64748B] dark:text-[#A8B3C2] text-sm font-medium">Calibrating your career roadmap & world map...</p>
        </div>
      </div>
    );
  }

  // Setup Screen if no roadmap exists
  if (!roadmap) {
    return (
      <div className="max-w-3xl mx-auto py-8 space-y-6">
        <div className="p-8 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] text-center space-y-3 shadow-sm">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#2563EB]/15 border border-[#2563EB]/30 text-[#17324D] dark:text-[#38BDF8] text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>AI Career World Map</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#0F172A] dark:text-[#F1F5F9] tracking-tight">Create Your Career World Map</h1>
          <p className="text-[#64748B] dark:text-[#A8B3C2] text-sm max-w-xl mx-auto">
            Build a gamified, level-by-level curriculum derived from your target career, verified skills, and skill gaps. Pass AI tests at each level to unlock the path forward!
          </p>
        </div>

        <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-6">
          <button
            type="button"
            onClick={() => handleGenerateRoadmap()}
            disabled={actionLoading}
            className="w-full py-4 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white font-bold text-sm shadow-sm transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            {actionLoading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin text-white" />
                <span>Generating Your World Map...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-[#2563EB]" />
                <span>Initialize Career World Map (Recommended)</span>
                <ArrowRight className="w-4 h-4 text-[#2563EB]" />
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16 relative">
      {/* Hidden Confetti Canvas Overlay */}
      <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-[70]" />

      {/* Top Banner & Gamification Controls */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <h1 className="text-2xl font-extrabold text-[#0F172A] dark:text-[#F1F5F9] tracking-tight flex items-center space-x-2">
              <span>🗺️ Career World Map</span>
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#2563EB]/15 text-[#17324D] dark:text-[#38BDF8] border border-[#2563EB]/30">
              {roadmap.target_role}
            </span>
          </div>
          <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">
            Step-by-step career quest • Pass AI tests to advance levels • Est. Duration: <strong className="text-[#0F172A] dark:text-[#F1F5F9]">{roadmap.total_estimated_weeks} weeks</strong>
          </p>
        </div>

        {/* View Toggle & Sound Controls */}
        <div className="flex items-center flex-wrap gap-2">
          {/* Sound Synthesizer Toggle */}
          <button
            onClick={() => {
              setSoundEnabled(!soundEnabled);
              playSound('click', !soundEnabled);
            }}
            title={soundEnabled ? 'Mute Game Sounds' : 'Enable Game Sounds'}
            className="p-2 rounded-xl bg-[#F1F5F9] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
          >
            {soundEnabled ? <Volume2 className="w-4 h-4 text-emerald-500" /> : <VolumeX className="w-4 h-4 text-slate-400" />}
          </button>

          {/* World Map vs Curriculum Toggle */}
          <div className="flex items-center bg-[#F1F5F9] dark:bg-[#0F172A] p-1 rounded-xl border border-[#E2E8F0] dark:border-[#334155]">
            <button
              onClick={() => {
                setViewMode('map');
                playSound('click', soundEnabled);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
                viewMode === 'map'
                  ? 'bg-white dark:bg-[#172235] text-[#2563EB] shadow-xs'
                  : 'text-[#64748B] dark:text-[#A8B3C2] hover:text-[#0F172A] dark:hover:text-white'
              }`}
            >
              <MapIcon className="w-3.5 h-3.5" />
              <span>World Map</span>
            </button>
            <button
              onClick={() => {
                setViewMode('curriculum');
                playSound('click', soundEnabled);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
                viewMode === 'curriculum'
                  ? 'bg-white dark:bg-[#172235] text-[#2563EB] shadow-xs'
                  : 'text-[#64748B] dark:text-[#A8B3C2] hover:text-[#0F172A] dark:hover:text-white'
              }`}
            >
              <ListChecks className="w-3.5 h-3.5" />
              <span>Syllabus View</span>
            </button>
          </div>

          {/* Minimal Design vs Labels Toggle */}
          {viewMode === 'map' && (
            <button
              onClick={() => {
                setShowLabels(!showLabels);
                playSound('click', soundEnabled);
              }}
              title={showLabels ? 'Switch to pure minimal design (numbers only)' : 'Show level title labels'}
              className="px-3 py-1.5 rounded-xl bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] text-xs font-semibold hover:bg-black/5 dark:hover:bg-white/5 transition flex items-center space-x-1.5 text-slate-700 dark:text-slate-200"
            >
              {showLabels ? <EyeOff className="w-3.5 h-3.5 text-rose-500" /> : <Eye className="w-3.5 h-3.5 text-rose-500" />}
              <span>{showLabels ? 'Minimal Style' : 'Show Labels'}</span>
            </button>
          )}

          {/* Add Custom Level Milestone Button */}
          <button
            onClick={() => {
              setShowAddCustomModal(true);
              playSound('click', soundEnabled);
            }}
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-[#ff4d4f]/15 to-rose-500/10 hover:from-[#ff4d4f]/25 hover:to-rose-500/20 border border-[#ff4d4f]/40 text-xs font-bold text-[#ff4d4f] hover:text-[#ff7875] transition flex items-center space-x-1.5 shadow-xs"
            title="Add a custom milestone or personalized level to your roadmap"
          >
            <Plus className="w-3.5 h-3.5 text-[#ff4d4f]" />
            <span>+ Add Level</span>
          </button>

          <button
            onClick={() => {
              setShowPreferences(!showPreferences);
              playSound('click', soundEnabled);
            }}
            className="px-3 py-1.5 rounded-xl bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] text-xs font-semibold hover:bg-black/5 dark:hover:bg-white/5 transition flex items-center space-x-1.5 text-slate-700 dark:text-slate-200"
          >
            <Sliders className="w-3.5 h-3.5 text-slate-400" />
            <span>Roadmap Pace</span>
          </button>
          <button
            onClick={handleRecalculate}
            disabled={actionLoading}
            className="px-3.5 py-1.5 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white text-xs font-semibold flex items-center space-x-1 shadow-sm transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            <span>Recalculate</span>
          </button>
        </div>
      </div>

      {/* Gamified Player Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Adventurer Level & XP */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-950/20 via-white to-white dark:from-indigo-950/40 dark:via-[#172235] dark:to-[#172235] border border-indigo-500/20 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-black text-xs">
                Lvl {adventurerLevel}
              </div>
              <div>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">Explorer Rank</span>
                <span className="text-xs font-extrabold text-[#0F172A] dark:text-white">
                  {adventurerLevel === 1 ? 'Novice Trainee' : adventurerLevel === 2 ? 'Code Pioneer' : adventurerLevel === 3 ? 'Architecture Scout' : 'Master Engineer'}
                </span>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs font-black text-indigo-400">{totalXp} XP</span>
              <span className="text-[10px] text-slate-400 block">/ {nextLevelXpTarget} XP</span>
            </div>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-200 dark:border-slate-800">
            <div 
              className="bg-indigo-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${xpProgressPercent}%` }}
            />
          </div>
        </div>

        {/* Current Active Quest Level */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] text-amber-500 font-extrabold uppercase tracking-wider flex items-center space-x-1">
              <Flame className="w-3.5 h-3.5 text-amber-500" />
              <span>Current Quest Level</span>
            </span>
            <div className="text-sm font-extrabold text-[#0F172A] dark:text-[#F1F5F9] mt-0.5">
              {activeLevelPhase?.level_name || 'Level 1: Spawn Point'}
            </div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              Level {activeLevelPhase?.phase_number || 1} • {activeLevelPhase?.level_theme}
            </span>
          </div>
          <button
            onClick={() => activeLevelPhase && handleNodeClick(activeLevelPhase, (activeLevelPhase.phase_number || 1) - 1)}
            className="px-3 py-1.5 bg-[#2563EB] hover:bg-[#1d4ed8] text-white text-xs font-bold rounded-xl transition shadow-sm"
          >
            Enter Level →
          </button>
        </div>

        {/* Level Test Gatekeeper Status */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] text-emerald-500 font-extrabold uppercase tracking-wider flex items-center space-x-1">
              <Award className="w-3.5 h-3.5 text-emerald-500" />
              <span>AI Gatekeeper Test</span>
            </span>
            <div className="text-sm font-extrabold text-[#0F172A] dark:text-[#F1F5F9] mt-0.5">
              {activeLevelPhase?.test_passed ? 'Mastery Verified 🏆' : 'Pass Test to Advance ⚔️'}
            </div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              Pass with 70%+ • Earn up to 3 ⭐ Stars
            </span>
          </div>
          {activeLevelPhase && (
            <button
              onClick={() => handleStartLevelTest(activeLevelPhase)}
              className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-900 font-black text-xs rounded-xl transition flex items-center space-x-1 shadow-sm"
            >
              <Zap className="w-3.5 h-3.5 text-slate-900" />
              <span>{activeLevelPhase.test_passed ? 'Retake' : 'Take Test'}</span>
            </button>
          )}
        </div>
      </div>

      {/* ============================================================== */}
      {/* 1. GAMIFIED WORLD MAP VIEW (Exact Neon Zig-Zag Design)          */}
      {/* ============================================================== */}
      {viewMode === 'map' && (
        <div className="relative rounded-3xl bg-[#18181b] border border-[#27272a] shadow-2xl overflow-hidden p-6 sm:p-8">
          {/* Map Header with choose-a-level dropdown & minimal mode badge */}
          <div className="flex items-center justify-between mb-5 z-10 relative">
            <div className="flex items-center space-x-2.5">
              <span className="w-3 h-3 rounded-full bg-[#ff4d4f] inline-block shadow-[0_0_10px_#ff4d4f]" />
              <div>
                <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide flex items-center space-x-2">
                  <span>Interactive Career Trail</span>
                </h2>
                <span className="text-xs text-slate-400">
                  Follow the numbered path • Pass AI tests at each stage to unlock higher milestones
                </span>
              </div>
            </div>

            {/* Quick Level Selector */}
            <div className="relative group">
              <select
                onChange={(e) => {
                  const idx = parseInt(e.target.value);
                  if (mappedPhases[idx]) handleNodeClick(mappedPhases[idx], idx);
                }}
                className="appearance-none bg-[#27272a]/90 hover:bg-[#27272a] text-slate-200 text-xs font-semibold px-3.5 py-1.5 pr-8 rounded-xl border border-slate-700/80 cursor-pointer focus:outline-none"
                defaultValue=""
              >
                <option value="" disabled>Jump to level ▾</option>
                {mappedPhases.map((ph, idx) => (
                  <option key={idx} value={idx}>
                    Level {ph.phase_number}: {ph.level_name} ({ph.status === 'completed' ? '✓ Mastered' : ph.status === 'in_progress' ? 'In Progress' : 'Locked'})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* World Map Interactive Canvas (Matching the Reference Image & Fully Dynamic) */}
          <div 
            style={{ aspectRatio: `800 / ${dynamicLayout.totalHeight}` }}
            className="relative w-full max-w-[760px] mx-auto rounded-2xl overflow-hidden bg-[#141416] border border-[#27272a]/60 select-none shadow-inner pb-6"
          >
            {/* Ambient Dark Charcoal Background with subtle vignette */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-[#141416]/50 to-[#0e0e10] pointer-events-none" />

            {/* SVG Connecting Trail (Exact Straight Dashed Red Lines) */}
            <svg 
              className="absolute inset-0 w-full h-full pointer-events-none" 
              viewBox={dynamicLayout.viewBox}
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                <filter id="neonRedGlow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
                <filter id="neonRedGlowWide" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="7" result="coloredBlurWide"/>
                  <feMerge>
                    <feMergeNode in="coloredBlurWide"/>
                  </feMerge>
                </filter>
              </defs>

              {/* Ambient Glow Trail */}
              <path
                d={dynamicLayout.pathD}
                fill="none"
                stroke="#ff4d4f"
                strokeWidth="9"
                strokeDasharray="10 10"
                strokeLinecap="round"
                className="opacity-20"
                filter="url(#neonRedGlowWide)"
              />

              {/* Sharp Neon Coral/Red Dashed Trail */}
              <path
                d={dynamicLayout.pathD}
                fill="none"
                stroke="#ff4d4f"
                strokeWidth="3.5"
                strokeDasharray="10 10"
                strokeLinecap="round"
                filter="url(#neonRedGlow)"
                className="opacity-95"
              />
            </svg>

            {/* Render Numbered Level Nodes (1 to N) at Dynamically Computed Coordinates */}
            {mappedPhases.map((phase, idx) => {
              const coords = dynamicLayout.coordinates[idx] || { x: 400, y: 125 + idx * 135 };
              const isCompleted = phase.status === 'completed';
              const isCurrent = phase.status === 'in_progress';

              const leftPct = (coords.x / 800) * 100;
              const topPct = (coords.y / dynamicLayout.totalHeight) * 100;

              return (
                <div
                  key={idx}
                  style={{ left: `${leftPct}%`, top: `${topPct}%` }}
                  className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center group cursor-pointer select-none z-10"
                  onClick={() => handleNodeClick(phase, idx)}
                  onMouseEnter={() => setHoveredPhase(phase)}
                  onMouseLeave={() => setHoveredPhase(null)}
                >
                  {/* Floating Player Pin on active level - Plenty of headroom so never cut off */}
                  {isCurrent && (
                    <div className="absolute -top-10 z-20 flex flex-col items-center animate-bounce pointer-events-none">
                      <span className="px-2.5 py-0.5 rounded-full bg-[#ff4d4f] text-white font-black text-[10px] shadow-[0_0_12px_rgba(255,77,79,0.7)] flex items-center space-x-1 whitespace-nowrap">
                        <MapPin className="w-3 h-3 fill-white" />
                        <span>Active Level</span>
                      </span>
                      <div className="w-1.5 h-1.5 bg-[#ff4d4f] rotate-45 -mt-1" />
                    </div>
                  )}

                  {/* Circular Node Button (Exact Neon-Red Glow Style) */}
                  <div className="relative">
                    {/* Pulsing ring for current level */}
                    {isCurrent && (
                      <div className="absolute -inset-2.5 rounded-full bg-[#ff4d4f]/30 animate-ping pointer-events-none" />
                    )}

                    <button
                      type="button"
                      style={{
                        background: '#1c1c1e',
                        borderColor: '#ff4d4f',
                        boxShadow: isCurrent
                          ? '0 0 24px 4px rgba(255, 77, 79, 0.75), inset 0 0 12px rgba(255, 77, 79, 0.25)'
                          : '0 0 16px 2px rgba(255, 77, 79, 0.45), inset 0 0 8px rgba(255, 77, 79, 0.15)',
                      }}
                      className="w-16 h-16 sm:w-20 sm:h-20 rounded-full border-2 flex items-center justify-center transition-all duration-300 transform group-hover:scale-110 group-hover:shadow-[0_0_30px_6px_rgba(255,77,79,0.85)] cursor-pointer"
                    >
                      <span
                        className="font-bold sm:font-black text-2xl sm:text-3xl font-mono text-[#ff4d4f]"
                        style={{ textShadow: '0 0 10px rgba(255, 77, 79, 0.65)' }}
                      >
                        {phase.phase_number}
                      </span>
                    </button>

                    {/* Completed Checkmark Badge */}
                    {isCompleted && (
                      <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 border-2 border-[#1c1c1e] text-white flex items-center justify-center shadow-[0_0_10px_rgba(16,185,129,0.7)]">
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    )}

                    {/* Locked Lock Badge */}
                    {!phase.is_unlocked && (
                      <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-slate-800 border-2 border-[#1c1c1e] text-slate-400 flex items-center justify-center shadow-md">
                        <Lock className="w-3 h-3 text-slate-400" />
                      </div>
                    )}
                  </div>

                  {/* Level Title & Subtitle (Toggleable with 'showLabels') */}
                  {showLabels && (
                    <div className="mt-2 text-center pointer-events-none max-w-[120px]">
                      <div className="text-[11px] sm:text-xs font-bold text-slate-200 tracking-tight drop-shadow truncate">
                        {phase.level_name}
                      </div>
                      <div className="mt-0.5">
                        {isCompleted ? (
                          <span className="text-[9px] font-semibold text-emerald-400">Mastered ✓</span>
                        ) : isCurrent ? (
                          <span className="text-[9px] font-semibold text-[#ff4d4f] animate-pulse">In Progress</span>
                        ) : (
                          <span className="text-[9px] font-medium text-slate-500">Locked</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Continuation "..." node at bottom connecting seamlessly */}
            {(() => {
              const coords = dynamicLayout.continuationCoord;
              const leftPct = (coords.x / 800) * 100;
              const topPct = (coords.y / dynamicLayout.totalHeight) * 100;

              return (
                <div
                  style={{ left: `${leftPct}%`, top: `${topPct}%` }}
                  className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center group cursor-pointer select-none z-10"
                  onClick={() => setShowFutureMilestonesModal(true)}
                  title={`Click to view horizons beyond Level ${mappedPhases.length}`}
                >
                  <div className="relative">
                    <button
                      type="button"
                      style={{
                        background: '#1c1c1e',
                        borderColor: 'rgba(255, 77, 79, 0.65)',
                        boxShadow: '0 0 14px 1px rgba(255, 77, 79, 0.25)',
                      }}
                      className="w-16 h-16 sm:w-20 sm:h-20 rounded-full border-2 border-dashed flex items-center justify-center transition-all duration-300 transform group-hover:scale-110 group-hover:shadow-[0_0_24px_3px_rgba(255,77,79,0.6)] cursor-pointer"
                    >
                      <span
                        className="font-bold sm:font-black text-xl sm:text-2xl font-mono text-[#ff4d4f]/80 pb-1 tracking-widest"
                        style={{ textShadow: '0 0 8px rgba(255, 77, 79, 0.5)' }}
                      >
                        ...
                      </span>
                    </button>
                  </div>

                  {showLabels && (
                    <div className="mt-2 text-center pointer-events-none max-w-[120px]">
                      <div className="text-[11px] sm:text-xs font-semibold text-slate-400">
                        Beyond Level {mappedPhases.length}
                      </div>
                      <span className="text-[9px] text-slate-500">Continuous Horizons</span>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>

          {/* Map Footer Legend */}
          <div className="mt-6 pt-4 border-t border-[#27272a] flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-medium">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full border border-[#ff4d4f] bg-[#1c1c1e] shadow-[0_0_8px_rgba(255,77,79,0.6)] inline-block" />
              <span className="text-slate-300">Career Level Node</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-4 h-0.5 border-t-2 border-dashed border-[#ff4d4f] inline-block" />
              <span className="text-slate-300">Winding Progression Trail</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full border border-dashed border-[#ff4d4f]/60 bg-[#1c1c1e] inline-block" />
              <span className="text-slate-300">Continuous Horizons (...)</span>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 2. SYLLABUS / CURRICULUM VIEW (Detailed Accordion)             */}
      {/* ============================================================== */}
      {viewMode === 'curriculum' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#0F172A] dark:text-[#F1F5F9] flex items-center space-x-2">
              <Layers className="w-5 h-5 text-[#2563EB]" />
              <span>Full Roadmap Curriculum & Level Tests</span>
            </h2>
          </div>

          {mappedPhases.map((phase, idx) => {
            const phaseId = phase.id || phase.phase_id || `phase-${idx + 1}`;
            const isOpen = openPhaseId === phaseId;
            const phaseTasks = phase.tasks || [];
            const completedCount = phaseTasks.filter((t: any) => t.is_completed || t.completed).length;

            return (
              <div 
                key={phaseId} 
                className={`rounded-2xl border transition-all ${
                  phase.is_unlocked 
                    ? 'bg-white dark:bg-[#172235] border-[#E2E8F0] dark:border-[#334155]' 
                    : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 opacity-80'
                }`}
              >
                <button
                  onClick={() => {
                    if (!phase.is_unlocked) {
                      playSound('fail', soundEnabled);
                      setLockedAlertPhase(phase);
                      return;
                    }
                    playSound('click', soundEnabled);
                    setOpenPhaseId(isOpen ? '' : phaseId);
                  }}
                  className="w-full p-5 text-left flex items-center justify-between transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                      phase.test_passed
                        ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
                        : phase.is_unlocked
                        ? 'bg-amber-500/15 text-amber-500 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-500 border border-slate-700'
                    }`}>
                      {phase.test_passed ? '✓' : phase.is_unlocked ? idx + 1 : <Lock className="w-4 h-4" />}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-[#2563EB] uppercase">Level {idx + 1}: {phase.level_name}</span>
                        {phase.test_passed && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 flex items-center space-x-1">
                            <span>Score: {phase.test_score || 100}%</span>
                            <span className="text-amber-400">{'⭐'.repeat(phase.stars || 1)}</span>
                          </span>
                        )}
                        {!phase.is_unlocked && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-400">
                            Locked
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-bold text-[#0F172A] dark:text-[#F1F5F9] mt-0.5">
                        {phase.title || phase.name}
                      </h3>
                      <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-0.5">{phase.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right hidden sm:block">
                      <span className="text-xs font-semibold text-[#2563EB]">
                        {completedCount}/{phaseTasks.length} tasks completed
                      </span>
                    </div>
                    {phase.is_unlocked ? (
                      isOpen ? <ChevronUp className="w-5 h-5 text-[#64748B]" /> : <ChevronDown className="w-5 h-5 text-[#64748B]" />
                    ) : (
                      <Lock className="w-5 h-5 text-amber-500" />
                    )}
                  </div>
                </button>

                {isOpen && phase.is_unlocked && (
                  <div className="p-6 border-t border-[#E2E8F0] dark:border-[#334155] space-y-6 bg-[#F8FAFC] dark:bg-[#0F172A]/50">
                    {/* Gatekeeper Test Card */}
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                      <div>
                        <h4 className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                          <Zap className="w-3.5 h-3.5" />
                          <span>Level {idx + 1} Advancement Gatekeeper</span>
                        </h4>
                        <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-0.5">
                          {phase.test_passed 
                            ? `Level mastery verified with ${phase.test_score || 100}%! Retake anytime to refresh knowledge.`
                            : `Pass this AI test with 70%+ to unlock Level ${idx + 2} on your World Map.`
                          }
                        </p>
                      </div>
                      <button
                        onClick={() => handleStartLevelTest(phase)}
                        className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-900 font-extrabold text-xs rounded-xl shadow-xs transition flex items-center space-x-1.5 flex-shrink-0"
                      >
                        <Zap className="w-3.5 h-3.5" />
                        <span>{phase.test_passed ? 'Retake AI Test' : 'Take AI Test Now'}</span>
                      </button>
                    </div>

                    {/* Detailed Syllabus & Tasks */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-[#64748B] dark:text-[#A8B3C2] uppercase tracking-wider">
                        Learning Tasks & Syllabus ({phaseTasks.length})
                      </h4>
                      <div className="space-y-2">
                        {phaseTasks.map((task: any) => (
                          <div
                            key={task.id}
                            className="p-4 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] flex items-start justify-between space-x-3"
                          >
                            <div className="flex items-start space-x-3">
                              <button
                                onClick={() => handleToggleTask(task.id, task.is_completed || task.completed)}
                                className="mt-0.5 text-[#2563EB]"
                              >
                                {task.is_completed || task.completed ? (
                                  <CheckCircle2 className="w-5 h-5 text-[#2E7D5B]" />
                                ) : (
                                  <Square className="w-5 h-5 text-[#64748B]" />
                                )}
                              </button>
                              <div>
                                <h5 className={`text-sm font-semibold ${(task.is_completed || task.completed) ? 'line-through text-[#64748B]' : 'text-[#0F172A] dark:text-[#F1F5F9]'}`}>
                                  {task.title}
                                </h5>
                                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-0.5">{task.description}</p>
                                {task.topics_to_learn && task.topics_to_learn.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {task.topics_to_learn.map((sub: string, sIdx: number) => (
                                      <span key={sIdx} className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                                        • {sub}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                            <span className="text-[11px] text-[#64748B] dark:text-[#A8B3C2] flex-shrink-0">
                              {task.estimated_minutes} min
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ============================================================== */}
      {/* 3. LEVEL DETAILS MODAL (3-Step Loop: Learn -> Practice -> Test) */}
      {/* ============================================================== */}
      {selectedPhase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-[#172235] border border-slate-200 dark:border-slate-700 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 sm:p-8 space-y-6">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-[#2563EB] uppercase tracking-wider">
                    Level {selectedPhase.phase_number || 1} • {selectedPhase.level_name}
                  </span>
                  {selectedPhase.test_passed ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
                      ✓ Mastered ({selectedPhase.test_score || 100}%)
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-500 border border-amber-500/30">
                      In Progress
                    </span>
                  )}
                </div>
                <h3 className="text-2xl font-black text-[#0F172A] dark:text-[#F1F5F9] mt-1">
                  {selectedPhase.title || selectedPhase.name}
                </h3>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-0.5">
                  {selectedPhase.description || selectedPhase.level_theme}
                </p>
              </div>
              <button
                onClick={() => setSelectedPhase(null)}
                className="p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 3-Step Action Tabs: Learn, Practice, Test */}
            <div className="grid grid-cols-3 gap-2 p-1.5 rounded-2xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-bold">
              <button
                onClick={() => setActiveTab('learn')}
                className={`py-2 px-3 rounded-xl transition flex items-center justify-center space-x-1.5 ${
                  activeTab === 'learn'
                    ? 'bg-white dark:bg-[#172235] text-[#2563EB] shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>1. Learn</span>
              </button>
              <button
                onClick={() => setActiveTab('practice')}
                className={`py-2 px-3 rounded-xl transition flex items-center justify-center space-x-1.5 ${
                  activeTab === 'practice'
                    ? 'bg-white dark:bg-[#172235] text-[#2563EB] shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Code className="w-3.5 h-3.5" />
                <span>2. Practice</span>
              </button>
              <button
                onClick={() => setActiveTab('test')}
                className={`py-2 px-3 rounded-xl transition flex items-center justify-center space-x-1.5 ${
                  activeTab === 'test'
                    ? 'bg-white dark:bg-[#172235] text-amber-500 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                <span>3. Level Test</span>
              </button>
            </div>

            {/* TAB 1: LEARN (Syllabus & Core Concepts) */}
            {activeTab === 'learn' && (
              <div className="space-y-4">
                {/* Learning Objectives */}
                {selectedPhase.learning_objectives && selectedPhase.learning_objectives.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2">
                    <h4 className="text-xs font-bold text-[#2563EB] uppercase tracking-wider flex items-center space-x-1.5">
                      <Target className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span>Key Objectives for this Level</span>
                    </h4>
                    <ul className="space-y-1.5 text-xs text-[#0F172A] dark:text-[#F1F5F9]">
                      {selectedPhase.learning_objectives.map((obj: string, oIdx: number) => (
                        <li key={oIdx} className="flex items-start space-x-2">
                          <span className="text-[#2563EB] font-bold">•</span>
                          <span>{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Topics & Concepts Checklist */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <ListChecks className="w-3.5 h-3.5 text-[#2563EB]" />
                    <span>Concepts to Master (Syllabus)</span>
                  </h4>
                  <div className="space-y-2">
                    {(selectedPhase.tasks || []).map((task: any) => (
                      <div
                        key={task.id}
                        className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 flex items-start justify-between"
                      >
                        <div className="flex items-start space-x-3">
                          <button
                            onClick={() => handleToggleTask(task.id, task.is_completed || task.completed)}
                            className="mt-0.5 text-[#2563EB]"
                          >
                            {task.is_completed || task.completed ? (
                              <CheckCircle2 className="w-5 h-5 text-[#2E7D5B]" />
                            ) : (
                              <Square className="w-5 h-5 text-[#64748B]" />
                            )}
                          </button>
                          <div>
                            <h5 className={`text-sm font-semibold ${(task.is_completed || task.completed) ? 'line-through text-slate-400' : 'text-slate-900 dark:text-white'}`}>
                              {task.title}
                            </h5>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{task.description}</p>
                            {task.topics_to_learn && task.topics_to_learn.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {task.topics_to_learn.map((sub: string, sIdx: number) => (
                                  <span key={sIdx} className="text-[10px] px-2 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                                    • {sub}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <span className="text-[11px] text-slate-400 flex-shrink-0">
                          {task.estimated_minutes}m
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: PRACTICE (Hands-on Coding Tasks) */}
            {activeTab === 'practice' && (
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <Code className="w-3.5 h-3.5" />
                      <span>Hands-on Practice Sandbox</span>
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Reinforce topics before taking the gatekeeper AI test. Practice questions in our dedicated Micro Practice Engine.
                  </p>
                </div>

                {/* Practice Goals from tasks */}
                <div className="space-y-2.5">
                  {(selectedPhase.tasks || []).map((task: any, tIdx: number) => (
                    <div
                      key={task.id || tIdx}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900 dark:text-white">{task.title}</span>
                        <a
                          href={`/practice?topic=${encodeURIComponent(task.title)}`}
                          className="px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-bold transition flex items-center space-x-1"
                        >
                          <span>Practice Topic</span>
                          <ArrowRight className="w-3 h-3" />
                        </a>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {task.practice_goal || task.practice_exercise || 'Build a working sample demonstrating this concept.'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: LEVEL TEST (Gatekeeper AI Test & Star Rewards) */}
            {activeTab === 'test' && (
              <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-400 text-xs font-black uppercase tracking-wider">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span>Level Gatekeeper Assessment</span>
                  </div>
                  <span className="text-xs font-black text-amber-500">
                    Reward: +100 XP & up to 3 ⭐
                  </span>
                </div>

                <div className="space-y-1.5">
                  <h4 className="text-base font-extrabold text-slate-900 dark:text-white">
                    {selectedPhase.test_passed ? 'Mastery Already Verified! 🏆' : 'Ready to unlock the next level?'}
                  </h4>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    {selectedPhase.test_passed
                      ? `You passed this level test with ${selectedPhase.test_score || 100}%. Retake the AI test anytime with fresh questions to keep your skills sharp.`
                      : 'Our AI evaluates your understanding across scenario questions, code analysis, and best practices. Score 70% or higher to unlock the next level!'
                    }
                  </p>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => {
                      setSelectedPhase(null);
                      handleStartLevelTest(selectedPhase);
                    }}
                    className="w-full py-3.5 bg-amber-500 hover:bg-amber-600 text-slate-900 font-black text-sm rounded-xl shadow-lg transition flex items-center justify-center space-x-2"
                  >
                    <Zap className="w-4 h-4 text-slate-900" />
                    <span>{selectedPhase.test_passed ? 'Retake AI Level Test (Fresh Questions)' : 'Start AI Level Test Now'}</span>
                    <ArrowRight className="w-4 h-4 text-slate-900" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 4. LOCKED LEVEL ALERT MODAL                                    */}
      {/* ============================================================== */}
      {lockedAlertPhase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-[#172235] border border-slate-700 rounded-3xl max-w-md w-full p-6 text-center space-y-5 shadow-2xl">
            <div className="w-16 h-16 rounded-full bg-amber-500/15 border-2 border-amber-500/40 text-amber-500 flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(245,158,11,0.3)]">
              <Lock className="w-8 h-8" />
            </div>

            <div className="space-y-1.5">
              <span className="text-xs font-bold uppercase text-amber-400 tracking-wider">
                Level {lockedAlertPhase.phase_number} Locked 🔒
              </span>
              <h3 className="text-xl font-black text-white">
                {lockedAlertPhase.level_name}
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed max-w-xs mx-auto">
                Next level me jane se pahele aapko previous level ke topics ka AI test pass karna hoga (minimum 70% score).
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-left text-xs text-slate-400 space-y-1.5">
              <div className="font-bold text-slate-200">Requirements to Unlock:</div>
              <div>• Previous level ke learning concepts cover karein</div>
              <div>• AI Gatekeeper Test me 70%+ score karein (earn 1-3 ⭐)</div>
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <button
                onClick={() => setLockedAlertPhase(null)}
                className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition"
              >
                Close
              </button>
              {activeLevelPhase && (
                <button
                  onClick={() => {
                    setLockedAlertPhase(null);
                    handleStartLevelTest(activeLevelPhase);
                  }}
                  className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-900 font-extrabold text-xs transition flex items-center justify-center space-x-1"
                >
                  <Zap className="w-3.5 h-3.5 text-slate-900" />
                  <span>Take Previous Test</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 5. TOP-NOTCH AI LEVEL TEST RUNNER (Timer, Code Box, Flags)     */}
      {/* ============================================================== */}
      {testActivePhase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#172235] border border-slate-700 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl max-h-[92vh] overflow-y-auto">
            {/* Loading State */}
            {testLoading && (
              <div className="py-16 text-center space-y-4">
                <div className="w-14 h-14 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-lg font-black text-white">Synthesizing AI Level Test...</h4>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    AI is preparing 5 diverse questions (scenarios, code snippet analysis, and architectural principles) for {testActivePhase.level_name}.
                  </p>
                </div>
              </div>
            )}

            {/* Test Active Screen */}
            {!testLoading && testData && !testResult && (
              <div className="space-y-5">
                {/* Test Header with Timer & Close */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-wider text-amber-400 block">
                      Level {testData.phase_number} Gatekeeper Test • Pass Mark: 70%
                    </span>
                    <h3 className="text-lg sm:text-xl font-black text-white mt-0.5">
                      {testData.level_name}: {testData.phase_title}
                    </h3>
                  </div>

                  <div className="flex items-center space-x-3">
                    {/* Timer Badge */}
                    <div className={`px-2.5 py-1 rounded-lg border text-xs font-mono font-bold flex items-center space-x-1.5 ${
                      testTimeRemaining < 120 
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse'
                        : 'bg-slate-900 text-slate-300 border-slate-800'
                    }`}>
                      <Clock className="w-3.5 h-3.5" />
                      <span>
                        {Math.floor(testTimeRemaining / 60).toString().padStart(2, '0')}:
                        {(testTimeRemaining % 60).toString().padStart(2, '0')}
                      </span>
                    </div>

                    <button
                      onClick={() => setTestActivePhase(null)}
                      className="p-1 rounded-lg text-slate-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Question Navigation Pill Bar */}
                <div className="flex items-center justify-between gap-1 overflow-x-auto pb-1">
                  <div className="flex items-center space-x-1.5">
                    {testData.questions.map((q, qIdx) => {
                      const isAnswered = Boolean(testAnswers[q.id]);
                      const isFlagged = Boolean(flaggedQuestions[q.id]);
                      const isCurrent = testCurrentIndex === qIdx;

                      return (
                        <button
                          key={q.id}
                          onClick={() => {
                            playSound('click', soundEnabled);
                            setTestCurrentIndex(qIdx);
                          }}
                          className={`w-8 h-8 rounded-lg text-xs font-bold transition flex items-center justify-center relative ${
                            isCurrent
                              ? 'bg-amber-500 text-slate-900 ring-2 ring-amber-400 font-black'
                              : isAnswered
                              ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}
                        >
                          <span>{qIdx + 1}</span>
                          {isFlagged && (
                            <span className="w-2 h-2 rounded-full bg-rose-400 absolute -top-0.5 -right-0.5" />
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Flag for review toggle */}
                  {testData.questions[testCurrentIndex] && (
                    <button
                      onClick={() => {
                        const qId = testData.questions[testCurrentIndex].id;
                        setFlaggedQuestions((prev) => ({ ...prev, [qId]: !prev[qId] }));
                      }}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition flex items-center space-x-1 ${
                        flaggedQuestions[testData.questions[testCurrentIndex].id]
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
                      }`}
                    >
                      <Flag className="w-3 h-3" />
                      <span>{flaggedQuestions[testData.questions[testCurrentIndex].id] ? 'Flagged' : 'Flag'}</span>
                    </button>
                  )}
                </div>

                {/* Current Question Body */}
                {testData.questions[testCurrentIndex] && (
                  <div className="space-y-4">
                    <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
                      <div className="flex items-center space-x-2 flex-wrap gap-1">
                        <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                          {testData.questions[testCurrentIndex].topic}
                        </span>
                        {testData.questions[testCurrentIndex].difficulty && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            {testData.questions[testCurrentIndex].difficulty}
                          </span>
                        )}
                        {testData.questions[testCurrentIndex].question_type && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                            {testData.questions[testCurrentIndex].question_type.replace('_', ' ')}
                          </span>
                        )}
                      </div>

                      <h4 className="text-sm sm:text-base font-bold text-white leading-relaxed">
                        {testData.questions[testCurrentIndex].question}
                      </h4>

                      {/* Code Snippet Box with syntax styling */}
                      {testData.questions[testCurrentIndex].code_snippet && (
                        <div className="relative mt-2 rounded-xl bg-[#090D16] border border-slate-800 p-3 font-mono text-xs text-emerald-400 overflow-x-auto">
                          <button
                            onClick={() => handleCopySnippet(testData.questions[testCurrentIndex].code_snippet || '')}
                            className="absolute top-2 right-2 p-1 rounded bg-slate-800/80 text-slate-400 hover:text-white text-[10px] flex items-center space-x-1"
                          >
                            {copiedCode ? <CheckCheck className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            <span>{copiedCode ? 'Copied' : 'Copy'}</span>
                          </button>
                          <pre className="pr-12 leading-relaxed whitespace-pre">
                            {testData.questions[testCurrentIndex].code_snippet}
                          </pre>
                        </div>
                      )}
                    </div>

                    {/* 4 Interactive Choices */}
                    <div className="space-y-2.5">
                      {testData.questions[testCurrentIndex].options.map((opt, oIdx) => {
                        const qId = testData.questions[testCurrentIndex].id;
                        const isSelected = testAnswers[qId] === opt;
                        return (
                          <button
                            key={oIdx}
                            type="button"
                            onClick={() => {
                              playSound('select', soundEnabled);
                              setTestAnswers({ ...testAnswers, [qId]: opt });
                            }}
                            className={`w-full p-3.5 rounded-xl text-left text-xs sm:text-sm font-semibold transition border flex items-center justify-between ${
                              isSelected
                                ? 'bg-amber-500/20 border-amber-500 text-amber-200 shadow-md ring-1 ring-amber-400'
                                : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-200'
                            }`}
                          >
                            <span>{opt}</span>
                            {isSelected && <Check className="w-4 h-4 text-amber-400 flex-shrink-0 ml-2" />}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Footer Navigation & Submit */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                  <button
                    disabled={testCurrentIndex === 0}
                    onClick={() => {
                      playSound('click', soundEnabled);
                      setTestCurrentIndex(testCurrentIndex - 1);
                    }}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-bold text-white transition"
                  >
                    ← Previous
                  </button>

                  {testCurrentIndex < testData.questions.length - 1 ? (
                    <button
                      onClick={() => {
                        playSound('click', soundEnabled);
                        setTestCurrentIndex(testCurrentIndex + 1);
                      }}
                      className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white transition flex items-center space-x-1"
                    >
                      <span>Next Question</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={handleSubmitLevelTest}
                      disabled={testSubmitting || Object.keys(testAnswers).length < testData.questions.length}
                      className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-slate-900 font-black text-xs transition flex items-center space-x-1.5 shadow-lg"
                    >
                      {testSubmitting ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin text-slate-900" />
                          <span>AI Evaluating...</span>
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4 text-slate-900" />
                          <span>Submit Test for AI Evaluation</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Test Results Screen */}
            {testResult && (
              <div className="space-y-6 text-center">
                {/* Result Hero Header with Stars */}
                <div className="space-y-3">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto shadow-2xl ${
                    testResult.passed
                      ? 'bg-[#10B981]/20 border-4 border-[#10B981] text-[#10B981]'
                      : 'bg-rose-500/20 border-4 border-rose-500 text-rose-500'
                  }`}>
                    {testResult.passed ? (
                      <Trophy className="w-10 h-10" />
                    ) : (
                      <AlertTriangle className="w-10 h-10" />
                    )}
                  </div>

                  {/* Stars Display on Result */}
                  {testResult.passed && (
                    <div className="flex items-center justify-center space-x-1.5">
                      {[1, 2, 3].map((starIdx) => (
                        <Star
                          key={starIdx}
                          className={`w-6 h-6 ${
                            starIdx <= (testResult.stars_awarded || 1)
                              ? 'text-amber-400 fill-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.9)] animate-bounce'
                              : 'text-slate-600'
                          }`}
                        />
                      ))}
                    </div>
                  )}

                  <div>
                    <span className={`text-xs font-black uppercase tracking-wider ${testResult.passed ? 'text-[#10B981]' : 'text-rose-400'}`}>
                      {testResult.passed ? `Level Cleared • ${testResult.mastery_level || 'Mastered'}` : 'Level Test Needs Review'}
                    </span>
                    <h3 className="text-2xl font-black text-white mt-1">
                      Score: {testResult.score_percent}% ({testResult.correct_count}/{testResult.total_questions} Correct)
                    </h3>
                    <p className="text-xs text-slate-300 max-w-md mx-auto mt-2 leading-relaxed">
                      {testResult.feedback}
                    </p>
                  </div>
                </div>

                {/* Level Unlocked Banner */}
                {testResult.passed && testResult.next_level_unlocked && (
                  <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500/20 via-blue-500/20 to-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center justify-center space-x-2">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    <span>Level unlocked: '{testResult.unlocked_level_name}' is now active on your World Map!</span>
                  </div>
                )}

                {/* Question Review Accordion */}
                <div className="text-left space-y-3 pt-2">
                  <button
                    onClick={() => setShowTestReview(!showTestReview)}
                    className="w-full text-xs font-bold text-slate-400 hover:text-white flex items-center justify-between p-2.5 rounded-xl bg-slate-900 border border-slate-800"
                  >
                    <span>Detailed Diagnostic Review ({testResult.results_detail.length} Questions)</span>
                    {showTestReview ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  {showTestReview && (
                    <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                      {testResult.results_detail.map((item, rIdx) => (
                        <div
                          key={rIdx}
                          className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                            item.is_correct
                              ? 'bg-emerald-500/10 border-emerald-500/30 text-slate-200'
                              : 'bg-rose-500/10 border-rose-500/30 text-slate-200'
                          }`}
                        >
                          <div className="flex items-center justify-between font-bold">
                            <span>Q{rIdx + 1}: {item.topic}</span>
                            <span className={item.is_correct ? 'text-emerald-400' : 'text-rose-400'}>
                              {item.is_correct ? '✓ Correct' : '✗ Incorrect'}
                            </span>
                          </div>
                          <div className="text-white font-medium">{item.question}</div>
                          {item.code_snippet && (
                            <div className="p-2 rounded bg-black/40 font-mono text-[10px] text-emerald-300 overflow-x-auto whitespace-pre">
                              {item.code_snippet}
                            </div>
                          )}
                          <div className="text-[11px] text-slate-300">
                            <strong>Your Answer: </strong>{item.user_answer}
                          </div>
                          {!item.is_correct && (
                            <div className="text-[11px] text-emerald-400">
                              <strong>Correct: </strong>{item.correct_answer}
                            </div>
                          )}
                          <div className="text-[11px] text-slate-400 italic pt-1 border-t border-slate-700/50">
                            {item.explanation}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-3 pt-3">
                  {!testResult.passed && (
                    <button
                      onClick={() => handleStartLevelTest(testActivePhase)}
                      className="flex-1 py-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-900 font-black text-xs transition flex items-center justify-center space-x-1.5 shadow-md"
                    >
                      <RotateCcw className="w-4 h-4 text-slate-900" />
                      <span>Retake AI Test with Fresh Questions</span>
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setTestActivePhase(null);
                      setTestResult(null);
                    }}
                    className="flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition"
                  >
                    {testResult.passed ? 'Continue on World Map →' : 'Review Syllabus & Close'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 6. HORIZONS BEYOND LEVEL 7 MODAL ("..." Node)                 */}
      {/* ============================================================== */}
      {showFutureMilestonesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#18181b] border border-[#27272a] rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl relative text-left">
            <button
              onClick={() => setShowFutureMilestonesModal(false)}
              className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3">
              <div 
                style={{
                  background: '#1c1c1e',
                  borderColor: 'rgba(255, 77, 79, 0.7)',
                  boxShadow: '0 0 16px rgba(255, 77, 79, 0.35)'
                }}
                className="w-12 h-12 rounded-full border-2 border-dashed flex items-center justify-center flex-shrink-0"
              >
                <span className="font-mono font-black text-xl text-[#ff4d4f] pb-1">...</span>
              </div>
              <div>
                <span className="text-[10px] font-black uppercase tracking-wider text-[#ff4d4f]">
                  Future Career Horizons
                </span>
                <h3 className="text-xl font-black text-white mt-0.5">
                  Beyond Level 7 Mastery
                </h3>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Completing your foundational and capstone levels is just the start of your trajectory. Here is where the winding path leads after placement:
            </p>

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-[#27272a]/50 border border-slate-700/60 space-y-1">
                <div className="text-xs font-bold text-white flex items-center space-x-2">
                  <span className="text-[#ff4d4f]">★</span>
                  <span>Staff & Principal Engineer Track</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Drive cross-team technical strategy, distributed systems resiliency, and engineering excellence across organizations.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-[#27272a]/50 border border-slate-700/60 space-y-1">
                <div className="text-xs font-bold text-white flex items-center space-x-2">
                  <span className="text-[#ff4d4f]">★</span>
                  <span>AI & Cloud Architecture Specialization</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Integrate autonomous agent pipelines, vector databases, multi-cloud Kubernetes, and enterprise microservices.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-[#27272a]/50 border border-slate-700/60 space-y-1">
                <div className="text-xs font-bold text-white flex items-center space-x-2">
                  <span className="text-[#ff4d4f]">★</span>
                  <span>Engineering Leadership & Mentorship</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Grow from an individual contributor into technical lead, advising junior developers and shaping hiring rubrics.
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center space-x-3">
              <button
                onClick={() => {
                  setShowFutureMilestonesModal(false);
                  handleRecalculate();
                }}
                className="flex-1 py-3 rounded-xl bg-[#ff4d4f] hover:bg-[#e03d3f] text-white font-bold text-xs transition shadow-md flex items-center justify-center space-x-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Recalculate Roadmap</span>
              </button>
              <button
                onClick={() => setShowFutureMilestonesModal(false)}
                className="py-3 px-5 rounded-xl bg-[#27272a] hover:bg-[#323236] text-white font-bold text-xs transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 7. ROADMAP PREFERENCES & TRACK PACE MODAL                      */}
      {/* ============================================================== */}
      {showPreferences && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#18181b] border border-[#27272a] rounded-3xl max-w-xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative text-left max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowPreferences(false)}
              className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-[#ff4d4f] flex items-center space-x-1.5">
                <Sliders className="w-3 h-3 text-[#ff4d4f]" />
                <span>Tailored Learning Architecture</span>
              </span>
              <h3 className="text-xl font-black text-white">
                Roadmap Pace & Preferences
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Har user ki preparation alag hoti hai. Apni current requirement ke mutabiq level depth aur pace choose karein.
              </p>
            </div>

            <form onSubmit={handleSavePreferences} className="space-y-5">
              {/* Pace & Level Count Selector */}
              <div className="space-y-2.5">
                <label className="text-xs font-bold text-slate-200 block">
                  Learning Track Pace & Level Depth
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    {
                      id: 'Express' as const,
                      title: 'Express Track',
                      levels: '2-3 Levels',
                      desc: 'Fast-track core concepts for upcoming interviews & quick placement prep'
                    },
                    {
                      id: 'Standard' as const,
                      title: 'Standard Track',
                      levels: '4-5 Levels',
                      desc: 'Balanced path covering foundation, architecture & production projects'
                    },
                    {
                      id: 'Comprehensive' as const,
                      title: 'Comprehensive',
                      levels: '6-7+ Levels',
                      desc: 'Complete zero-to-hero mastery from basics to enterprise scale'
                    }
                  ].map((pace) => {
                    const isSelected = trackPace === pace.id;
                    return (
                      <button
                        key={pace.id}
                        type="button"
                        onClick={() => {
                          setTrackPace(pace.id);
                          playSound('select', soundEnabled);
                        }}
                        className={`p-3.5 rounded-2xl text-left border transition relative flex flex-col justify-between ${
                          isSelected
                            ? 'bg-[#ff4d4f]/10 border-[#ff4d4f] text-white shadow-[0_0_15px_rgba(255,77,79,0.2)] ring-1 ring-[#ff4d4f]'
                            : 'bg-[#27272a]/40 hover:bg-[#27272a]/70 border-slate-700/60 text-slate-300'
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-extrabold">{pace.title}</span>
                            {isSelected && <span className="w-2 h-2 rounded-full bg-[#ff4d4f] shadow-[0_0_6px_#ff4d4f]" />}
                          </div>
                          <span className={`text-[10px] font-bold block mb-1.5 ${isSelected ? 'text-[#ff4d4f]' : 'text-slate-400'}`}>
                            {pace.levels}
                          </span>
                          <p className="text-[10px] text-slate-400 leading-tight">
                            {pace.desc}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Experience Level */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-200 block">
                  Your Current Experience Level
                </label>
                <div className="grid grid-cols-3 gap-2.5">
                  {['Beginner', 'Intermediate', 'Advanced'].map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setUserLevel(lvl)}
                      className={`py-2 px-3 rounded-xl text-xs font-bold border transition ${
                        userLevel === lvl
                          ? 'bg-[#2563EB]/20 border-[#2563EB] text-blue-300 ring-1 ring-[#2563EB]'
                          : 'bg-[#27272a]/40 hover:bg-[#27272a]/70 border-slate-700/60 text-slate-400'
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Study Commitment (Hours & Days) */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-300">
                    Hours per day: <strong className="text-white">{hoursPerDay}h</strong>
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={6}
                    value={hoursPerDay}
                    onChange={(e) => setHoursPerDay(parseInt(e.target.value))}
                    className="w-full accent-[#ff4d4f]"
                  />
                  <div className="flex justify-between text-[9px] text-slate-500">
                    <span>1h (Casual)</span>
                    <span>6h (Intensive)</span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-300">
                    Days per week: <strong className="text-white">{daysPerWeek} days</strong>
                  </label>
                  <input
                    type="range"
                    min={2}
                    max={7}
                    value={daysPerWeek}
                    onChange={(e) => setDaysPerWeek(parseInt(e.target.value))}
                    className="w-full accent-[#ff4d4f]"
                  />
                  <div className="flex justify-between text-[9px] text-slate-500">
                    <span>2 days</span>
                    <span>7 days (Full)</span>
                  </div>
                </div>
              </div>

              {/* Learning Style */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-slate-300 block">
                  Preferred Learning Mode
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['Hands-on', 'Video-guided', 'Reading & Docs'].map((style) => (
                    <button
                      key={style}
                      type="button"
                      onClick={() => setLearningStyle(style)}
                      className={`py-1.5 px-2 rounded-lg text-[11px] font-semibold border transition ${
                        learningStyle === style
                          ? 'bg-slate-800 border-slate-500 text-white'
                          : 'bg-[#27272a]/30 border-slate-700/50 text-slate-400'
                      }`}
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>

              {/* Add Custom Level Shortcut Banner */}
              <div className="p-3.5 rounded-2xl bg-[#27272a]/50 border border-slate-700/60 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">Specific Milestone Add Karna Hai?</span>
                  <span className="text-[10px] text-slate-400">Add a custom milestone for a specific framework or company.</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setShowPreferences(false);
                    setShowAddCustomModal(true);
                  }}
                  className="px-3 py-1.5 rounded-xl bg-[#ff4d4f]/20 hover:bg-[#ff4d4f]/30 border border-[#ff4d4f]/40 text-xs font-bold text-[#ff4d4f] transition flex items-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>+ Custom Milestone</span>
                </button>
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center space-x-3 pt-2">
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="flex-1 py-3 rounded-xl bg-[#ff4d4f] hover:bg-[#e03d3f] text-white font-bold text-xs transition shadow-md flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  {actionLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Calibrating Roadmap...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Save & Recalibrate Roadmap</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowPreferences(false)}
                  className="py-3 px-5 rounded-xl bg-[#27272a] hover:bg-[#323236] text-white font-bold text-xs transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 8. ADD CUSTOM MILESTONE MODAL                                  */}
      {/* ============================================================== */}
      {showAddCustomModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#18181b] border border-[#27272a] rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl relative text-left">
            <button
              onClick={() => setShowAddCustomModal(false)}
              className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-[#ff4d4f] flex items-center space-x-1.5">
                <Plus className="w-3 h-3 text-[#ff4d4f]" />
                <span>Custom Career Level</span>
              </span>
              <h3 className="text-xl font-black text-white">
                Add Custom Level to Trail
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Add a specialized phase tailored to your target company or stack. Yeh level dynamically aapke career path me attach ho jayega.
              </p>
            </div>

            <form onSubmit={handleAddCustomMilestone} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-200 block">
                  Level Title <span className="text-[#ff4d4f]">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={customPhaseTitle}
                  onChange={(e) => setCustomPhaseTitle(e.target.value)}
                  placeholder="e.g. Microservices & Kubernetes Deployment"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#27272a]/60 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-[#ff4d4f]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-200 block">
                  Milestone Focus & Goal
                </label>
                <textarea
                  rows={2}
                  value={customPhaseDesc}
                  onChange={(e) => setCustomPhaseDesc(e.target.value)}
                  placeholder="e.g. Learn to containerize services, configure ingress, and orchestrate with Docker and K8s."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#27272a]/60 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-[#ff4d4f] resize-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-200 block">
                  Key Topics / Technologies (Comma-separated)
                </label>
                <input
                  type="text"
                  value={customPhaseTopics}
                  onChange={(e) => setCustomPhaseTopics(e.target.value)}
                  placeholder="e.g. Docker, Kubernetes, Helm, RabbitMQ, CI/CD"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#27272a]/60 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-[#ff4d4f]"
                />
                <span className="text-[10px] text-slate-500 block">
                  AI will generate specific hands-on tasks and a gatekeeper diagnostic test for these topics.
                </span>
              </div>

              <div className="flex items-center space-x-3 pt-3">
                <button
                  type="submit"
                  disabled={customPhaseLoading || !customPhaseTitle.trim()}
                  className="flex-1 py-3 rounded-xl bg-[#ff4d4f] hover:bg-[#e03d3f] text-white font-bold text-xs transition shadow-md flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  {customPhaseLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Adding Milestone...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Milestone to World Map</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddCustomModal(false)}
                  className="py-3 px-5 rounded-xl bg-[#27272a] hover:bg-[#323236] text-white font-bold text-xs transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
