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
  Clock
} from 'lucide-react';
import {
  getAssessmentResult,
  getResumeAnalysis,
  getRecommendedJobs,
  getUserApplications,
} from '@/lib/api-client';
import { getDigitalTwinProfile } from '@/lib/digital-twin-api';
import {
  AssessmentResultData,
  ResumeAnalysisData,
  JobMatchAnalysis,
  JobApplicationData,
  CareerDigitalTwinData,
} from '@/lib/types';

export default function DashboardPage() {
  const [assessmentData, setAssessmentData] = useState<AssessmentResultData | null>(null);
  const [resumeData, setResumeData] = useState<ResumeAnalysisData | null>(null);
  const [jobMatches, setJobMatches] = useState<JobMatchAnalysis[]>([]);
  const [userApps, setUserApps] = useState<JobApplicationData[]>([]);
  const [twin, setTwin] = useState<CareerDigitalTwinData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [assessRes, resumeRes, jobsRes, appsRes, twinRes] = await Promise.allSettled([
          getAssessmentResult(),
          getResumeAnalysis(),
          getRecommendedJobs(),
          getUserApplications(),
          getDigitalTwinProfile(),
        ]);

        if (assessRes.status === 'fulfilled') setAssessmentData(assessRes.value);
        if (resumeRes.status === 'fulfilled') setResumeData(resumeRes.value);
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

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-purple-950/60 border border-indigo-500/20 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Career Twin & Intelligence Platform</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
            Welcome to Your AI Career Cockpit
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed">
            Your single unified Career Digital Twin brings together assessments, resume ATS optimization, verified skill matrix, learning roadmaps, job opportunities, and AI mock interviews.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              href="/progress"
              className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-600/30 flex items-center space-x-2"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Readiness Progress</span>
            </Link>
            <Link
              href="/jobs"
              className="px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center space-x-2"
            >
              <Briefcase className="w-4 h-4 text-emerald-400" />
              <span>Job Tracker</span>
            </Link>
            <Link
              href="/interview"
              className="px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center space-x-2"
            >
              <Mic className="w-4 h-4 text-pink-400" />
              <span>Mock Interview</span>
            </Link>
            <Link
              href="/roadmap"
              className="px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center space-x-2"
            >
              <MapPin className="w-4 h-4 text-indigo-400" />
              <span>Career Roadmap</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Next Best Action Widget */}
      {nextAction && nextAction.title && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-indigo-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
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
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center space-x-2 shrink-0 self-start md:self-auto transition-colors"
          >
            <span>Start Now</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Real Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Career Readiness</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {readinessScore}<span className="text-sm font-normal text-slate-400">/100</span>
          </div>
          <p className="text-xs text-indigo-400 font-medium">{readinessLabel}</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Career</span>
            <Target className="w-4 h-4 text-purple-400" />
          </div>
          {targetCareer ? (
            <>
              <div className="text-xl font-bold text-white mb-1 truncate">{targetCareer}</div>
              <p className="text-xs text-purple-400 font-medium">Active Direction</p>
            </>
          ) : (
            <>
              <div className="text-xl font-bold text-slate-400 mb-1">Not selected</div>
              <p className="text-xs text-slate-500 font-medium">Select in Assessment</p>
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
              <div className="text-xl font-bold text-slate-400 mb-1">Not calculated</div>
              <p className="text-xs text-slate-500 font-medium">Upload PDF/DOCX</p>
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
              <div className="text-xl font-bold text-slate-400 mb-1">Scanning Jobs...</div>
              <p className="text-xs text-slate-500 font-medium">Provider Catalog Sync</p>
            </>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Sub-Score Breakdown Preview */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Award className="w-5 h-5 text-indigo-400" />
                <span>Readiness Engine Health Breakdown</span>
              </h2>
              <Link href="/progress" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1">
                <span>View Breakdown</span>
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
                      <p className="text-xs text-slate-400 mt-1">{match.job.company} ? {match.job.location}</p>
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
              <div className="text-xs text-slate-500 italic">No discovery recommendations yet. Complete assessment to unlock.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

