'use client';

import { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  Loader2, 
  Target, 
  Award, 
  ShieldAlert, 
  TrendingUp, 
  RefreshCw 
} from 'lucide-react';
import { uploadResumeFile, getResumeAnalysis } from '@/lib/api-client';
import { ResumeAnalysisData } from '@/lib/types';

export default function ResumePage() {
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysisData | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load existing analysis if available
  useEffect(() => {
    async function loadAnalysis() {
      setLoading(true);
      setError(null);
      try {
        const data = await getResumeAnalysis();
        if (data) {
          setAnalysis(data);
        }
      } catch (err: any) {
        console.error('Failed to load resume analysis:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAnalysis();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      handleUpload(file);
    }
  };

  const handleUpload = async (fileToUpload: File) => {
    setUploading(true);
    setError(null);
    try {
      const resultData = await uploadResumeFile(fileToUpload);
      setAnalysis(resultData);
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload and analyze document');
    } finally {
      setUploading(false);
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

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
            <FileText className="w-4 h-4" />
            <span>Resume Intelligence & ATS Optimization</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">Resume Analysis & Target Career Match</h1>
        </div>
        {analysis && (
          <label className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-all flex items-center space-x-2 shrink-0">
            <RefreshCw className="w-4 h-4 text-purple-400" />
            <span>Re-upload Resume</span>
            <input type="file" accept=".pdf,.docx" className="hidden" onChange={handleFileChange} />
          </label>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Upload Zone (Shown if no analysis exists or during upload) */}
      {(!analysis || uploading) && (
        <div className="p-10 rounded-2xl bg-slate-900/40 border-2 border-dashed border-slate-800 hover:border-indigo-500/50 transition-all text-center flex flex-col items-center justify-center min-h-[300px]">
          {uploading ? (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
              <div>
                <h3 className="text-lg font-bold text-white mb-1">Extracting & Analyzing Resume Content...</h3>
                <p className="text-xs text-slate-400">PyMuPDF / python-docx text extraction & ATS scoring in progress</p>
              </div>
            </div>
          ) : (
            <>
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Upload className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-slate-100 mb-1">Upload Resume (PDF or DOCX)</h3>
              <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
                Upload your resume file. Text will be extracted cleanly without exposing file paths. Max size 10MB.
              </p>
              <label className="px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm cursor-pointer shadow-lg shadow-indigo-500/25 transition-all flex items-center space-x-2">
                <FileText className="w-5 h-5" />
                <span>Select PDF or DOCX Document</span>
                <input type="file" accept=".pdf,.docx" className="hidden" onChange={handleFileChange} />
              </label>
            </>
          )}
        </div>
      )}

      {/* Analysis Output View */}
      {analysis && !uploading && (
        <div className="space-y-8">
          {/* File Metadata Header */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-5 h-5 text-indigo-400" />
              <span className="text-sm font-semibold text-slate-200">{analysis.filename}</span>
            </div>
            <span className="text-xs text-slate-400">
              Evaluated against target: <strong className="text-white">{analysis.target_match.target_career_name}</strong>
            </span>
          </div>

          {/* Top Metric Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall ATS Score</span>
              <div className="text-4xl font-extrabold text-indigo-400">
                {analysis.ats_score}<span className="text-sm text-slate-500 font-normal">/100</span>
              </div>
              <p className="text-xs text-slate-400">Calculated from 5 formatting & content sub-scores</p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Role Match</span>
              <div className="text-4xl font-extrabold text-emerald-400">
                {analysis.target_match.match_percentage}%
              </div>
              <p className="text-xs text-slate-400">Target Role: {analysis.target_match.target_career_name}</p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Formatting Risk Flags</span>
              <div className="text-4xl font-extrabold text-amber-400">
                {analysis.formatting_risk_flags.length}
              </div>
              <p className="text-xs text-slate-400">Actionable risk points detected</p>
            </div>
          </div>

          {/* Sub-scores Breakdown & Target Match Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* ATS Sub-scores Breakdown */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                <span>ATS Sub-Score Breakdown</span>
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                    <span>Formatting & Section Structure</span>
                    <span className="text-indigo-400">{analysis.ats_breakdown.formatting_score}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full" style={{ width: `${analysis.ats_breakdown.formatting_score}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                    <span>Technical Skills Coverage</span>
                    <span className="text-indigo-400">{analysis.ats_breakdown.skills_score}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-purple-500 h-full" style={{ width: `${analysis.ats_breakdown.skills_score}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                    <span>Quantitative Metrics & Keywords</span>
                    <span className="text-indigo-400">{analysis.ats_breakdown.keyword_score}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-pink-500 h-full" style={{ width: `${analysis.ats_breakdown.keyword_score}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                    <span>Work Experience & Projects</span>
                    <span className="text-indigo-400">{analysis.ats_breakdown.experience_score}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full" style={{ width: `${analysis.ats_breakdown.experience_score}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Target Career Skill Match */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <Target className="w-5 h-5 text-emerald-400" />
                <span>Target Skill Overlap ({analysis.target_match.target_career_name})</span>
              </h3>

              <div className="space-y-3">
                <div>
                  <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Matching Skills Found:</span>
                  <div className="flex flex-wrap gap-1.5 pt-1.5">
                    {analysis.target_match.matching_skills.map((sk, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 font-semibold flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{sk}</span>
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Missing Target Role Skills:</span>
                  <div className="flex flex-wrap gap-1.5 pt-1.5">
                    {analysis.target_match.missing_skills.length > 0 ? (
                      analysis.target_match.missing_skills.map((gap, idx) => (
                        <span key={idx} className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 font-semibold">
                          {gap}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400">All target skills detected!</span>
                    )}
                  </div>
                </div>
              </div>
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
