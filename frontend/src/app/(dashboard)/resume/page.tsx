'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle,
  HelpCircle,
  Sparkles, 
  Loader2, 
  Target, 
  Award, 
  ShieldAlert, 
  TrendingUp, 
  RefreshCw,
  Compass,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Briefcase,
  GraduationCap
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { uploadResumeFile, getResumeAnalysis, matchJobDescription } from '@/lib/api-client';
import { ResumeAnalysisData, ScoringFactorItem, EligibilityItem } from '@/lib/types';
import SkillActionBadge from '@/components/common/SkillActionBadge';
import CandidateProfileCard from '@/components/resume/CandidateProfileCard';

export default function ResumePage() {
  const { user, isLoading: authLoading, markResumeAnalyzed, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [matchingJD, setMatchingJD] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jdError, setJdError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysisData | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobDescriptionInput, setJobDescriptionInput] = useState('');
  const [showJdPanel, setShowJdPanel] = useState(false);

  // Load existing analysis scoped to current authenticated user
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('cached_resume_analysis');
    }

    if (authLoading) return;

    if (!user?.id) {
      setAnalysis(null);
      setLoading(false);
      return;
    }

    const userCacheKey = `cached_resume_analysis_${user.id}`;

    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem(userCacheKey);
      if (cached) {
        try {
          setAnalysis(JSON.parse(cached));
          setLoading(false);
        } catch (e) {
          // ignore parsing error
        }
      }
    }

    async function loadAnalysis() {
      setError(null);
      try {
        const data = await getResumeAnalysis();
        if (data) {
          setAnalysis(data);
          if (typeof window !== 'undefined' && user?.id) {
            localStorage.setItem(userCacheKey, JSON.stringify(data));
          }
        }
      } catch (err: any) {
        console.error('Failed to load resume analysis:', err);
      } finally {
        setLoading(false);
      }
    }

    loadAnalysis();
  }, [user?.id, authLoading]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.docx', '.doc'].includes(ext)) {
        setError('Unsupported format. Application only accepts PDF (.pdf) and Word (.doc, .docx) files. Please upload only resume. (Kripya keval apna resume hi upload karein)');
        return;
      }
      setSelectedFile(file);
      handleUpload(file);
    }
  };

  const handleUpload = async (fileToUpload: File) => {
    setUploading(true);
    setError(null);
    try {
      const resultData = await uploadResumeFile(fileToUpload, jobDescriptionInput.trim() || undefined);
      setAnalysis(resultData);
      if (typeof window !== 'undefined' && user?.id) {
        localStorage.setItem(`cached_resume_analysis_${user.id}`, JSON.stringify(resultData));
      }
      markResumeAnalyzed();
      try {
        await refreshUser();
      } catch {}
    } catch (err: any) {
      console.error('Upload error:', err);
      const raw = err?.message || '';
      if (
        raw.includes('Sorry hum aapke baare me nahi jaan payen') ||
        raw.includes('assesment') ||
        raw.includes('assessment') ||
        raw.includes('not a valid resume') ||
        raw.includes('short or empty') ||
        raw.includes('Failed to upload')
      ) {
        setError('Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye.');
      } else {
        setError(raw || 'Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleMatchJobDescription = async () => {
    if (!jobDescriptionInput || jobDescriptionInput.trim().length < 20) {
      setJdError('Job description must be at least 20 characters long.');
      return;
    }
    setJdError(null);
    setMatchingJD(true);
    try {
      const resultData = await matchJobDescription(jobDescriptionInput.trim());
      setAnalysis(resultData);
      if (typeof window !== 'undefined' && user?.id) {
        localStorage.setItem(`cached_resume_analysis_${user.id}`, JSON.stringify(resultData));
      }
      setShowJdPanel(false);
    } catch (err: any) {
      console.error('JD Match error:', err);
      setJdError(err?.message || 'Failed to match against job description.');
    } finally {
      setMatchingJD(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Loading Resume Intelligence Analysis...</p>
      </div>
    );
  }

  const isModeA = analysis?.ats_breakdown?.scoring_mode === 'target_role' || analysis?.ats_breakdown?.scoring_mode === 'job_description';
  const isSpecificJD = analysis?.ats_breakdown?.scoring_mode === 'job_description' || analysis?.target_match?.match_source === 'job_description';
  const isGeneralMode = !isModeA;

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
            <FileText className="w-4 h-4" />
            <span>Resume Intelligence & ATS Optimization</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">Dual-Mode ATS Resume Scoring Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic, explainable scoring with transparent factor weights, candidate achievement scores, and contributions.
          </p>
        </div>
        {analysis && (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setShowJdPanel(!showJdPanel)}
              className="px-3.5 py-2.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-xs font-semibold transition-all flex items-center space-x-1.5"
            >
              <Briefcase className="w-3.5 h-3.5" />
              <span>{showJdPanel ? 'Close JD Match' : 'Match Specific JD'}</span>
            </button>
            <label className="px-3.5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-all flex items-center space-x-1.5 shrink-0">
              <RefreshCw className="w-3.5 h-3.5 text-purple-400" />
              <span>Re-upload</span>
              <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={handleFileChange} />
            </label>
          </div>
        )}
      </div>

      {/* Optional Job Description Matching Panel */}
      {showJdPanel && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-500/40 shadow-xl space-y-4 animate-in fade-in duration-300">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="inline-flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                <Target className="w-4 h-4" />
                <span>Mode A: Specific Job Vacancy Matcher</span>
              </div>
              <h3 className="text-base font-bold text-white">Paste Job Description for Specific Vacancy</h3>
              <p className="text-xs text-slate-300">
                Paste the employer job description below to calculate exact vacancy-specific skill match, keyword relevance, and eligibility.
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <textarea
              value={jobDescriptionInput}
              onChange={(e) => setJobDescriptionInput(e.target.value)}
              placeholder="Paste job description text here (requirements, responsibilities, qualifications)..."
              rows={6}
              className="w-full p-3.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-indigo-500 text-slate-100 text-xs leading-relaxed placeholder:text-slate-500 focus:outline-none transition-all"
            />
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Min 20 characters (Recommended: include Responsibilities & Qualifications)</span>
              <span>{jobDescriptionInput.length} characters</span>
            </div>
          </div>

          {jdError && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{jdError}</span>
            </div>
          )}

          <div className="flex items-center justify-end space-x-3 pt-1">
            <button
              onClick={() => setShowJdPanel(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              onClick={handleMatchJobDescription}
              disabled={matchingJD || jobDescriptionInput.trim().length < 20}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-indigo-600/30 transition"
            >
              {matchingJD ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating Vacancy Match...</span>
                </>
              ) : (
                <>
                  <Target className="w-3.5 h-3.5" />
                  <span>Analyze Against Job Description</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="p-6 rounded-2xl bg-amber-500/10 border-2 border-amber-500/40 text-amber-200 space-y-4 shadow-xl animate-in fade-in duration-300">
          <div className="flex items-start space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 shrink-0">
              <AlertTriangle className="w-6 h-6 animate-pulse" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base sm:text-lg font-bold text-white">
                {error}
              </h3>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                Aapke uploaded resume se hum aapke baare me aur aapki skills ke baare me nahi jaan paye hain. Application ko analyze karne ke liye please Career Discovery Assessment dijiye.
              </p>
            </div>
          </div>
          <div className="pt-1 flex flex-col sm:flex-row items-center gap-3">
            <Link
              href="/assessment"
              className="inline-flex items-center justify-center space-x-2 w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs sm:text-sm shadow-md transition"
            >
              <Compass className="w-4 h-4" />
              <span>Career Assessment Dijiye (Take Assessment Now)</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <label className="inline-flex items-center justify-center space-x-2 w-full sm:w-auto px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs cursor-pointer border border-slate-700 transition">
              <RefreshCw className="w-4 h-4 text-purple-400" />
              <span>Try Another Resume (.pdf/.docx)</span>
              <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={handleFileChange} />
            </label>
          </div>
        </div>
      )}

      {/* Upload Zone (Shown if no analysis exists or during upload) */}
      {(!analysis || uploading) && (
        <div className="p-10 rounded-2xl bg-slate-900/40 border-2 border-dashed border-slate-800 hover:border-indigo-500/50 transition-all text-center flex flex-col items-center justify-center min-h-[300px]">
          {uploading ? (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
              <div>
                <h3 className="text-lg font-bold text-white mb-1">Verifying Document & Computing Deterministic ATS Scores...</h3>
                <p className="text-xs text-slate-400">Auditing document authenticity, extracting skills verbatim, and calculating dual-mode factor weights</p>
              </div>
            </div>
          ) : (
            <>
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Upload className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-slate-100 mb-1">Upload Resume (PDF, DOC, or DOCX)</h3>
              <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
                Upload your resume in .pdf or .doc/.docx format. Our system computes transparent ATS scores (Mode A when a target career is chosen, or Mode B general quality score). Max size 10MB.
              </p>
              <label className="px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm cursor-pointer shadow-lg shadow-indigo-500/25 transition-all flex items-center space-x-2">
                <FileText className="w-5 h-5" />
                <span>Select PDF or Word Document (.pdf, .doc, .docx)</span>
                <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={handleFileChange} />
              </label>
            </>
          )}
        </div>
      )}

      {/* Analysis Output View */}
      {analysis && !uploading && (
        <div className="space-y-8">

          {/* Active Scoring Mode Indicator Banner */}
          <div className={`p-5 rounded-2xl border shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4 ${
            isModeA 
              ? 'bg-gradient-to-r from-indigo-950/70 via-slate-900 to-purple-950/70 border-indigo-500/40' 
              : 'bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border-amber-500/30'
          }`}>
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                  isSpecificJD 
                    ? 'bg-purple-500/20 text-purple-300 border-purple-500/30'
                    : isModeA
                    ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                }`}>
                  {isSpecificJD ? 'Mode A: Specific Job Vacancy Match' : isModeA ? 'Mode A: Career Catalog Match' : 'Mode B: General Resume Quality'}
                </span>
                <span className="text-xs text-slate-400">
                  Target Context: <strong className="text-white">{analysis.target_match?.target_career_name || 'None'}</strong>
                </span>
              </div>
              <h2 className="text-lg font-bold text-white">
                {analysis.ats_breakdown?.mode_label || (isModeA ? 'Role-Specific ATS Match Evaluation' : 'General Resume Quality & ATS Readiness')}
              </h2>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                {isSpecificJD ? (
                  'Scoring evaluated directly against pasted job vacancy requirements. Not a generic catalog estimation.'
                ) : isModeA ? (
                  `Scoring evaluated against ${analysis.target_match.target_career_name} industry competencies from Career Catalog. Paste a specific job description above for exact vacancy matching.`
                ) : (
                  'No target career selected. This score measures general formatting, section completeness, skill documentation, and content clarity without assuming a target role.'
                )}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {isGeneralMode && (
                <Link
                  href="/assessment"
                  className="px-4 py-2 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-200 text-xs font-semibold flex items-center space-x-1.5 transition"
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>Choose Target Career →</span>
                </Link>
              )}
              <button
                onClick={() => setShowJdPanel(true)}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm"
              >
                <Briefcase className="w-3.5 h-3.5" />
                <span>Match Specific JD</span>
              </button>
            </div>
          </div>

          {/* Fresher Mode Badge if active */}
          {analysis.ats_breakdown?.is_fresher_mode && (
            <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs flex items-center space-x-2.5">
              <GraduationCap className="w-4 h-4 shrink-0 text-blue-400" />
              <span>
                <strong>Fresher / Student Profile Detected:</strong> Practical projects and coursework are evaluated as practical evidence without penalizing for lack of formal corporate tenure.
              </span>
            </div>
          )}

          {/* Candidate Profile Card */}
          <section className="space-y-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h2 className="text-xl font-extrabold text-white tracking-tight">
                Candidate Profile (Extracted from Resume)
              </h2>
            </div>
            <CandidateProfileCard resumeData={analysis} />
          </section>

          {/* Top Metric Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall ATS Score</span>
              <div className="text-4xl font-extrabold text-indigo-400">
                {analysis.ats_score}<span className="text-sm text-slate-500 font-normal">/100</span>
              </div>
              <p className="text-xs text-slate-400">
                Sum of {analysis.ats_breakdown?.factors?.length || 6} weighted factor contributions
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {isModeA ? 'Role Skill Match' : 'General Evaluation Mode'}
              </span>
              <div className={`text-4xl font-extrabold ${isModeA ? 'text-emerald-400' : 'text-slate-400'}`}>
                {isModeA ? `${analysis.target_match.match_percentage}%` : 'N/A'}
              </div>
              <p className="text-xs text-slate-400">
                {isModeA ? `Target: ${analysis.target_match.target_career_name}` : 'No target role specified'}
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Formatting & ATS Risks</span>
              <div className="text-4xl font-extrabold text-amber-400">
                {analysis.formatting_risk_flags.length}
              </div>
              <p className="text-xs text-slate-400">Actionable risk points detected</p>
            </div>
          </div>

          {/* Transparent Mathematical Scoring Factors Breakdown Table */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-indigo-400" />
                  <span>Configured Scoring Breakdown & Mathematical Contribution</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Formula: Weighted Contribution = Candidate Factor Score × Factor Weight / 100. Total Score = Sum of Contributions.
                </p>
              </div>
              <span className="px-2.5 py-1 rounded bg-slate-800 text-[11px] font-semibold text-slate-300 self-start sm:self-auto">
                Model: {isModeA ? 'Mode A (Target Role Match)' : 'Mode B (General Resume Quality)'}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/70 text-[11px] uppercase font-bold text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-3">Evaluation Factor</th>
                    <th className="py-3 px-3 text-center">Configured Weight</th>
                    <th className="py-3 px-3 text-center">Candidate Score</th>
                    <th className="py-3 px-3 text-center">Contribution</th>
                    <th className="py-3 px-3">Evidence & Gaps</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(analysis.ats_breakdown?.factors && analysis.ats_breakdown.factors.length > 0) ? (
                    analysis.ats_breakdown.factors.map((factor: ScoringFactorItem, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3.5 px-3 align-top">
                          <div className="font-bold text-white text-xs">{factor.factor_name}</div>
                          <div className="text-[11px] text-slate-400 max-w-xs mt-0.5">{factor.description}</div>
                        </td>
                        <td className="py-3.5 px-3 text-center font-bold text-indigo-400 align-top">
                          {factor.weight}%
                        </td>
                        <td className="py-3.5 px-3 text-center align-top">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                            factor.factor_score >= 70 ? 'bg-emerald-500/20 text-emerald-300' :
                            factor.factor_score >= 40 ? 'bg-amber-500/20 text-amber-300' :
                            'bg-red-500/20 text-red-300'
                          }`}>
                            {factor.factor_score}/100
                          </span>
                        </td>
                        <td className="py-3.5 px-3 text-center font-bold text-white align-top">
                          +{factor.weighted_contribution.toFixed(1)} pts
                        </td>
                        <td className="py-3.5 px-3 align-top space-y-1.5 max-w-md">
                          {factor.strengths && factor.strengths.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {factor.strengths.map((s, sIdx) => (
                                <span key={sIdx} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-medium">
                                  ✓ {s}
                                </span>
                              ))}
                            </div>
                          )}
                          {factor.missing_evidence && factor.missing_evidence.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {factor.missing_evidence.map((m, mIdx) => (
                                <span key={mIdx} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 font-medium">
                                  ⚠ {m}
                                </span>
                              ))}
                            </div>
                          )}
                          {factor.status === 'unverifiable' && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 italic">
                              Information not verifiable from resume
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-4 text-center text-slate-400">
                        Detailed factors calculated with overall score of {analysis.ats_score}%.
                      </td>
                    </tr>
                  )}
                </tbody>
                <tfoot className="bg-slate-950 font-bold text-xs border-t-2 border-slate-700 text-white">
                  <tr>
                    <td className="py-3 px-3">Total Configured Weights</td>
                    <td className="py-3 px-3 text-center text-indigo-400">100%</td>
                    <td className="py-3 px-3 text-center text-slate-400">-</td>
                    <td className="py-3 px-3 text-center text-emerald-400">
                      {analysis.ats_score}.0 / 100
                    </td>
                    <td className="py-3 px-3 text-[11px] text-slate-400 font-normal">
                      Final ATS Score equals sum of factor contributions
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Missing Data Notes if any */}
            {analysis.ats_breakdown?.missing_data_notes && analysis.ats_breakdown.missing_data_notes.length > 0 && (
              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <span className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Missing Data & Normalization Policy:</span>
                <ul className="list-disc list-inside space-y-0.5">
                  {analysis.ats_breakdown.missing_data_notes.map((note, nIdx) => (
                    <li key={nIdx}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Mandatory Eligibility & Qualifications Section (Mode A) */}
          {analysis.ats_breakdown?.eligibility_criteria && analysis.ats_breakdown.eligibility_criteria.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center space-x-2">
                <Award className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Mandatory Eligibility & Qualifications Audit</h3>
              </div>
              <p className="text-xs text-slate-400">
                Evaluation of explicit candidate eligibility requirements. Items that cannot be established from the resume are marked &quot;Unknown&quot; rather than assumed failed.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                {analysis.ats_breakdown.eligibility_criteria.map((item: EligibilityItem, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{item.criterion}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.status === 'MET' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        item.status === 'NOT_MET' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                        'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}>
                        {item.status === 'MET' ? '✓ MET' : item.status === 'NOT_MET' ? '✗ NOT MET' : '? UNKNOWN'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{item.details}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills Breakdown: Required vs Preferred Skills */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">
                  {isModeA ? `Role Skill Match: ${analysis.target_match.target_career_name}` : 'Documented Resume Skills'}
                </h3>
              </div>
              {isModeA && (
                <span className="text-xs font-bold text-emerald-400">
                  {analysis.target_match.matching_skills.length} Required Skills Matched
                </span>
              )}
            </div>

            {/* Required Skills Section */}
            <div className="space-y-3">
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  {isModeA ? 'Required Skills Matched:' : 'Extracted Technical Skills:'}
                </span>
                <div className="flex flex-wrap gap-1.5 pt-1.5">
                  {analysis.target_match.matching_skills.length > 0 ? (
                    analysis.target_match.matching_skills.map((sk, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 font-semibold flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{sk}</span>
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">
                      {isModeA ? 'No required target skills found in resume.' : 'No technical skills identified.'}
                    </span>
                  )}
                </div>
              </div>

              {isModeA && (
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Missing Required Skills:</span>
                    <Link href="/skills" className="text-[11px] text-amber-400/80 hover:text-amber-300 font-semibold transition-colors">
                      Skill Intelligence →
                    </Link>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-2">
                    {analysis.target_match.missing_skills.length > 0 ? (
                      analysis.target_match.missing_skills.map((gap, idx) => (
                        <SkillActionBadge key={idx} skillName={gap} />
                      ))
                    ) : (
                      <span className="text-xs text-slate-400">All required target skills detected!</span>
                    )}
                  </div>
                </div>
              )}

              {/* Preferred / Desired Skills Section */}
              {isModeA && (
                <div className="pt-2 border-t border-slate-800/80 space-y-2">
                  <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                    Preferred & Bonus Qualifications:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {(analysis.target_match.preferred_skills_matching || []).map((sk, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/20 text-[11px] text-purple-300 font-medium flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3 text-purple-400" />
                        <span>{sk} (Preferred - Matched)</span>
                      </span>
                    ))}
                    {(analysis.target_match.preferred_skills_missing || []).map((sk, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-800/60 border border-slate-700 text-[11px] text-slate-400 font-medium">
                        ○ {sk} (Preferred - Missing)
                      </span>
                    ))}
                    {(!analysis.target_match.preferred_skills_matching?.length && !analysis.target_match.preferred_skills_missing?.length) && (
                      <span className="text-xs text-slate-400">No explicit preferred skills listed.</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Formatting & Content Risk Flags */}
          {analysis.formatting_risk_flags.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                <span>Detected ATS & Formatting Risks</span>
              </h3>
              <div className="space-y-2">
                {analysis.formatting_risk_flags.map((risk, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{risk}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bullet Improvement Suggestions */}
          {analysis.improvement_suggestions.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span>AI Bullet Point Improvement Suggestions</span>
              </h3>
              <p className="text-xs text-slate-400">
                Actionable enhancements grounded strictly in accomplishments and missing evidence from your resume.
              </p>
              <div className="space-y-4">
                {analysis.improvement_suggestions.map((imp, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="text-xs text-slate-400 line-through">
                      <strong className="text-slate-500">Original:</strong> {imp.original_text}
                    </div>
                    <div className="text-xs font-semibold text-emerald-400">
                      <strong className="text-slate-300">Suggested Rewrite:</strong> {imp.improved_text}
                    </div>
                    <p className="text-[11px] text-slate-400 italic pt-1 border-t border-slate-800/60">
                      Rationale: {imp.explanation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}