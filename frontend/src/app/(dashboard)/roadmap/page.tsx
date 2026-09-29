'use client';

import { useEffect, useState } from 'react';
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
  CheckSquare,
  Square,
  ArrowRight,
  ListChecks,
  Lightbulb
} from 'lucide-react';
import { 
  getCurrentRoadmap, 
  generateRoadmap, 
  getTodayTasks, 
  completeRoadmapTask, 
  uncompleteRoadmapTask, 
  recalculateRoadmap,
  updateRoadmapPreferences
} from '@/lib/api-client';
import { 
  RoadmapData, 
  DailyTasksData, 
  RoadmapPhase, 
  RoadmapTask 
} from '@/lib/types';

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [todayData, setTodayData] = useState<DailyTasksData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [openPhaseId, setOpenPhaseId] = useState<string>('phase_1');
  const [showPreferences, setShowPreferences] = useState(false);
  const [openTaskId, setOpenTaskId] = useState<string | null>(null);  // for expandable task detail
  const [quizAnswered, setQuizAnswered] = useState<Record<string, string>>({});  // taskId -> answer

  // Setup form states
  const [userLevel, setUserLevel] = useState('Beginner');
  const [hoursPerDay, setHoursPerDay] = useState(1);
  const [daysPerWeek, setDaysPerWeek] = useState(5);
  const [learningStyle, setLearningStyle] = useState('Hands-on');

  useEffect(() => {
    loadRoadmapData();
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
          setOpenPhaseId(rData.phases[0].phase_id || rData.phases[0].id || 'phase_1');
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
    } catch (err) {
      console.error('Failed to generate roadmap:', err);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRecalculate() {
    setActionLoading(true);
    try {
      const newRoadmap = await recalculateRoadmap();
      setRoadmap(newRoadmap);
      const tData = await getTodayTasks();
      setTodayData(tData);
    } catch (err) {
      console.error('Failed to recalculate roadmap:', err);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleToggleTask(taskId: string, isCompleted: boolean) {
    if (!roadmap) return;
    try {
      let progressRes;
      if (isCompleted) {
        progressRes = await uncompleteRoadmapTask(taskId);
      } else {
        progressRes = await completeRoadmapTask(taskId);
      }

      // Optimistically update state
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

      // Refresh today's tasks
      getTodayTasks().then(setTodayData).catch(() => {});
    } catch (err) {
      console.error('Failed to toggle task completion:', err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-3">
          <RefreshCw className="w-8 h-8 text-[#17324D] dark:text-[#2563EB] animate-spin" />
          <p className="text-[#64748B] dark:text-[#A8B3C2] text-sm font-medium">Calibrating your career roadmap...</p>
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
            <span>Personalized Career Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#0F172A] dark:text-[#F1F5F9] tracking-tight">Create Your Career Roadmap</h1>
          <p className="text-[#64748B] dark:text-[#A8B3C2] text-sm max-w-xl mx-auto">
            Build a dependency-ordered, step-by-step curriculum derived from your target career, verified skills, and skill gaps.
          </p>
        </div>

        {/* 1-Click Quick Start with Smart Defaults */}
        <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-6">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Recommended Student Pace
              </span>
              <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Smart Defaults Pre-Configured
              </span>
            </div>
            <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600 dark:text-slate-400">
              <span className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                Level: <strong className="text-slate-900 dark:text-white">{userLevel}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                Pace: <strong className="text-slate-900 dark:text-white">{hoursPerDay}h / day</strong>
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                Commitment: <strong className="text-slate-900 dark:text-white">{daysPerWeek} days / week</strong>
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                Style: <strong className="text-slate-900 dark:text-white">{learningStyle}</strong>
              </span>
            </div>
          </div>

          {/* Primary 1-Click Action */}
          <button
            type="button"
            onClick={() => handleGenerateRoadmap()}
            disabled={actionLoading}
            className="w-full py-4 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white font-bold text-sm shadow-sm transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            {actionLoading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin text-white" />
                <span>Generating Your Roadmap...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-[#2563EB]" />
                <span>Start Initial Roadmap (Recommended)</span>
                <ArrowRight className="w-4 h-4 text-[#2563EB]" />
              </>
            )}
          </button>

          {/* Secondary Customize Schedule Control */}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-800/80">
            <button
              type="button"
              onClick={() => setShowPreferences(!showPreferences)}
              className="w-full flex items-center justify-between text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 py-1 transition"
            >
              <span>Customize Schedule & Learning Style (Optional)</span>
              {showPreferences ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showPreferences && (
              <form onSubmit={handleGenerateRoadmap} className="mt-4 space-y-5 pt-4 border-t border-dashed border-slate-200 dark:border-slate-800">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] uppercase tracking-wider mb-2">
                      Current Experience Level
                    </label>
                    <select
                      value={userLevel}
                      onChange={(e) => setUserLevel(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] text-[#0F172A] dark:text-[#F1F5F9] text-sm focus:outline-none focus:border-[#17324D] dark:focus:border-[#2563EB]"
                    >
                      <option value="Beginner">Beginner (Starting from scratch)</option>
                      <option value="Intermediate">Intermediate (Have basic coding experience)</option>
                      <option value="Advanced">Advanced (Upskilling / Specialty transition)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] uppercase tracking-wider mb-2">
                      Preferred Learning Style
                    </label>
                    <select
                      value={learningStyle}
                      onChange={(e) => setLearningStyle(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] text-[#0F172A] dark:text-[#F1F5F9] text-sm focus:outline-none focus:border-[#17324D] dark:focus:border-[#2563EB]"
                    >
                      <option value="Hands-on">Hands-on Labs & Coding</option>
                      <option value="Project-Based">Project-Based Portfolio Building</option>
                      <option value="Theoretical Deep Dive">Theoretical Concepts & Deep Dives</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] uppercase tracking-wider mb-2">
                      Daily Learning Time: {hoursPerDay} {hoursPerDay === 1 ? 'hour' : 'hours'}/day
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="6"
                      value={hoursPerDay}
                      onChange={(e) => setHoursPerDay(parseInt(e.target.value))}
                      className="w-full accent-[#17324D] dark:accent-[#2563EB] cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] uppercase tracking-wider mb-2">
                      Study Schedule: {daysPerWeek} days/week
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="7"
                      value={daysPerWeek}
                      onChange={(e) => setDaysPerWeek(parseInt(e.target.value))}
                      className="w-full accent-[#17324D] dark:accent-[#2563EB] cursor-pointer"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={actionLoading}
                  className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition shadow-xs flex items-center justify-center space-x-2"
                >
                  {actionLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  ) : (
                    <span>Apply Custom Schedule & Generate</span>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Active Roadmap View
  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <h1 className="text-2xl font-extrabold text-[#0F172A] dark:text-[#F1F5F9] tracking-tight">Personalized Career Roadmap</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#2563EB]/15 text-[#17324D] dark:text-[#38BDF8] border border-[#2563EB]/30">
              {roadmap.target_role}
            </span>
          </div>
          <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">
            Dependency-ordered curriculum • Level: <strong className="text-[#0F172A] dark:text-[#F1F5F9]">{roadmap.user_level}</strong> • Est. Duration: <strong className="text-[#0F172A] dark:text-[#F1F5F9]">{roadmap.total_estimated_weeks} weeks</strong> ({roadmap.hours_per_day}h/day, {roadmap.days_per_week}d/week)
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowPreferences(!showPreferences)}
            className="px-3.5 py-2 rounded-xl bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] hover:bg-black/5 dark:hover:bg-white/5 text-[#0F172A] dark:text-[#F1F5F9] text-xs font-semibold transition-all"
          >
            Preferences
          </button>
          <button
            onClick={handleRecalculate}
            disabled={actionLoading}
            className="px-4 py-2 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white text-xs font-semibold transition-all flex items-center space-x-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            <span>Recalculate</span>
          </button>
        </div>
      </div>

      {/* Outdated Roadmap Warning Alert */}
      {roadmap.is_outdated && (
        <div className="p-4 rounded-xl bg-[#C78A20]/10 border border-[#C78A20]/30 flex items-center justify-between">
          <div className="flex items-center space-x-3 text-[#C78A20] text-sm">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <div>
              <strong className="font-semibold">Target Career Updated:</strong> Your target career on your profile has changed. Your roadmap can be recalculated to align with your new skill requirements while preserving your completed progress.
            </div>
          </div>
          <button
            onClick={handleRecalculate}
            className="px-3.5 py-1.5 rounded-lg bg-[#C78A20] text-white font-bold text-xs hover:bg-[#C78A20]/90 transition-all flex-shrink-0"
          >
            Update Roadmap Now
          </button>
        </div>
      )}

      {/* Progress Bar Card */}
      <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-[#64748B] dark:text-[#A8B3C2] uppercase tracking-wider">Overall Roadmap Completion</span>
          <span className="text-[#17324D] dark:text-[#38BDF8] text-sm font-extrabold">{roadmap.overall_progress_percent}%</span>
        </div>
        <div className="w-full bg-[#F8FAFC] dark:bg-[#0F172A] h-3 rounded-full overflow-hidden border border-[#E2E8F0] dark:border-[#334155]">
          <div 
            className="bg-[#17324D] dark:bg-[#2563EB] h-full transition-all duration-500 rounded-full" 
            style={{ width: `${roadmap.overall_progress_percent}%` }} 
          />
        </div>
        <div className="flex items-center justify-between text-xs text-[#64748B] dark:text-[#A8B3C2] pt-1">
          <span>{roadmap.completed_task_ids.length} tasks completed</span>
          <span>{roadmap.phases.length} Phases Total</span>
        </div>
      </div>

      {/* Preferences Form Modal/Drawer */}
      {showPreferences && (
        <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-[#0F172A] dark:text-[#F1F5F9] uppercase tracking-wider">Adjust Learning Schedule</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-[#64748B] dark:text-[#A8B3C2] mb-1">Hours / Day ({hoursPerDay}h)</label>
              <input
                type="range"
                min="1"
                max="6"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(parseInt(e.target.value))}
                className="w-full accent-[#17324D] dark:accent-[#2563EB]"
              />
            </div>
            <div>
              <label className="block text-[#64748B] dark:text-[#A8B3C2] mb-1">Days / Week ({daysPerWeek}d)</label>
              <input
                type="range"
                min="1"
                max="7"
                value={daysPerWeek}
                onChange={(e) => setDaysPerWeek(parseInt(e.target.value))}
                className="w-full accent-[#17324D] dark:accent-[#2563EB]"
              />
            </div>
            <div>
              <label className="block text-[#64748B] dark:text-[#A8B3C2] mb-1">Level</label>
              <select
                value={userLevel}
                onChange={(e) => setUserLevel(e.target.value)}
                className="w-full px-3 py-1.5 bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] rounded-lg text-[#0F172A] dark:text-[#F1F5F9]"
              >
                <option value="Beginner">Beginner (Start from Scratch - No prior knowledge)</option>
                <option value="Intermediate">Intermediate (Core & Frameworks)</option>
                <option value="Advanced">Advanced (System Architecture & Interview Mastery)</option>
              </select>
            </div>
          </div>
          <button
            onClick={() => handleGenerateRoadmap()}
            className="px-4 py-2 bg-[#17324D] hover:bg-[#102A43] text-white rounded-lg text-xs font-bold transition-all shadow-sm"
          >
            Save Preferences & Regenerate
          </button>
        </div>
      )}

      {/* Today's Focus Widget */}
      {todayData && (todayData.tasks || []).length > 0 && (
        <div className="p-6 rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-4 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-[#17324D] dark:text-[#38BDF8] text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-[#2563EB]" />
              <span>Today's Focus • {todayData.current_phase_name}</span>
            </div>
            <span className="text-xs text-[#64748B] dark:text-[#A8B3C2] flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-[#2563EB]" />
              <span>Time Budget: {todayData.hours_budget}h</span>
            </span>
          </div>

          <div>
            <h3 className="text-lg font-bold text-[#0F172A] dark:text-[#F1F5F9] mb-1">{todayData.today_focus_title}</h3>
            <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">{todayData.why_it_matters}</p>
          </div>

          <div className="space-y-2 pt-2">
            {(todayData.tasks || []).map((task) => (
              <div
                key={task.id}
                className={`p-3.5 rounded-xl border flex items-start justify-between space-x-3 transition-all ${
                  task.is_priority
                    ? 'bg-[#F8FAFC] dark:bg-[#0F172A] border-[#2563EB]/40'
                    : 'bg-[#F8FAFC] dark:bg-[#0F172A] border-[#E2E8F0] dark:border-[#334155]'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <button
                    onClick={() => handleToggleTask(task.id, task.is_completed)}
                    className="mt-0.5 text-[#17324D] dark:text-[#2563EB] hover:opacity-80 transition-colors"
                  >
                    {task.is_completed ? (
                      <CheckCircle2 className="w-5 h-5 text-[#2E7D5B]" />
                    ) : (
                      <Square className="w-5 h-5 text-[#64748B]" />
                    )}
                  </button>
                  <div>
                    <div className="flex items-center space-x-2 flex-wrap gap-1">
                      <h4 className={`text-sm font-semibold ${task.is_completed ? 'line-through text-[#64748B]' : 'text-[#0F172A] dark:text-[#F1F5F9]'}`}>
                        {task.title}
                      </h4>
                      {task.is_priority && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#2563EB]/15 text-[#17324D] dark:text-[#38BDF8] border border-[#2563EB]/30 font-bold">⚡ Interview Priority</span>
                      )}
                    </div>
                    <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-0.5">{task.description}</p>
                  </div>
                </div>
                <div className="flex-shrink-0 text-right space-y-1">
                  <span className="block px-2 py-1 rounded bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] text-[11px] text-[#64748B] dark:text-[#A8B3C2] font-medium">
                    {task.estimated_minutes} min
                  </span>
                  <a
                    href={`/practice?topic=${encodeURIComponent(task.title)}`}
                    className="block text-[10px] text-[#17324D] dark:text-[#38BDF8] hover:underline font-semibold"
                  >
                    Practice →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Adaptive Roadmap Phases Accordion */}
      <div className="space-y-6">
        <h2 className="text-lg font-bold text-[#0F172A] dark:text-[#F1F5F9] flex items-center space-x-2">
          <Layers className="w-5 h-5 text-[#17324D] dark:text-[#2563EB]" />
          <span>Roadmap Phases & Skill Milestones</span>
        </h2>

        {roadmap.phases.map((phase, idx) => {
          const phaseId = (phase as any).phase_id || (phase as any).id || `phase-${idx}`;
          const isOpen = openPhaseId === phaseId;
          const phaseTasks = (phase as any).tasks || [];
          const phaseSkills = (phase as any).skills || [];
          const phaseName = (phase as any).name || (phase as any).title || `Phase ${idx + 1}`;
          const phaseDesc = (phase as any).description || '';
          const completedTasksInPhase = phaseTasks.filter((t: any) => t.is_completed || t.completed).length;
          const phasePct = phaseTasks.length > 0 ? Math.round((completedTasksInPhase / phaseTasks.length) * 100) : 0;

          return (
            <div key={phaseId} className="rounded-2xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm overflow-hidden">
              {/* Phase Header */}
              <button
                onClick={() => setOpenPhaseId(isOpen ? '' : phaseId)}
                className="w-full p-5 text-left flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-sm ${phasePct === 100 ? 'bg-[#2E7D5B]/15 text-[#2E7D5B] border border-[#2E7D5B]/30' : 'bg-[#17324D]/10 dark:bg-[#2563EB]/20 text-[#17324D] dark:text-[#38BDF8] border border-[#17324D]/20 dark:border-[#2563EB]/30'}`}>
                    {idx + 1}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#0F172A] dark:text-[#F1F5F9]">{phaseName}</h3>
                    <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-0.5">{phaseDesc}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right hidden sm:block">
                    <span className="text-xs font-semibold text-[#17324D] dark:text-[#38BDF8]">{phasePct}% Complete</span>
                    <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">{completedTasksInPhase}/{phaseTasks.length} tasks</p>
                  </div>
                  {isOpen ? <ChevronUp className="w-5 h-5 text-[#64748B]" /> : <ChevronDown className="w-5 h-5 text-[#64748B]" />}
                </div>
              </button>

              {/* Phase Collapsible Body */}
              {isOpen && (
                <div className="p-6 border-t border-[#E2E8F0] dark:border-[#334155] space-y-6 bg-[#F8FAFC] dark:bg-[#0F172A]/50">
                  {/* Phase Skills Bar */}
                  <div>
                    <h4 className="text-xs font-bold text-[#64748B] dark:text-[#A8B3C2] uppercase tracking-wider mb-2">Target Skills in this Phase</h4>
                    <div className="flex flex-wrap gap-2">
                      {phaseSkills.map((sk: any, sIdx: number) => {
                        const skillName = typeof sk === 'string' ? sk : sk.name;
                        const skillStatus = typeof sk === 'string' ? 'Target' : sk.status;
                        return (
                          <span
                            key={sIdx}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold border ${
                              skillStatus === 'Verified' ? 'bg-[#2E7D5B]/10 text-[#2E7D5B] border-[#2E7D5B]/30' : 'bg-white dark:bg-[#172235] text-[#0F172A] dark:text-[#F1F5F9] border-[#E2E8F0] dark:border-[#334155]'
                            }`}
                          >
                            {skillName}{skillStatus && skillStatus !== 'Target' ? ` • ${skillStatus}` : ''}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {/* Learning Objectives */}
                  {(phase as any).learning_objectives && (phase as any).learning_objectives.length > 0 && (
                    <div className="p-4 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] space-y-2">
                      <h4 className="text-xs font-bold text-[#17324D] dark:text-[#38BDF8] uppercase tracking-wider flex items-center space-x-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>Learning Objectives</span>
                      </h4>
                      <ul className="space-y-1.5 text-xs text-[#0F172A] dark:text-[#F1F5F9]">
                        {(phase as any).learning_objectives.map((obj: string, oIdx: number) => (
                          <li key={oIdx} className="flex items-start space-x-2">
                            <span className="text-[#2563EB] font-bold">•</span>
                            <span>{obj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Tasks List with Expandable Learning Resources */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-[#64748B] dark:text-[#A8B3C2] uppercase tracking-wider flex items-center space-x-1.5">
                        <ListChecks className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>Topic-Wise Learning Curriculum</span>
                      </h4>
                      <span className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">
                        Detailed syllabus • What to learn & practice
                      </span>
                    </div>

                    <div className="space-y-3">
                      {phaseTasks.map((task: any) => {
                        const isTaskOpen = openTaskId === task.id;
                        const isCompleted = task.is_completed || task.completed;
                        const isPriority = task.is_priority;
                        const hasTopics = task.topics_to_learn && task.topics_to_learn.length > 0;
                        const hasLegacyLearning = task.concept_explanation || task.practice_exercise || task.check_quiz_question;
                        const hasExpandableContent = hasTopics || task.learning_focus || task.practice_goal || hasLegacyLearning;

                        return (
                          <div
                            key={task.id}
                            className={`rounded-xl border transition-all ${
                              isPriority ? 'border-[#2563EB]/40 bg-white dark:bg-[#172235]' :
                              isCompleted ? 'border-[#2E7D5B]/30 bg-white dark:bg-[#172235]' :
                              'border-[#E2E8F0] dark:border-[#334155] bg-white dark:bg-[#172235]'
                            }`}
                          >
                            {/* Task Header Row */}
                            <div className="p-4 flex items-start justify-between space-x-3">
                              <div className="flex items-start space-x-3">
                                <button
                                  onClick={() => handleToggleTask(task.id, isCompleted)}
                                  className="mt-0.5 text-[#17324D] dark:text-[#2563EB] hover:opacity-80"
                                >
                                  {isCompleted ? (
                                    <CheckCircle2 className="w-5 h-5 text-[#2E7D5B]" />
                                  ) : (
                                    <Square className="w-5 h-5 text-[#64748B]" />
                                  )}
                                </button>
                                <div>
                                  <div className="flex items-center flex-wrap gap-1.5 mb-1">
                                    <h5 className={`text-sm font-semibold ${
                                      isCompleted ? 'line-through text-[#64748B]' : 'text-[#0F172A] dark:text-[#F1F5F9]'
                                    }`}>
                                      {task.title}
                                    </h5>
                                    {task.difficulty_level && (
                                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#17324D]/10 dark:bg-[#2563EB]/20 text-[#17324D] dark:text-[#38BDF8] border border-[#17324D]/20 dark:border-[#2563EB]/30 font-medium">
                                        {task.difficulty_level}
                                      </span>
                                    )}
                                    {isPriority && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#2563EB]/15 text-[#17324D] dark:text-[#38BDF8] border border-[#2563EB]/30 font-bold">
                                        ⚡ Interview Priority
                                      </span>
                                    )}
                                    {task.task_type && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F8FAFC] dark:bg-[#0F172A] text-[#64748B] dark:text-[#A8B3C2] border border-[#E2E8F0] dark:border-[#334155] font-medium">
                                        {task.task_type}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">{task.description}</p>
                                  {(task.why_it_matters || task.why_matters) && (
                                    <p className="text-[11px] text-[#17324D] dark:text-[#38BDF8] mt-1 font-medium">
                                      Goal: {task.why_it_matters || task.why_matters}
                                    </p>
                                  )}
                                  {isPriority && task.priority_reason && (
                                    <p className="text-[10px] text-[#2563EB] mt-1">📌 {task.priority_reason}</p>
                                  )}
                                </div>
                              </div>

                              <div className="flex-shrink-0 text-right space-y-1.5">
                                <span className="block px-2.5 py-1 rounded bg-[#F8FAFC] dark:bg-[#0F172A] border border-[#E2E8F0] dark:border-[#334155] text-[11px] text-[#64748B] dark:text-[#A8B3C2] font-medium">
                                  {task.estimated_minutes} min
                                </span>
                                {hasExpandableContent && (
                                  <button
                                    onClick={() => setOpenTaskId(isTaskOpen ? null : task.id)}
                                    className="block w-full text-[11px] text-[#17324D] dark:text-[#38BDF8] hover:underline font-semibold transition-colors"
                                  >
                                    {isTaskOpen ? '▲ Hide Syllabus' : '▼ What to Learn'}
                                  </button>
                                )}
                                <a
                                  href={`/practice?topic=${encodeURIComponent(task.title)}`}
                                  className="block text-[10px] text-[#17324D] dark:text-[#38BDF8] hover:underline font-semibold"
                                >
                                  Practice →
                                </a>
                              </div>
                            </div>

                            {/* Expandable Topic-wise Syllabus & What to Learn */}
                            {isTaskOpen && hasExpandableContent && (
                              <div className="border-t border-[#E2E8F0] dark:border-[#334155] p-5 space-y-4 bg-[#F8FAFC] dark:bg-[#0F172A]">
                                {/* What to Learn (Subtopics Checklist) */}
                                {hasTopics && (
                                  <div className="space-y-2">
                                    <h6 className="text-[11px] font-bold text-[#17324D] dark:text-[#38BDF8] uppercase tracking-wider flex items-center space-x-1.5">
                                      <ListChecks className="w-3.5 h-3.5 text-[#2563EB]" />
                                      <span>Topics & Concepts to Cover (Syllabus)</span>
                                    </h6>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                                      {task.topics_to_learn.map((subtopic: string, sIdx: number) => (
                                        <div key={sIdx} className="flex items-start space-x-2 p-2 rounded-lg bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155]">
                                          <CheckCircle2 className="w-3.5 h-3.5 text-[#2E7D5B] mt-0.5 flex-shrink-0" />
                                          <span className="text-xs text-[#0F172A] dark:text-[#F1F5F9]">{subtopic}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Learning Focus */}
                                {task.learning_focus && (
                                  <div className="p-3 rounded-lg bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] space-y-1">
                                    <h6 className="text-[10px] font-bold text-[#17324D] dark:text-[#38BDF8] uppercase tracking-wider flex items-center space-x-1">
                                      <Lightbulb className="w-3 h-3 text-[#2563EB]" />
                                      <span>Learning Focus</span>
                                    </h6>
                                    <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">{task.learning_focus}</p>
                                  </div>
                                )}

                                {/* Hands-on Practice Goal */}
                                {(task.practice_goal || task.practice_exercise) && (
                                  <div className="p-3 rounded-lg bg-[#2E7D5B]/10 border border-[#2E7D5B]/30 space-y-1">
                                    <h6 className="text-[10px] font-bold text-[#2E7D5B] uppercase tracking-wider flex items-center space-x-1">
                                      <Code className="w-3 h-3 text-[#2E7D5B]" />
                                      <span>Hands-on Practice Goal (What to Build)</span>
                                    </h6>
                                    <p className="text-xs text-[#2E7D5B] leading-relaxed">
                                      {task.practice_goal || task.practice_exercise}
                                    </p>
                                  </div>
                                )}

                                {/* Recommended Study Topics & Documentation References */}
                                {task.recommended_resources && task.recommended_resources.length > 0 && (
                                  <div className="space-y-1.5 pt-1">
                                    <h6 className="text-[10px] font-bold text-[#64748B] dark:text-[#A8B3C2] uppercase tracking-wider flex items-center space-x-1">
                                      <BookOpen className="w-3 h-3 text-[#2563EB]" />
                                      <span>Recommended Study Topics & Documentation</span>
                                    </h6>
                                    <div className="flex flex-wrap gap-1.5">
                                      {task.recommended_resources.map((res: string, rIdx: number) => (
                                        <span key={rIdx} className="px-2.5 py-1 rounded bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] text-[11px] text-[#0F172A] dark:text-[#F1F5F9]">
                                          📖 {res}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Prerequisites / Details */}
                                {task.prerequisites && task.prerequisites.length > 0 && (
                                  <div className="text-[11px] text-[#64748B] dark:text-[#A8B3C2] pt-1">
                                    <strong className="text-[#0F172A] dark:text-[#F1F5F9]">Prerequisites: </strong>
                                    {task.prerequisites.join(', ')}
                                  </div>
                                )}

                                {/* Legacy Concept Explanation if exists and no topics_to_learn */}
                                {!hasTopics && task.concept_explanation && (
                                  <div className="space-y-1">
                                    <h6 className="text-[10px] font-bold text-[#17324D] dark:text-[#38BDF8] uppercase tracking-wider flex items-center space-x-1">
                                      <BookOpen className="w-3 h-3 text-[#2563EB]" /><span>Concept Overview</span>
                                    </h6>
                                    <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">{task.concept_explanation}</p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Portfolio Projects */}
                  {(phase as any).projects && (phase as any).projects.length > 0 && (
                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-[#17324D] dark:text-[#38BDF8] uppercase tracking-wider flex items-center space-x-1.5">
                        <Code className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>Phase Capstone Project</span>
                      </h4>
                      {(phase as any).projects.map((proj: any) => (
                        <div key={proj.id} className="p-5 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-2">
                          <div className="flex items-center justify-between">
                            <h5 className="text-sm font-bold text-[#0F172A] dark:text-[#F1F5F9]">{proj.title}</h5>
                            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#2563EB]/15 text-[#17324D] dark:text-[#38BDF8] border border-[#2563EB]/30">
                              {proj.difficulty}
                            </span>
                          </div>
                          <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">{proj.objective}</p>
                          <div className="text-[11px] text-[#17324D] dark:text-[#38BDF8] font-medium pt-1">
                            <strong>Resume Impact:</strong> {proj.resume_relevance}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Portfolio Project (single object format) */}
                  {(phase as any).project && (
                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-[#17324D] dark:text-[#38BDF8] uppercase tracking-wider flex items-center space-x-1.5">
                        <Code className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>Phase Capstone Project</span>
                      </h4>
                      <div className="p-5 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-2">
                        <div className="flex items-center justify-between">
                          <h5 className="text-sm font-bold text-[#0F172A] dark:text-[#F1F5F9]">{(phase as any).project.title}</h5>
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#2563EB]/15 text-[#17324D] dark:text-[#38BDF8] border border-[#2563EB]/30">
                            {(phase as any).project.difficulty}
                          </span>
                        </div>
                        <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">{(phase as any).project.objective}</p>
                        <div className="text-[11px] text-[#17324D] dark:text-[#38BDF8] font-medium pt-1">
                          <strong>Resume Impact:</strong> {(phase as any).project.resume_relevance}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Phase Milestone */}
                  {(phase as any).milestones && (phase as any).milestones.length > 0 && (
                    <div className="pt-2">
                      {(phase as any).milestones.map((m: any) => (
                        <div key={m.id} className="p-3.5 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm flex items-center space-x-3">
                          <Award className="w-5 h-5 text-[#2563EB]" />
                          <div>
                            <h5 className="text-xs font-bold text-[#0F172A] dark:text-[#F1F5F9]">{m.title}</h5>
                            <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">{m.criteria}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Milestone (single object format) */}
                  {(phase as any).milestone && (
                    <div className="pt-2">
                      <div className="p-3.5 rounded-xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm flex items-center space-x-3">
                        <Award className="w-5 h-5 text-[#2563EB]" />
                        <div>
                          <h5 className="text-xs font-bold text-[#0F172A] dark:text-[#F1F5F9]">{(phase as any).milestone.title}</h5>
                          <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">{(phase as any).milestone.criteria}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
