'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
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
  Compass
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
  // Dynamic 4-Step Onboarding Checklist Calculation (Real DB State)
  // ----------------------------------------------------
  const isStep1Done = Boolean(
    targetCareer || 
    assessmentData?.selected_target_career || 
    (assessmentData?.analysis?.recommended_careers && assessmentData.analysis.recommended_careers.length > 0)
  );

  const isStep2Done = Boolean(resumeData && resumeData.ats_score > 0);

  const isStep3Done = Boolean(roadmapData && roadmapData.phases && roadmapData.phases.length > 0);

  const completedInterviews = interviewHistory.filter(i => i.is_completed);
  const isStep4Done = Boolean(
    completedInterviews.length > 0 || 
    (twin?.evidence_summary?.interviews as any)?.completed_count > 0 ||
    (twin?.sub_scores?.interview_readiness ?? 0) > 0
  );

  const completedStepsCount = [isStep1Done, isStep2Done, isStep3Done, isStep4Done].filter(Boolean).length;
  const onboardingProgressPct = (completedStepsCount / 4) * 100;

  // Determine the next incomplete step
  const getNextStepInfo = () => {
    if (!isStep1Done) {
      return {
        stepNum: 1,
        title: 'Discover Your Target Career Role',
        desc: 'Take the 12-dimension discovery assessment to identify your natural strengths and ideal career direction.',
        href: '/assessment',
        btnText: 'Start Career Discovery →',
      };
    }
    if (!isStep2Done) {
      return {
        stepNum: 2,
        title: 'Upload & Optimize Your Resume',
        desc: 'Scan your resume against ATS benchmarks and automatically extract verified skills into your skill matrix.',
        href: '/resume',
        btnText: 'Upload Resume →',
      };
    }
    if (!isStep3Done) {
      return {
        stepNum: 3,
        title: 'Generate Personalized Learning Roadmap',
        desc: 'Build your custom, prerequisite-ordered learning path tailored to close your verified skill gaps.',
        href: '/roadmap',
        btnText: 'Build Roadmap →',
      };
    }
    if (!isStep4Done) {
      return {
        stepNum: 4,
        title: 'Practice Your First AI Mock Interview',
        desc: 'Test your technical, HR, and STAR behavioral answers with real-time feedback and skill evidence points.',
        href: '/interview',
        btnText: 'Start Mock Interview →',
      };
    }
    return {
      stepNum: 0,
      title: "🎉 You're Job Ready to Move Forward",
      desc: 'All foundational onboarding steps are complete! Review your 10-point Placement Readiness checklist and export your 1-Page Student Career Brief.',
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
            <span>AI Career Twin & Intelligence Platform</span>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            Welcome to Your AI Career Cockpit
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Your single unified Career Digital Twin brings together assessments, resume ATS optimization, verified skill matrix, learning roadmaps, job opportunities, and AI mock interviews.
          </p>

          <div className="pt-2 flex flex-wrap gap-2.5 sm:gap-3">
            <Link
              href="/progress"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs sm:text-sm transition-all shadow-lg shadow-indigo-600/30 flex items-center space-x-2"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Readiness Progress</span>
            </Link>
            <Link
              href="/jobs"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <Briefcase className="w-4 h-4 text-emerald-400" />
              <span>Job Tracker</span>
            </Link>
            <Link
              href="/interview"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <Mic className="w-4 h-4 text-pink-400" />
              <span>Mock Interview</span>
            </Link>
            <Link
              href="/roadmap"
              className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs sm:text-sm transition-all flex items-center space-x-2"
            >
              <MapPin className="w-4 h-4 text-indigo-400" />
              <span>Career Roadmap</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------- */}
      {/* FEATURE 1: Interactive 4-Step Onboarding Checklist   */}
      {/* ---------------------------------------------------- */}
      <section className="p-6 sm:p-7 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-5">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Compass className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">
                Getting Started: 4 Steps to Job-Ready
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              {completedStepsCount === 4
                ? 'All foundational steps completed. Your Career Digital Twin is continuously learning!'
                : 'Complete these essential milestones to activate your complete Career Digital Twin.'}
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <div className="text-right">
              <span className="text-xs font-bold text-slate-200">
                Progress: <span className="text-indigo-400">{completedStepsCount}</span> / 4 Completed
              </span>
              <p className="text-[11px] text-slate-500">{Math.round(onboardingProgressPct)}% Complete</p>
            </div>
            <div className="w-16 sm:w-24 bg-slate-800 h-2.5 rounded-full overflow-hidden border border-slate-700">
              <div
                className="bg-gradient-to-r from-indigo-500 to-emerald-500 h-full rounded-full transition-all duration-700"
                style={{ width: `${onboardingProgressPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Dynamic Priority Callout Banner */}
        <div className="p-4 sm:p-5 rounded-xl bg-gradient-to-r from-indigo-950/60 to-purple-950/60 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400 animate-pulse" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                {nextStep.stepNum > 0 ? `Step ${nextStep.stepNum} Recommended` : 'Full Readiness Activated'}
              </span>
            </div>
            <h3 className="text-base font-bold text-white">{nextStep.title}</h3>
            <p className="text-xs text-slate-300 max-w-2xl">{nextStep.desc}</p>
          </div>

          <Link
            href={nextStep.href}
            className="px-4 sm:px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-2 shrink-0 transition-colors shadow-lg shadow-indigo-600/30 self-start sm:self-auto"
          >
            <span>{nextStep.btnText}</span>
          </Link>
        </div>

        {/* 4 Interactive Step Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Step 1 Card: Career Discovery */}
          <div
            className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 ${
              isStep1Done
                ? 'bg-slate-950/60 border-emerald-500/30 shadow-sm'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Compass className="w-4 h-4" />
                </div>
                {isStep1Done ? (
                  <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <CheckCircle className="w-3 h-3" />
                    <span>Done</span>
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border border-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">
                    1
                  </span>
                )}
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">1. Discover Career</h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  {isStep1Done
                    ? `Selected: ${targetCareer || 'Career Discovered'}`
                    : '12-dimension survey matching natural strengths.'}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/60 mt-3">
              <Link
                href="/assessment"
                className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors ${
                  isStep1Done
                    ? 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
                    : 'bg-indigo-600 text-white hover:bg-indigo-500'
                }`}
              >
                <span>{isStep1Done ? 'Revisit Role' : 'Discover Career'}</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Step 2 Card: Resume Intelligence */}
          <div
            className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 ${
              isStep2Done
                ? 'bg-slate-950/60 border-emerald-500/30 shadow-sm'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <FileText className="w-4 h-4" />
                </div>
                {isStep2Done ? (
                  <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <CheckCircle className="w-3 h-3" />
                    <span>Done</span>
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border border-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">
                    2
                  </span>
                )}
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">2. Upload Resume</h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  {isStep2Done
                    ? `ATS Score: ${atsScore}% (${resumeData?.filename || 'Uploaded'})`
                    : 'Scan PDF/DOCX for ATS score & verified skills.'}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/60 mt-3">
              <Link
                href="/resume"
                className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors ${
                  isStep2Done
                    ? 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
                    : 'bg-indigo-600 text-white hover:bg-indigo-500'
                }`}
              >
                <span>{isStep2Done ? 'View Analysis' : 'Upload Resume'}</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Step 3 Card: Personalized Roadmap */}
          <div
            className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 ${
              isStep3Done
                ? 'bg-slate-950/60 border-emerald-500/30 shadow-sm'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <MapPin className="w-4 h-4" />
                </div>
                {isStep3Done ? (
                  <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <CheckCircle className="w-3 h-3" />
                    <span>Done</span>
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border border-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">
                    3
                  </span>
                )}
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">3. Build Roadmap</h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  {isStep3Done
                    ? `${roadmapData?.phases?.length || 0} Phases active (${roadmapData?.overall_progress_percent || 0}% progress)`
                    : 'Prerequisite-ordered daily tasks & projects.'}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/60 mt-3">
              <Link
                href="/roadmap"
                className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors ${
                  isStep3Done
                    ? 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
                    : 'bg-indigo-600 text-white hover:bg-indigo-500'
                }`}
              >
                <span>{isStep3Done ? 'Open Roadmap' : 'Build Roadmap'}</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Step 4 Card: AI Mock Interview */}
          <div
            className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 ${
              isStep4Done
                ? 'bg-slate-950/60 border-emerald-500/30 shadow-sm'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400">
                  <Mic className="w-4 h-4" />
                </div>
                {isStep4Done ? (
                  <span className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <CheckCircle className="w-3 h-3" />
                    <span>Done</span>
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border border-slate-700 text-slate-500 flex items-center justify-center text-[10px] font-bold">
                    4
                  </span>
                )}
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">4. Mock Interview</h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  {isStep4Done
                    ? `${completedInterviews.length} Completed Session(s) Recorded`
                    : 'Adaptive technical & STAR behavioral practice.'}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/60 mt-3">
              <Link
                href="/interview"
                className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors ${
                  isStep4Done
                    ? 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
                    : 'bg-indigo-600 text-white hover:bg-indigo-500'
                }`}
              >
                <span>{isStep4Done ? 'Practice Again' : 'Start Interview'}</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
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
