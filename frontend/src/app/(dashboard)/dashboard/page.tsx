'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useLanguage } from '@/context/LanguageContext';
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  Award,
  FileText,
  Briefcase,
  Target,
  MapPin,
  Mic,
  Zap,
  CheckCircle,
  Compass,
  BookOpen,
  Dumbbell,
  GraduationCap,
  ChevronRight,
  Check
} from 'lucide-react';
import {
  getAssessmentResult,
  getResumeAnalysis,
  getRecommendedJobs,
  getUserApplications,
  getCurrentRoadmap,
  getInterviewHistory,
} from '@/lib/api-client';
import { getDigitalTwinProfile } from '@/lib/digital-twin-api';
import {
  AssessmentResultData,
  ResumeAnalysisData,
  JobMatchAnalysis,
  JobApplicationData,
  CareerDigitalTwinData,
  RoadmapData,
  InterviewSessionData,
} from '@/lib/types';

export default function DashboardPage() {
  const { t } = useLanguage();
  const [assessmentData, setAssessmentData] = useState<AssessmentResultData | null>(null);
  const [resumeData, setResumeData] = useState<ResumeAnalysisData | null>(null);
  const [roadmapData, setRoadmapData] = useState<RoadmapData | null>(null);
  const [interviewHistory, setInterviewHistory] = useState<InterviewSessionData[]>([]);
  const [jobMatches, setJobMatches] = useState<JobMatchAnalysis[]>([]);
  const [userApps, setUserApps] = useState<JobApplicationData[]>([]);
  const [twin, setTwin] = useState<CareerDigitalTwinData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [assessRes, resumeRes, roadmapRes, interviewRes, jobsRes, appsRes, twinRes] = await Promise.allSettled([
          getAssessmentResult(),
          getResumeAnalysis(),
          getCurrentRoadmap(),
          getInterviewHistory(),
          getRecommendedJobs(),
          getUserApplications(),
          getDigitalTwinProfile(),
        ]);

        if (assessRes.status === 'fulfilled') setAssessmentData(assessRes.value);
        if (resumeRes.status === 'fulfilled') setResumeData(resumeRes.value);
        if (roadmapRes.status === 'fulfilled') setRoadmapData(roadmapRes.value);
        if (interviewRes.status === 'fulfilled') setInterviewHistory(interviewRes.value);
        if (jobsRes.status === 'fulfilled') setJobMatches(jobsRes.value);
        if (appsRes.status === 'fulfilled') setUserApps(appsRes.value);
        if (twinRes.status === 'fulfilled') setTwin(twinRes.value);
      } catch (err) {
        console.error('Dashboard data load error:', err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const targetCareer = twin?.target_career || assessmentData?.selected_target_career || null;
  const topJobMatch = jobMatches.length > 0 ? jobMatches[0] : null;
  const atsScore = resumeData?.ats_score ?? null;
  const readinessScore = twin?.overall_readiness_score ?? 0;
  const readinessLabel = twin?.readiness_label ?? 'Not Started';
  const nextAction = twin?.next_action;
  const subScores = twin?.sub_scores;

  // ----------------------------------------------------
  // Dynamic 8-Step Career Working Flow Calculation (Real DB State)
  // Workflow: Discovery → Resume → Skills → Roadmap → Practice → Interview → Jobs → Readiness
  // ----------------------------------------------------
  const isStep1Done = Boolean(
    targetCareer || 
    assessmentData?.selected_target_career || 
    (assessmentData?.analysis?.recommended_careers && assessmentData.analysis.recommended_careers.length > 0)
  );

  const isStep2Done = Boolean(resumeData && resumeData.ats_score > 0);

  const verifiedSkillsCount = (twin?.top_skills && twin.top_skills.length) || (resumeData?.extracted_skills && resumeData.extracted_skills.length) || 0;
  const isStep3Done = Boolean(verifiedSkillsCount > 0 || (assessmentData?.analysis?.skills_identified && assessmentData.analysis.skills_identified.length > 0));

  const isStep4Done = Boolean(roadmapData && roadmapData.phases && roadmapData.phases.length > 0);

  const practiceCount = (twin?.evidence_summary?.tasks as any)?.completed_count || 0;
  const isStep5Done = Boolean(practiceCount > 0 || (roadmapData?.phases?.some(p => p.milestones?.some(m => m.is_completed))));

  const completedInterviews = interviewHistory.filter(i => i.is_completed);
  const isStep6Done = Boolean(
    completedInterviews.length > 0 || 
    (twin?.evidence_summary?.interviews as any)?.completed_count > 0 ||
    (twin?.sub_scores?.interview_readiness ?? 0) > 0
  );

  const isStep7Done = Boolean(userApps.length > 0 || jobMatches.length > 0);

  const isStep8Done = Boolean(readinessScore >= 70);

  const stepsState = [
    {
      num: 1,
      id: 'discovery',
      name: 'Discovery Assessment',
      shortName: 'Discovery',
      href: '/assessment',
      icon: Compass,
      isDone: isStep1Done,
      desc: '12-dimension strength & role analysis',
      statusText: isStep1Done ? `Role: ${targetCareer || 'Discovered'}` : 'Not yet completed',
      actionText: isStep1Done ? 'Revisit Assessment' : 'Start Assessment',
    },
    {
      num: 2,
      id: 'resume',
      name: 'Resume & ATS',
      shortName: 'Resume',
      href: '/resume',
      icon: FileText,
      isDone: isStep2Done,
      desc: 'ATS scan & verified skill extraction',
      statusText: isStep2Done ? `ATS Score: ${atsScore}%` : 'Resume not scanned',
      actionText: isStep2Done ? 'View Resume ATS' : 'Upload Resume',
    },
    {
      num: 3,
      id: 'skills',
      name: 'Skill Matrix',
      shortName: 'Skills',
      href: '/skills',
      icon: Award,
      isDone: isStep3Done,
      desc: 'Target benchmark gaps & proficiencies',
      statusText: isStep3Done ? `${verifiedSkillsCount} Verified Skills` : 'No skills mapped',
      actionText: isStep3Done ? 'Manage Skills' : 'Explore Matrix',
    },
    {
      num: 4,
      id: 'roadmap',
      name: 'Roadmap & Tasks',
      shortName: 'Roadmap',
      href: '/roadmap',
      icon: MapPin,
      isDone: isStep4Done,
      desc: 'Personalized milestone-driven curriculum',
      statusText: isStep4Done ? `${roadmapData?.phases?.length || 0} Phases (${roadmapData?.overall_progress_percent || 0}% Done)` : 'No active roadmap',
      actionText: isStep4Done ? 'View Roadmap' : 'Generate Roadmap',
    },
    {
      num: 5,
      id: 'practice',
      name: 'Micro Practice',
      shortName: 'Practice',
      href: '/practice',
      icon: Dumbbell,
      isDone: isStep5Done,
      desc: 'Daily skill challenges & proof-of-work',
      statusText: isStep5Done ? `${practiceCount} Evidence Points` : 'Start first challenge',
      actionText: isStep5Done ? 'Practice Daily' : 'Start Practice',
    },
    {
      num: 6,
      id: 'interview',
      name: 'Mock Interview',
      shortName: 'Interview',
      href: '/interview',
      icon: Mic,
      isDone: isStep6Done,
      desc: 'Adaptive technical & STAR behavioral prep',
      statusText: isStep6Done ? `${completedInterviews.length} Sessions Complete` : 'No sessions taken',
      actionText: isStep6Done ? 'Practice Again' : 'Start Interview',
    },
    {
      num: 7,
      id: 'jobs',
      name: 'Job Engine',
      shortName: 'Jobs',
      href: '/jobs',
      icon: Briefcase,
      isDone: isStep7Done,
      desc: 'Live listings & AI role compatibility',
      statusText: isStep7Done ? `${jobMatches.length} Matching Roles` : 'Check opportunities',
      actionText: isStep7Done ? 'Explore Jobs' : 'Find Matches',
    },
    {
      num: 8,
      id: 'readiness',
      name: 'Placement Readiness',
      shortName: 'Readiness',
      href: '/placement',
      icon: GraduationCap,
      isDone: isStep8Done,
      desc: '10-point checklist & Student Career Brief',
      statusText: isStep8Done ? `${readinessScore}% - Placement Ready` : `${readinessScore}% current score`,
      actionText: isStep8Done ? 'Export Career Brief' : 'Review Checklist',
    },
  ];

  const completedStepsCount = stepsState.filter((s) => s.isDone).length;
  const workflowProgressPct = Math.round((completedStepsCount / 8) * 100);

  // Determine the next incomplete step as Today's Focus
  const getNextStepInfo = () => {
    if (!isStep1Done) {
      return {
        stepNum: 1,
        title: 'Step 1 Focus: Complete Discovery Assessment',
        desc: 'Take the 12-dimension discovery assessment to identify your natural strengths, work archetype, and recommended career trajectories.',
        href: '/assessment',
        btnText: 'Start Discovery Assessment →',
      };
    }
    if (!isStep2Done) {
      return {
        stepNum: 2,
        title: 'Step 2 Focus: Upload & Optimize Your Resume',
        desc: 'Scan your resume against ATS benchmarks to measure your keyword compatibility and automatically extract verified skills.',
        href: '/resume',
        btnText: 'Upload & Scan Resume →',
      };
    }
    if (!isStep3Done) {
      return {
        stepNum: 3,
        title: 'Step 3 Focus: Review Skill Matrix & Gaps',
        desc: 'Inspect your target career benchmark, verify existing skill proficiencies, and pinpoint high-priority missing prerequisites.',
        href: '/skills',
        btnText: 'Explore Skill Matrix →',
      };
    }
    if (!isStep4Done) {
      return {
        stepNum: 4,
        title: 'Step 4 Focus: Generate Personalized Learning Roadmap',
        desc: 'Build your custom, prerequisite-ordered learning path tailored to close your verified skill gaps with clear milestones.',
        href: '/roadmap',
        btnText: 'Generate Roadmap →',
      };
    }
    if (!isStep5Done) {
      return {
        stepNum: 5,
        title: 'Step 5 Focus: Complete Your First Micro Practice Task',
        desc: 'Solve bite-sized daily challenges to reinforce your technical knowledge and earn verified proof-of-work evidence.',
        href: '/practice',
        btnText: 'Start Micro Practice →',
      };
    }
    if (!isStep6Done) {
      return {
        stepNum: 6,
        title: 'Step 6 Focus: Practice Your First AI Mock Interview',
        desc: 'Test your technical, HR, and STAR behavioral answers with real-time feedback and skill evidence points.',
        href: '/interview',
        btnText: 'Start Mock Interview →',
      };
    }
    if (!isStep7Done) {
      return {
        stepNum: 7,
        title: 'Step 7 Focus: Explore Matching Job Opportunities',
        desc: 'Browse live tech openings ranked by compatibility with your Digital Twin profile and apply with 1-click tailored readiness.',
        href: '/jobs',
        btnText: 'Explore Job Engine →',
      };
    }
    if (!isStep8Done) {
      return {
        stepNum: 8,
        title: 'Step 8 Focus: Boost Placement Readiness & Export Brief',
        desc: 'Achieve 80%+ readiness score, verify your 10-point placement checklist, and export your 1-Page Student Career Brief.',
        href: '/placement',
        btnText: 'Review Placement Checklist →',
      };
    }
    return {
      stepNum: 0,
      title: "🎉 Full Career Trajectory Activated!",
      desc: 'All 8 foundational milestones are underway! Review your 10-point Placement Readiness checklist and export your 1-Page Student Career Brief.',
      href: '/placement',
      btnText: 'Check Placement Readiness & Brief →',
    };
  };

  const nextStep = getNextStepInfo();

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Welcome Banner */}
      <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-indigo-950/70 via-slate-900 to-purple-950/70 border border-indigo-500/20 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3 sm:space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>{t('app.title', 'AI Career Coach')}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            {t('dashboard.welcome', 'Welcome back')}! {t('header.cockpit', 'AI Career Coach Cockpit')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            {t('dashboard.subtitle', 'Your single unified Career Digital Twin brings together assessments, resume ATS optimization, verified skill matrix, learning roadmaps, job opportunities, and AI mock interviews.')}
          </p>

          <div className="pt-2 flex flex-wrap gap-2.5 sm:gap-3">
            <Link
              href="/guide"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs sm:text-sm transition-all shadow-lg shadow-purple-600/30 flex items-center space-x-2"
            >
              <BookOpen className="w-4 h-4" />
              <span>{t('nav.guide', 'How to Use / Guide')}</span>
            </Link>
            <Link
              href="/progress"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span>{t('nav.progress', 'Progress & Readiness')}</span>
            </Link>
            <Link
              href="/jobs"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <Briefcase className="w-4 h-4 text-emerald-400" />
              <span>{t('nav.jobs', 'Job Engine')}</span>
            </Link>
            <Link
              href="/interview"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <Mic className="w-4 h-4 text-pink-400" />
              <span>{t('nav.interview', 'Mock Interview')}</span>
            </Link>
            <Link
              href="/roadmap"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <MapPin className="w-4 h-4 text-indigo-400" />
              <span>{t('nav.roadmap', 'Roadmap & Tasks')}</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------- */}
      {/* FEATURE 1: Interactive 8-Step Career Working Flow    */}
      {/* Workflow: Discovery → Resume → Skills → Roadmap → Practice → Interview → Jobs → Readiness */}
      {/* ---------------------------------------------------- */}
      <section className="p-6 sm:p-7 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-5">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Compass className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">
                Career Working Flow: 8 Steps to Placement
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Follow your guided trajectory from assessment to final placement readiness.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <div className="text-right">
              <span className="text-xs font-bold text-slate-200">
                Progress: <span className="text-indigo-400">{completedStepsCount}</span> / 8 Steps
              </span>
              <p className="text-[11px] text-slate-500">{workflowProgressPct}% Complete</p>
            </div>
            <div className="w-20 sm:w-28 bg-slate-800 h-2.5 rounded-full overflow-hidden border border-slate-700">
              <div
                className="bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 h-full rounded-full transition-all duration-700"
                style={{ width: `${workflowProgressPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Workflow Horizontal Stepper Pipeline */}
        <div className="overflow-x-auto pb-2 scrollbar-none">
          <div className="flex items-center justify-between min-w-[700px] gap-1 px-1">
            {stepsState.map((st, idx) => {
              const isCurrentFocus = nextStep.stepNum === st.num;
              return (
                <React.Fragment key={st.id}>
                  <Link
                    href={st.href}
                    className={`group flex items-center space-x-2 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                      st.isDone
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                        : isCurrentFocus
                        ? 'bg-amber-500/15 border-amber-500/40 text-amber-300 ring-2 ring-amber-500/30 shadow-md shadow-amber-500/10'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                        st.isDone
                          ? 'bg-emerald-500 text-slate-950'
                          : isCurrentFocus
                          ? 'bg-amber-400 text-slate-950 animate-pulse'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {st.isDone ? <Check className="w-3 h-3 stroke-[3]" /> : st.num}
                    </div>
                    <span className="whitespace-nowrap font-semibold">{st.shortName}</span>
                  </Link>
                  {idx < stepsState.length - 1 && (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Dynamic Priority Callout Banner: Next Step / Today's Focus */}
        <div className="p-4 sm:p-5 rounded-xl bg-gradient-to-r from-indigo-950/70 via-purple-950/60 to-slate-900 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400 animate-pulse" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                {nextStep.stepNum > 0 ? `Today's Focus • Step ${nextStep.stepNum} of 8` : 'All 8 Steps Active'}
              </span>
            </div>
            <h3 className="text-base font-bold text-white">{nextStep.title}</h3>
            <p className="text-xs text-slate-300 max-w-2xl">{nextStep.desc}</p>
          </div>

          <Link
            href={nextStep.href}
            className="px-4 sm:px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-2 shrink-0 transition shadow-lg shadow-indigo-600/30 self-start sm:self-auto"
          >
            <span>{nextStep.btnText}</span>
          </Link>
        </div>

        {/* 8 Interactive Step Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stepsState.map((st) => {
            const StepIcon = st.icon;
            const isCurrentFocus = nextStep.stepNum === st.num;
            return (
              <div
                key={st.id}
                className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 ${
                  st.isDone
                    ? 'bg-slate-950/60 border-emerald-500/30 shadow-sm'
                    : isCurrentFocus
                    ? 'bg-slate-950 border-amber-500/50 ring-1 ring-amber-500/30 shadow-md shadow-amber-500/5'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        st.isDone
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : isCurrentFocus
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                      }`}
                    >
                      <StepIcon className="w-4 h-4" />
                    </div>

                    {st.isDone ? (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle className="w-3 h-3" />
                        <span>Done</span>
                      </span>
                    ) : isCurrentFocus ? (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                        <span>Today&apos;s Focus</span>
                      </span>
                    ) : (
                      <span className="w-5 h-5 rounded-full border border-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">
                        {st.num}
                      </span>
                    )}
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-white">
                      {st.num}. {st.name}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">{st.desc}</p>
                    <p className="text-[11px] text-indigo-300 font-medium mt-1 truncate">
                      {st.statusText}
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-800/60 mt-3">
                  <Link
                    href={st.href}
                    className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors ${
                      st.isDone
                        ? 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
                        : isCurrentFocus
                        ? 'bg-gradient-to-r from-amber-500 to-indigo-600 text-white hover:from-amber-400 hover:to-indigo-500 shadow-md'
                        : 'bg-indigo-600 text-white hover:bg-indigo-500'
                    }`}
                  >
                    <span>{st.actionText}</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Next Best Action Widget */}
      {nextAction && nextAction.title && (
        <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/80 border border-indigo-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-bold uppercase text-amber-400">Next Best Action for You</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">{nextAction.related_goal}</span>
            </div>
            <h3 className="text-base font-bold text-white">{nextAction.title}</h3>
            <p className="text-xs text-slate-400">{nextAction.why_it_matters}</p>
          </div>
          <Link
            href={nextAction.action_link}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center space-x-2 shrink-0 self-start md:self-auto transition-colors shadow-md shadow-indigo-600/20"
          >
            <span>Start Now</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Real Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Career Readiness</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {readinessScore}<span className="text-sm font-normal text-slate-400">/100</span>
          </div>
          <p className="text-xs text-indigo-400 font-medium">
            {readinessScore > 0 ? readinessLabel : 'Complete Step 1 to calculate'}
          </p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Career</span>
            <Target className="w-4 h-4 text-purple-400" />
          </div>
          {targetCareer ? (
            <>
              <div className="text-lg sm:text-xl font-bold text-white mb-1 truncate">{targetCareer}</div>
              <p className="text-xs text-purple-400 font-medium">Active Direction</p>
            </>
          ) : (
            <>
              <div className="text-sm font-bold text-slate-400 mb-1">Not selected yet</div>
              <p className="text-xs text-slate-500 font-medium">Select in Step 1</p>
            </>
          )}
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">ATS Resume Score</span>
            <FileText className="w-4 h-4 text-emerald-400" />
          </div>
          {atsScore !== null ? (
            <>
              <div className="text-3xl font-bold text-white mb-1">{atsScore}%</div>
              <p className="text-xs text-emerald-400 font-medium truncate">{resumeData?.filename || 'Parsed Resume'}</p>
            </>
          ) : (
            <>
              <div className="text-sm font-bold text-slate-400 mb-1">Not scanned yet</div>
              <p className="text-xs text-slate-500 font-medium">Upload in Step 2</p>
            </>
          )}
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top Job Match</span>
            <Briefcase className="w-4 h-4 text-pink-400" />
          </div>
          {topJobMatch ? (
            <>
              <div className="text-3xl font-bold text-white mb-1">
                {topJobMatch.match_breakdown.overall_score}%
              </div>
              <p className="text-xs text-pink-400 font-medium truncate">{topJobMatch.job.title}</p>
            </>
          ) : (
            <>
              <div className="text-sm font-bold text-slate-400 mb-1">Matching Jobs...</div>
              <p className="text-xs text-slate-500 font-medium">Provider Catalog Sync</p>
            </>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Sub-Score Breakdown Preview */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Award className="w-5 h-5 text-indigo-400" />
                <span>Readiness Engine Health Breakdown</span>
              </h2>
              <Link href="/progress" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1">
                <span>View Full Analysis</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Skills (30%)</span>
                <p className="text-lg font-bold text-indigo-400">{subScores?.skill_readiness ?? 0}%</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Resume ATS (20%)</span>
                <p className="text-lg font-bold text-purple-400">{subScores?.resume_readiness ?? 0}%</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Interview (20%)</span>
                <p className="text-lg font-bold text-pink-400">{subScores?.interview_readiness ?? 0}%</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Roadmap (15%)</span>
                <p className="text-lg font-bold text-blue-400">{subScores?.roadmap_progress ?? 0}%</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Job Match (10%)</span>
                <p className="text-lg font-bold text-emerald-400">{subScores?.job_match_readiness ?? 0}%</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400">Portfolio (5%)</span>
                <p className="text-lg font-bold text-amber-400">{subScores?.portfolio_readiness ?? 0}%</p>
              </div>
            </div>
          </div>

          {/* Recommended Job Highlights */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Briefcase className="w-5 h-5 text-emerald-400" />
                <span>Top Matched Job Opportunities</span>
              </h2>
              <Link href="/jobs" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1">
                <span>View All Jobs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {jobMatches.length > 0 ? (
              <div className="space-y-3">
                {jobMatches.slice(0, 3).map((match) => (
                  <div key={match.job.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400">
                          {match.match_breakdown.overall_score}% Match
                        </span>
                        <h3 className="text-sm font-bold text-white">{match.job.title}</h3>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{match.job.company} • {match.job.location}</p>
                    </div>
                    <Link
                      href="/jobs"
                      className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shrink-0"
                    >
                      View Match
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic p-4 text-center">No job matches found yet. Search provider catalog.</div>
            )}
          </div>
        </div>

        {/* Right Column: Career Recommendations */}
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <h2 className="text-base font-bold text-white mb-1">Career Discovery Roles</h2>
            <p className="text-xs text-slate-400 mb-4">From your 12-dimension assessment</p>

            {assessmentData?.analysis?.recommended_careers ? (
              <div className="space-y-4">
                {assessmentData.analysis.recommended_careers.slice(0, 3).map((match) => (
                  <div key={match.slug} className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-slate-200 text-sm">{match.title}</h3>
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-500/20 text-indigo-400">
                        {match.match_percentage}% Match
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-indigo-500 h-full" style={{ width: `${match.match_percentage}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic">No discovery recommendations yet. Complete step 1 assessment to unlock.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
