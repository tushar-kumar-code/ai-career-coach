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
  ArrowRight
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
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin" />
          <p className="text-slate-400 text-sm font-medium">Calibrating your career roadmap...</p>
        </div>
      </div>
    );
  }

  // Setup Screen if no roadmap exists
  if (!roadmap) {
    return (
      <div className="max-w-3xl mx-auto py-8 space-y-6">
        <div className="p-8 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900 border border-indigo-500/20 text-center space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Personalized Career Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Create Your Career Roadmap</h1>
          <p className="text-slate-300 text-sm max-w-xl mx-auto">
            Build a dependency-ordered, step-by-step curriculum derived from your target career, verified skills, and skill gaps.
          </p>
        </div>

        <form onSubmit={handleGenerateRoadmap} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Current Experience Level
              </label>
              <select
                value={userLevel}
                onChange={(e) => setUserLevel(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="Beginner">Beginner (Starting from scratch)</option>
                <option value="Intermediate">Intermediate (Have basic coding experience)</option>
                <option value="Advanced">Advanced (Upskilling / Specialty transition)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Preferred Learning Style
              </label>
              <select
                value={learningStyle}
                onChange={(e) => setLearningStyle(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="Hands-on">Hands-on Labs & Coding</option>
                <option value="Project-Based">Project-Based Portfolio Building</option>
                <option value="Theoretical Deep Dive">Theoretical Concepts & Deep Dives</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Daily Learning Time: {hoursPerDay} {hoursPerDay === 1 ? 'hour' : 'hours'}/day
              </label>
              <input
                type="range"
                min="1"
                max="6"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(parseInt(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Study Schedule: {daysPerWeek} days/week
              </label>
              <input
                type="range"
                min="1"
                max="7"
                value={daysPerWeek}
                onChange={(e) => setDaysPerWeek(parseInt(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={actionLoading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 transition-all flex items-center justify-center space-x-2"
          >
            {actionLoading ? (
              <RefreshCw className="w-5 h-5 animate-spin text-white" />
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate My Personalized Roadmap</span>
              </>
            )}
          </button>
        </form>
      </div>
    );
  }

  // Active Roadmap View
  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Personalized Career Roadmap</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              {roadmap.target_role}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Dependency-ordered curriculum • Level: <strong className="text-slate-200">{roadmap.user_level}</strong> • Est. Duration: <strong className="text-slate-200">{roadmap.total_estimated_weeks} weeks</strong> ({roadmap.hours_per_day}h/day, {roadmap.days_per_week}d/week)
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowPreferences(!showPreferences)}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all"
          >
            Preferences
          </button>
          <button
            onClick={handleRecalculate}
            disabled={actionLoading}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            <span>Recalculate</span>
          </button>
        </div>
      </div>

      {/* Outdated Roadmap Warning Alert */}
      {roadmap.is_outdated && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center space-x-3 text-amber-300 text-sm">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <div>
              <strong className="font-semibold">Target Career Updated:</strong> Your target career on your profile has changed. Your roadmap can be recalculated to align with your new skill requirements while preserving your completed progress.
            </div>
          </div>
          <button
            onClick={handleRecalculate}
            className="px-3.5 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition-all flex-shrink-0"
          >
            Update Roadmap Now
          </button>
        </div>
      )}

      {/* Progress Bar Card */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-slate-400 uppercase tracking-wider">Overall Roadmap Completion</span>
          <span className="text-indigo-400 text-sm font-extrabold">{roadmap.overall_progress_percent}%</span>
        </div>
        <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
          <div 
            className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full transition-all duration-500" 
            style={{ width: `${roadmap.overall_progress_percent}%` }} 
          />
        </div>
        <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
          <span>{roadmap.completed_task_ids.length} tasks completed</span>
          <span>{roadmap.phases.length} Phases Total</span>
        </div>
      </div>

      {/* Preferences Form Modal/Drawer */}
      {showPreferences && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-indigo-500/30 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Adjust Learning Schedule</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Hours / Day ({hoursPerDay}h)</label>
              <input
                type="range"
                min="1"
                max="6"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Days / Week ({daysPerWeek}d)</label>
              <input
                type="range"
                min="1"
                max="7"
                value={daysPerWeek}
                onChange={(e) => setDaysPerWeek(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Level</label>
              <select
                value={userLevel}
                onChange={(e) => setUserLevel(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-200"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>
          </div>
          <button
            onClick={() => handleGenerateRoadmap()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold"
          >
            Save Preferences & Regenerate
          </button>
        </div>
      )}

      {/* Today's Focus Widget */}
      {todayData && (todayData.tasks || []).length > 0 && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-950/60 to-slate-900 border border-indigo-500/30 space-y-4 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Today's Focus • {todayData.current_phase_name}</span>
            </div>
            <span className="text-xs text-slate-400 flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              <span>Time Budget: {todayData.hours_budget}h</span>
            </span>
          </div>

          <div>
            <h3 className="text-lg font-bold text-white mb-1">{todayData.today_focus_title}</h3>
            <p className="text-xs text-indigo-200/80 leading-relaxed">{todayData.why_it_matters}</p>
          </div>

          <div className="space-y-2 pt-2">
            {(todayData.tasks || []).map((task) => (
              <div
                key={task.id}
                className={`p-3.5 rounded-xl border flex items-start justify-between space-x-3 transition-all ${
                  task.is_priority
                    ? 'bg-violet-950/40 border-violet-500/40 hover:border-violet-400/50'
                    : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <button
                    onClick={() => handleToggleTask(task.id, task.is_completed)}
                    className="mt-0.5 text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    {task.is_completed ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <Square className="w-5 h-5 text-slate-500" />
                    )}
                  </button>
                  <div>
                    <div className="flex items-center space-x-2 flex-wrap gap-1">
                      <h4 className={`text-sm font-semibold ${task.is_completed ? 'line-through text-slate-500' : 'text-slate-200'}`}>
                        {task.title}
                      </h4>
                      {task.is_priority && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/20 font-bold">⚡ Interview Priority</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{task.description}</p>
                  </div>
                </div>
                <div className="flex-shrink-0 text-right space-y-1">
                  <span className="block px-2 py-1 rounded bg-slate-900 text-[11px] text-slate-400 font-medium">
                    {task.estimated_minutes} min
                  </span>
                  <a
                    href={`/practice?topic=${encodeURIComponent(task.title)}`}
                    className="block text-[10px] text-violet-400 hover:text-violet-300 font-semibold"
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
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Layers className="w-5 h-5 text-indigo-400" />
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
            <div key={phaseId} className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden">
              {/* Phase Header */}
              <button
                onClick={() => setOpenPhaseId(isOpen ? '' : phaseId)}
                className="w-full p-5 text-left flex items-center justify-between hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-sm ${phasePct === 100 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'}`}>
                    {idx + 1}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">{phaseName}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{phaseDesc}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right hidden sm:block">
                    <span className="text-xs font-semibold text-indigo-400">{phasePct}% Complete</span>
                    <p className="text-[11px] text-slate-500">{completedTasksInPhase}/{phaseTasks.length} tasks</p>
                  </div>
                  {isOpen ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                </div>
              </button>

              {/* Phase Collapsible Body */}
              {isOpen && (
                <div className="p-6 border-t border-slate-800/80 space-y-6 bg-slate-950/40">
                  {/* Phase Skills Bar */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Target Skills in this Phase</h4>
                    <div className="flex flex-wrap gap-2">
                      {phaseSkills.map((sk: any, sIdx: number) => {
                        const skillName = typeof sk === 'string' ? sk : sk.name;
                        const skillStatus = typeof sk === 'string' ? 'Target' : sk.status;
                        return (
                          <span
                            key={sIdx}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold border ${
                              skillStatus === 'Verified' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-slate-900 text-slate-300 border-slate-800'
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
                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
                      <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center space-x-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Learning Objectives</span>
                      </h4>
                      <ul className="space-y-1.5 text-xs text-slate-300">
                        {(phase as any).learning_objectives.map((obj: string, oIdx: number) => (
                          <li key={oIdx} className="flex items-start space-x-2">
                            <span className="text-indigo-400 font-bold">•</span>
                            <span>{obj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Tasks List with Expandable Learning Resources */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Actionable Learning Tasks</h4>
                    <div className="space-y-2">
                      {phaseTasks.map((task: any) => {
                        const isTaskOpen = openTaskId === task.id;
                        const isCompleted = task.is_completed || task.completed;
                        const isPriority = task.is_priority;
                        const hasLearning = task.concept_explanation || task.practice_exercise || task.check_quiz_question;

                        return (
                          <div
                            key={task.id}
                            className={`rounded-xl border transition-all ${
                              isPriority ? 'border-violet-500/40 bg-violet-950/20' :
                              isCompleted ? 'border-emerald-500/20 bg-emerald-950/10' :
                              'border-slate-800 bg-slate-950'
                            }`}
                          >
                            {/* Task Header Row */}
                            <div className="p-4 flex items-start justify-between space-x-3">
                              <div className="flex items-start space-x-3">
                                <button
                                  onClick={() => handleToggleTask(task.id, isCompleted)}
                                  className="mt-0.5 text-indigo-400 hover:text-indigo-300"
                                >
                                  {isCompleted ? (
                                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                                  ) : (
                                    <Square className="w-5 h-5 text-slate-600" />
                                  )}
                                </button>
                                <div>
                                  <div className="flex items-center flex-wrap gap-1.5 mb-0.5">
                                    <h5 className={`text-sm font-semibold ${
                                      isCompleted ? 'line-through text-slate-500' : 'text-slate-200'
                                    }`}>
                                      {task.title}
                                    </h5>
                                    {isPriority && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/20 font-bold">
                                        ⚡ Interview Priority
                                      </span>
                                    )}
                                    {task.task_type && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-medium">
                                        {task.task_type}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-400">{task.description}</p>
                                  {(task.why_it_matters || task.why_matters) && (
                                    <p className="text-[11px] text-indigo-300/80 mt-1 font-medium">
                                      Why: {task.why_it_matters || task.why_matters}
                                    </p>
                                  )}
                                  {isPriority && task.priority_reason && (
                                    <p className="text-[10px] text-violet-300/80 mt-1">📌 {task.priority_reason}</p>
                                  )}
                                </div>
                              </div>

                              <div className="flex-shrink-0 text-right space-y-1.5">
                                <span className="block px-2.5 py-1 rounded bg-slate-900 text-[11px] text-slate-400 font-medium">
                                  {task.estimated_minutes} min
                                </span>
                                {hasLearning && !isCompleted && (
                                  <button
                                    onClick={() => setOpenTaskId(isTaskOpen ? null : task.id)}
                                    className="block w-full text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold"
                                  >
                                    {isTaskOpen ? '▲ Hide' : '▼ Learn'}
                                  </button>
                                )}
                                <a
                                  href={`/practice?topic=${encodeURIComponent(task.title)}`}
                                  className="block text-[10px] text-violet-400 hover:text-violet-300 font-semibold"
                                >
                                  Practice →
                                </a>
                              </div>
                            </div>

                            {/* Expandable Learning Resources */}
                            {isTaskOpen && hasLearning && (
                              <div className="border-t border-slate-800 p-4 space-y-4 bg-slate-900/60">
                                {/* Learn */}
                                {task.concept_explanation && (
                                  <div className="space-y-1.5">
                                    <h6 className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center space-x-1">
                                      <BookOpen className="w-3 h-3" /><span>Understand the Concept</span>
                                    </h6>
                                    <p className="text-xs text-slate-300 leading-relaxed">{task.concept_explanation}</p>
                                  </div>
                                )}

                                {/* Practice */}
                                {task.practice_exercise && (
                                  <div className="space-y-1.5">
                                    <h6 className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1">
                                      <Code className="w-3 h-3" /><span>Hands-on Exercise</span>
                                    </h6>
                                    <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/20 text-xs text-emerald-200">
                                      {task.practice_exercise}
                                    </div>
                                  </div>
                                )}

                                {/* Quiz */}
                                {task.check_quiz_question && (
                                  <div className="space-y-2">
                                    <h6 className="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1">
                                      <CheckSquare className="w-3 h-3" /><span>Check Yourself</span>
                                    </h6>
                                    <p className="text-xs text-slate-200 font-medium">{task.check_quiz_question}</p>
                                    <div className="space-y-1.5">
                                      {(task.check_quiz_options || []).map((opt: string, oi: number) => {
                                        const letter = opt.charAt(0);
                                        const answered = quizAnswered[task.id];
                                        const isCorrect = task.check_quiz_answer?.startsWith(letter);
                                        const wasChosen = answered === letter;
                                        return (
                                          <button
                                            key={oi}
                                            onClick={() => setQuizAnswered(prev => ({ ...prev, [task.id]: letter }))}
                                            className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                                              !answered
                                                ? 'border-slate-700 bg-slate-900 text-slate-300 hover:border-indigo-500/50 hover:bg-indigo-950/20'
                                                : wasChosen && isCorrect
                                                ? 'border-emerald-500/50 bg-emerald-950/30 text-emerald-300'
                                                : wasChosen && !isCorrect
                                                ? 'border-red-500/40 bg-red-950/20 text-red-300'
                                                : isCorrect
                                                ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-400'
                                                : 'border-slate-700 bg-slate-900 text-slate-500'
                                            }`}
                                          >
                                            {opt}
                                          </button>
                                        );
                                      })}
                                    </div>
                                    {quizAnswered[task.id] && task.check_quiz_answer && (
                                      <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-[11px] text-indigo-300">
                                        <strong>Explanation:</strong> {task.check_quiz_answer}
                                      </div>
                                    )}
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
                      <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center space-x-1.5">
                        <Code className="w-3.5 h-3.5" />
                        <span>Phase Capstone Project</span>
                      </h4>
                      {(phase as any).projects.map((proj: any) => (
                        <div key={proj.id} className="p-5 rounded-xl bg-gradient-to-r from-purple-950/30 to-slate-950 border border-purple-500/20 space-y-2">
                          <div className="flex items-center justify-between">
                            <h5 className="text-sm font-bold text-white">{proj.title}</h5>
                            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300">
                              {proj.difficulty}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300">{proj.objective}</p>
                          <div className="text-[11px] text-purple-300 font-medium pt-1">
                            <strong>Resume Impact:</strong> {proj.resume_relevance}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Portfolio Project (single object format) */}
                  {(phase as any).project && (
                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center space-x-1.5">
                        <Code className="w-3.5 h-3.5" />
                        <span>Phase Capstone Project</span>
                      </h4>
                      <div className="p-5 rounded-xl bg-gradient-to-r from-purple-950/30 to-slate-950 border border-purple-500/20 space-y-2">
                        <div className="flex items-center justify-between">
                          <h5 className="text-sm font-bold text-white">{(phase as any).project.title}</h5>
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300">
                            {(phase as any).project.difficulty}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300">{(phase as any).project.objective}</p>
                        <div className="text-[11px] text-purple-300 font-medium pt-1">
                          <strong>Resume Impact:</strong> {(phase as any).project.resume_relevance}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Phase Milestone */}
                  {(phase as any).milestones && (phase as any).milestones.length > 0 && (
                    <div className="pt-2">
                      {(phase as any).milestones.map((m: any) => (
                        <div key={m.id} className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center space-x-3">
                          <Award className="w-5 h-5 text-amber-400" />
                          <div>
                            <h5 className="text-xs font-bold text-slate-200">{m.title}</h5>
                            <p className="text-[11px] text-slate-400">{m.criteria}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Milestone (single object format) */}
                  {(phase as any).milestone && (
                    <div className="pt-2">
                      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center space-x-3">
                        <Award className="w-5 h-5 text-amber-400" />
                        <div>
                          <h5 className="text-xs font-bold text-slate-200">{(phase as any).milestone.title}</h5>
                          <p className="text-[11px] text-slate-400">{(phase as any).milestone.criteria}</p>
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
