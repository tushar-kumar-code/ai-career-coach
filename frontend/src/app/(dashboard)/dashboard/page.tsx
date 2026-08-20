'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  Sparkles, 
  Compass, 
  FileText, 
  Award, 
  Briefcase, 
  MapPin, 
  Mic, 
  TrendingUp, 
  CheckCircle2, 
  ArrowRight,
  Target,
  Clock,
  Layers,
  Building
} from 'lucide-react';
import { 
  getAssessmentResult, 
  getResumeAnalysis, 
  getCurrentRoadmap, 
  getTodayTasks,
  getRecommendedJobs,
  getUserApplications
} from '@/lib/api-client';
import { 
  AssessmentResultData, 
  ResumeAnalysisData, 
  RoadmapData, 
  DailyTasksData,
  JobMatchAnalysis,
  JobApplicationData
} from '@/lib/types';

export default function DashboardPage() {
  const [assessmentData, setAssessmentData] = useState<AssessmentResultData | null>(null);
  const [resumeData, setResumeData] = useState<ResumeAnalysisData | null>(null);
  const [roadmapData, setRoadmapData] = useState<RoadmapData | null>(null);
  const [todayData, setTodayData] = useState<DailyTasksData | null>(null);
  const [jobMatches, setJobMatches] = useState<JobMatchAnalysis[]>([]);
  const [userApps, setUserApps] = useState<JobApplicationData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [aRes, rRes, rmRes, tRes, jRes, appRes] = await Promise.all([
          getAssessmentResult(),
          getResumeAnalysis(),
          getCurrentRoadmap(),
          getTodayTasks().catch(() => null),
          getRecommendedJobs().catch(() => []),
          getUserApplications().catch(() => [])
        ]);
        setAssessmentData(aRes);
        setResumeData(rRes);
        setRoadmapData(rmRes);
        setTodayData(tRes);
        setJobMatches(jRes);
        setUserApps(appRes);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  const targetCareer = assessmentData?.selected_target_career || resumeData?.target_match?.target_career_name || roadmapData?.target_role || null;
  const atsScore = resumeData?.ats_score ?? null;
  const topJobMatch = jobMatches.length > 0 ? jobMatches[0] : null;
  const topMatch = assessmentData?.analysis?.recommended_careers?.[0];
  const readinessScore = topJobMatch ? topJobMatch.match_breakdown.overall_score : (topMatch?.match_percentage || (atsScore ? Math.round((atsScore + (topMatch?.match_percentage || 70)) / 2) : null));

  return (
    <div className="space-y-8 pb-12">
      {/* Top Banner / Welcome */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900 border border-indigo-500/20 relative overflow-hidden">
        <div className="max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium mb-3">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Digital Twin Calibrated</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">
            Welcome to your AI Career Dashboard
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed mb-6">
            Your Career Discovery profile, Resume Intelligence, Roadmap, and Job Intelligence are synchronized in real-time.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/jobs"
              className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-500/25 flex items-center space-x-2"
            >
              <Briefcase className="w-4 h-4" />
              <span>Job Intelligence & Tracker</span>
            </Link>
            <Link
              href="/roadmap"
              className="px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center space-x-2"
            >
              <MapPin className="w-4 h-4 text-indigo-400" />
              <span>Career Roadmap</span>
            </Link>
            <Link
              href="/resume"
              className="px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center space-x-2"
            >
              <FileText className="w-4 h-4 text-purple-400" />
              <span>Resume Intelligence</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Real Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top Job Match</span>
            <Briefcase className="w-4 h-4 text-emerald-400" />
          </div>
          {topJobMatch ? (
            <>
              <div className="text-3xl font-bold text-white mb-1">
                {topJobMatch.match_breakdown.overall_score}%
              </div>
              <p className="text-xs text-emerald-400 font-medium truncate">{topJobMatch.job.title}</p>
            </>
          ) : (
            <>
              <div className="text-xl font-bold text-slate-400 mb-1">Scanning Jobs...</div>
              <p className="text-xs text-slate-500 font-medium">Provider Catalog Sync</p>
            </>
          )}
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Career</span>
            <Target className="w-4 h-4 text-indigo-400" />
          </div>
          {targetCareer ? (
            <>
              <div className="text-xl font-bold text-white mb-1 truncate">{targetCareer}</div>
              <p className="text-xs text-indigo-400 font-medium">Active Selection</p>
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
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Applications</span>
            <Briefcase className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">{userApps.length}</div>
          <p className="text-xs text-indigo-400 font-medium">Application Tracker Sync</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">ATS Resume Score</span>
            <FileText className="w-4 h-4 text-purple-400" />
          </div>
          {atsScore !== null ? (
            <>
              <div className="text-3xl font-bold text-white mb-1">{atsScore}%</div>
              <p className="text-xs text-purple-400 font-medium">{resumeData?.filename || 'Parsed Resume'}</p>
            </>
          ) : (
            <>
              <div className="text-xl font-bold text-slate-400 mb-1">Not calculated</div>
              <p className="text-xs text-slate-500 font-medium">Upload PDF/DOCX resume</p>
            </>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Recommended Job Highlights */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                <Briefcase className="w-5 h-5 text-indigo-400" />
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
              <div className="text-xs text-slate-500 italic p-4 text-center">No job matches found. Search provider catalog.</div>
            )}
          </div>
        </div>

        {/* Right Column: Career Recommendations */}
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <h2 className="text-lg font-bold text-white mb-1">Recommended Roles</h2>
            <p className="text-xs text-slate-400 mb-6">From your Career Discovery profile</p>

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
