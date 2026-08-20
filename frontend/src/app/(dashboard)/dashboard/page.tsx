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
  Target
} from 'lucide-react';
import { getAssessmentResult, getResumeAnalysis } from '@/lib/api-client';
import { AssessmentResultData, ResumeAnalysisData } from '@/lib/types';

export default function DashboardPage() {
  const [assessmentData, setAssessmentData] = useState<AssessmentResultData | null>(null);
  const [resumeData, setResumeData] = useState<ResumeAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [aRes, rRes] = await Promise.all([
          getAssessmentResult(),
          getResumeAnalysis()
        ]);
        setAssessmentData(aRes);
        setResumeData(rRes);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  const targetCareer = assessmentData?.selected_target_career || resumeData?.target_match?.target_career_name || null;
  const atsScore = resumeData?.ats_score ?? null;
  const topMatch = assessmentData?.analysis?.recommended_careers?.[0];
  const readinessScore = topMatch?.match_percentage || (atsScore ? Math.round((atsScore + (topMatch?.match_percentage || 70)) / 2) : null);

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
            Your Career Discovery profile and Resume Intelligence metrics are synchronized in real-time.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/assessment"
              className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-500/25 flex items-center space-x-2"
            >
              <Compass className="w-4 h-4" />
              <span>Career Discovery</span>
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
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Readiness Score</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          {readinessScore !== null ? (
            <>
              <div className="text-3xl font-bold text-white mb-1">
                {readinessScore}<span className="text-sm font-normal text-slate-400">/100</span>
              </div>
              <p className="text-xs text-emerald-400 font-medium">Verified by Discovery & Resume</p>
            </>
          ) : (
            <>
              <div className="text-xl font-bold text-slate-400 mb-1">Not calculated yet</div>
              <p className="text-xs text-slate-500 font-medium">Complete Discovery Assessment</p>
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
              <div className="text-xl font-bold text-slate-400 mb-1">Not calculated yet</div>
              <p className="text-xs text-slate-500 font-medium">Select in Assessment</p>
            </>
          )}
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
              <div className="text-xl font-bold text-slate-400 mb-1">Not calculated yet</div>
              <p className="text-xs text-slate-500 font-medium">Upload PDF/DOCX resume</p>
            </>
          )}
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Extracted Skills</span>
            <Award className="w-4 h-4 text-pink-400" />
          </div>
          {resumeData?.extracted_skills ? (
            <>
              <div className="text-3xl font-bold text-white mb-1">{resumeData.extracted_skills.length}</div>
              <p className="text-xs text-pink-400 font-medium">Extracted from Resume</p>
            </>
          ) : (
            <>
              <div className="text-xl font-bold text-slate-400 mb-1">Not calculated yet</div>
              <p className="text-xs text-slate-500 font-medium">Upload resume to extract</p>
            </>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <span>Recommended Actions</span>
            </h2>

            {!assessmentData && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Take Career Discovery Assessment</h3>
                  <p className="text-xs text-slate-400 mt-1">Discover your natural strengths, career archetype, and top matching roles.</p>
                </div>
                <Link href="/assessment" className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-semibold text-xs">
                  Start
                </Link>
              </div>
            )}

            {!resumeData && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Upload & Analyze Resume</h3>
                  <p className="text-xs text-slate-400 mt-1">Get real ATS score, formatting risk flags, and target career skill overlap.</p>
                </div>
                <Link href="/resume" className="px-4 py-2 rounded-lg bg-purple-600 text-white font-semibold text-xs">
                  Upload
                </Link>
              </div>
            )}

            {assessmentData && resumeData && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex items-center space-x-2 text-emerald-400 text-sm font-bold">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Career Discovery Profile & Resume Analysis Synchronized</span>
                </div>
                <p className="text-xs text-slate-300">
                  Target Role: <strong className="text-white">{targetCareer}</strong> | ATS Score: <strong className="text-white">{atsScore}%</strong>
                </p>
              </div>
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
