'use client';

import { useEffect, useState } from 'react';
import { 
  Briefcase, 
  Building, 
  CheckCircle2, 
  ArrowUpRight, 
  Search, 
  Bookmark, 
  BookmarkCheck, 
  Sparkles, 
  TrendingUp, 
  Clock, 
  AlertTriangle, 
  Layers, 
  Plus, 
  Filter, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  Trash2,
  Calendar,
  FileText,
  MapPin,
  Check,
  X
} from 'lucide-react';
import { 
  searchJobs, 
  getRecommendedJobs, 
  getSavedJobs, 
  saveJob, 
  deleteSavedJob, 
  getUserApplications, 
  createJobApplication, 
  updateJobApplication, 
  deleteJobApplication, 
  getApplicationHistory 
} from '@/lib/api-client';
import { 
  JobData, 
  JobMatchAnalysis, 
  SavedJobData, 
  JobApplicationData, 
  ApplicationHistoryItem 
} from '@/lib/types';

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<'search' | 'tracker'>('search');
  const [recommendedMatches, setRecommendedMatches] = useState<JobMatchAnalysis[]>([]);
  const [allJobs, setAllJobs] = useState<JobData[]>([]);
  const [savedJobs, setSavedJobs] = useState<SavedJobData[]>([]);
  const [applications, setApplications] = useState<JobApplicationData[]>([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [selectedMatchMode, setSelectedMatchMode] = useState<'recommended' | 'all'>('recommended');
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  // Application Modal states
  const [selectedJobForApp, setSelectedJobForApp] = useState<JobData | null>(null);
  const [appStatus, setAppStatus] = useState('Applied');
  const [appNotes, setAppNotes] = useState('');
  const [selectedHistoryAppId, setSelectedHistoryAppId] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<ApplicationHistoryItem[]>([]);

  useEffect(() => {
    loadJobsData();
  }, []);

  async function loadJobsData() {
    setLoading(true);
    try {
      const [recData, jobsData, savedData, appData] = await Promise.all([
        getRecommendedJobs(),
        searchJobs(),
        getSavedJobs(),
        getUserApplications()
      ]);
      setRecommendedMatches(recData);
      setAllJobs(jobsData);
      setSavedJobs(savedData);
      setApplications(appData);
    } catch (err) {
      console.error('Failed to load jobs data:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e?: React.FormEvent) {
    if (e) e.preventDefault();
    try {
      const jobs = await searchJobs({
        query: searchQuery || undefined,
        location: locationQuery || undefined,
        remote_only: remoteOnly || undefined
      });
      setAllJobs(jobs);
    } catch (err) {
      console.error('Search error:', err);
    }
  }

  async function handleToggleSave(job: JobData) {
    const isSaved = savedJobs.some((s) => s.job_id === job.id);
    try {
      if (isSaved) {
        await deleteSavedJob(job.id);
        setSavedJobs(savedJobs.filter((s) => s.job_id !== job.id));
      } else {
        const newSaved = await saveJob(job.id);
        setSavedJobs([...savedJobs, newSaved]);
      }
    } catch (err) {
      console.error('Failed to toggle save:', err);
    }
  }

  async function handleCreateApplication(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedJobForApp) return;
    try {
      const newApp = await createJobApplication({
        job_id: selectedJobForApp.id,
        status: appStatus,
        notes: appNotes
      });
      setApplications([...applications, newApp]);
      setSelectedJobForApp(null);
      setAppNotes('');
    } catch (err) {
      console.error('Failed to create application:', err);
    }
  }

  async function handleStatusChange(appId: string, newStatus: string) {
    try {
      const updated = await updateJobApplication(appId, { status: newStatus });
      setApplications(applications.map((a) => (a.id === appId ? updated : a)));
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  }

  async function handleViewHistory(appId: string) {
    setSelectedHistoryAppId(appId);
    try {
      const history = await getApplicationHistory(appId);
      setHistoryItems(history);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  }

  const KANBAN_STATUSES = ['Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn'];

  function getReadinessBadge(status: string) {
    switch (status) {
      case 'READY':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">READY</span>;
      case 'NEARLY READY':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">NEARLY READY</span>;
      case 'NEEDS SKILL DEVELOPMENT':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">NEEDS SKILLS</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">LOW MATCH</span>;
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-3">
          <Sparkles className="w-8 h-8 text-indigo-400 animate-spin" />
          <p className="text-slate-400 text-sm font-medium">Scanning career catalog & evaluating job matches...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Job Intelligence & Application Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Personalized job matching evaluated against your Target Career, Resume ATS, verified skills, and roadmap gaps.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1 rounded-xl border border-slate-800 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === 'search' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Job Recommendations & Search
          </button>
          <button
            onClick={() => setActiveTab('tracker')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === 'tracker' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Application Tracker ({applications.length})
          </button>
        </div>
      </div>

      {/* TAB 1: JOB RECOMMENDATIONS & SEARCH */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {/* Search Controls */}
          <form onSubmit={handleSearch} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  placeholder="Job title, skill (e.g. Python, React)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="relative">
                <MapPin className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  placeholder="Location (e.g. Remote, San Francisco)..."
                  value={locationQuery}
                  onChange={(e) => setLocationQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-between space-x-3">
                <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={remoteOnly}
                    onChange={(e) => setRemoteOnly(e.target.checked)}
                    className="accent-indigo-500 rounded"
                  />
                  <span>Remote Only</span>
                </label>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all"
                >
                  Search Jobs
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-800/80 pt-3 text-xs">
              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => setSelectedMatchMode('recommended')}
                  className={`font-semibold ${selectedMatchMode === 'recommended' ? 'text-indigo-400 underline underline-offset-4' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Top AI Match Recommendations ({recommendedMatches.length})
                </button>
                <span className="text-slate-700">|</span>
                <button
                  type="button"
                  onClick={() => setSelectedMatchMode('all')}
                  className={`font-semibold ${selectedMatchMode === 'all' ? 'text-indigo-400 underline underline-offset-4' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  All Available Postings ({allJobs.length})
                </button>
              </div>

              <span className="text-[11px] text-slate-500 italic">
                Source: Provider Catalog Architecture
              </span>
            </div>
          </form>

          {/* Job List */}
          <div className="space-y-4">
            {selectedMatchMode === 'recommended' && (
              recommendedMatches.length > 0 ? (
                recommendedMatches.map((item) => {
                  const job = item.job;
                  const isSaved = savedJobs.some((s) => s.job_id === job.id);
                  const isExpanded = expandedJobId === job.id;
                  const hasApplied = applications.some((a) => a.job_id === job.id);

                  return (
                    <div key={job.id} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                              {item.match_breakdown.overall_score}% Match
                            </span>
                            {getReadinessBadge(item.match_breakdown.readiness_status)}
                            <h3 className="text-lg font-bold text-white">{job.title}</h3>
                          </div>

                          <p className="text-xs text-slate-400 flex items-center space-x-3">
                            <span className="flex items-center space-x-1">
                              <Building className="w-3.5 h-3.5 text-slate-500" />
                              <strong className="text-slate-200">{job.company}</strong>
                            </span>
                            <span>•</span>
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-3.5 h-3.5 text-slate-500" />
                              <span>{job.location}</span>
                            </span>
                            {job.salary_min && (
                              <>
                                <span>•</span>
                                <span className="text-emerald-400 font-semibold">
                                  ${job.salary_min.toLocaleString()} - ${job.salary_max?.toLocaleString()}
                                </span>
                              </>
                            )}
                          </p>

                          {/* Skill Tags */}
                          <div className="flex flex-wrap gap-2 pt-1">
                            {item.matching_skills.map((sk) => (
                              <span key={sk} className="px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-[11px] text-emerald-300 font-medium">
                                ✓ {sk}
                              </span>
                            ))}
                            {item.missing_skills.map((sk) => (
                              <span key={sk} className="px-2.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400 font-medium">
                                ⚠ {sk}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-3 shrink-0">
                          <button
                            onClick={() => handleToggleSave(job)}
                            className="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-all"
                            title={isSaved ? "Remove Bookmark" : "Save Job"}
                          >
                            {isSaved ? <BookmarkCheck className="w-4 h-4 text-indigo-400" /> : <Bookmark className="w-4 h-4" />}
                          </button>

                          <button
                            onClick={() => setSelectedJobForApp(job)}
                            disabled={hasApplied}
                            className={`px-4 py-2.5 rounded-xl font-bold text-xs transition-all flex items-center space-x-1.5 ${hasApplied ? 'bg-slate-800 text-slate-500 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'}`}
                          >
                            <span>{hasApplied ? 'Applied' : 'Track Application'}</span>
                            <ArrowUpRight className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Expandable Match Breakdown & Roadmap Gap Connection */}
                      <div className="border-t border-slate-800/80 pt-3">
                        <button
                          onClick={() => setExpandedJobId(isExpanded ? null : job.id)}
                          className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1"
                        >
                          <span>{isExpanded ? 'Hide Match Analysis & Roadmap Connection' : 'View Full Match Breakdown & Roadmap Connections'}</span>
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>

                        {isExpanded && (
                          <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4 text-xs">
                            <p className="text-slate-300 leading-relaxed">{item.match_breakdown.readiness_explanation}</p>

                            {/* Sub-score Gauges */}
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-1">
                              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                <span className="text-[10px] text-slate-400 font-semibold uppercase">Skill Match</span>
                                <div className="text-base font-bold text-white mt-0.5">{item.match_breakdown.skill_score}%</div>
                              </div>
                              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                <span className="text-[10px] text-slate-400 font-semibold uppercase">Career Alignment</span>
                                <div className="text-base font-bold text-white mt-0.5">{item.match_breakdown.career_alignment_score}%</div>
                              </div>
                              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                <span className="text-[10px] text-slate-400 font-semibold uppercase">Resume ATS</span>
                                <div className="text-base font-bold text-white mt-0.5">{item.match_breakdown.resume_score}%</div>
                              </div>
                              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                <span className="text-[10px] text-slate-400 font-semibold uppercase">Experience</span>
                                <div className="text-base font-bold text-white mt-0.5">{item.match_breakdown.experience_score}%</div>
                              </div>
                              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                <span className="text-[10px] text-slate-400 font-semibold uppercase">Roadmap Sync</span>
                                <div className="text-base font-bold text-white mt-0.5">{item.match_breakdown.roadmap_score}%</div>
                              </div>
                            </div>

                            {/* Roadmap Gap Connection Box */}
                            {item.roadmap_connections && item.roadmap_connections.length > 0 && (
                              <div className="p-3.5 rounded-lg bg-indigo-950/40 border border-indigo-500/20 space-y-2">
                                <h4 className="text-xs font-bold text-indigo-300 flex items-center space-x-1.5">
                                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                                  <span>Skill Gap → Roadmap Connections</span>
                                </h4>
                                <div className="space-y-1.5">
                                  {item.roadmap_connections.map((rc) => (
                                    <div key={rc.skill_name} className="flex items-center justify-between text-slate-300">
                                      <span>Missing <strong className="text-amber-300">{rc.skill_name}</strong> is scheduled in <strong>{rc.roadmap_phase}</strong></span>
                                      <span className="text-emerald-400 font-bold">+{rc.match_boost_percent}% Match Boost</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Description Snippet */}
                            <div className="pt-2">
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Role Description</h4>
                              <p className="text-slate-300 leading-relaxed">{job.description}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-8 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400 text-xs">
                  No recommended jobs found matching your criteria. Try adjusting search filters.
                </div>
              )
            )}

            {selectedMatchMode === 'all' && (
              allJobs.length > 0 ? (
                allJobs.map((job) => {
                  const isSaved = savedJobs.some((s) => s.job_id === job.id);
                  const hasApplied = applications.some((a) => a.job_id === job.id);

                  return (
                    <div key={job.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                      <div className="space-y-1">
                        <h3 className="text-base font-bold text-white">{job.title}</h3>
                        <p className="text-xs text-slate-400">{job.company} • {job.location}</p>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {job.required_skills.map((s) => (
                            <span key={s} className="px-2 py-0.5 rounded bg-slate-950 text-[11px] text-slate-300">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleToggleSave(job)}
                          className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300"
                        >
                          {isSaved ? <BookmarkCheck className="w-4 h-4 text-indigo-400" /> : <Bookmark className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => setSelectedJobForApp(job)}
                          disabled={hasApplied}
                          className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs"
                        >
                          {hasApplied ? 'Applied' : 'Track'}
                        </button>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-8 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400 text-xs">
                  No jobs found.
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* TAB 2: KANBAN APPLICATION TRACKER */}
      {activeTab === 'tracker' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Briefcase className="w-5 h-5 text-indigo-400" />
              <span>Application Lifecycle Kanban Tracker</span>
            </h2>
          </div>

          {/* Kanban Columns Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-7 gap-4 overflow-x-auto pb-4">
            {KANBAN_STATUSES.map((statusName) => {
              const statusApps = applications.filter((a) => a.status === statusName);

              return (
                <div key={statusName} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col min-w-[200px] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{statusName}</span>
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-800 text-slate-400">
                      {statusApps.length}
                    </span>
                  </div>

                  <div className="space-y-3 flex-1">
                    {statusApps.map((app) => (
                      <div key={app.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs hover:border-slate-700 transition-all">
                        <div className="font-bold text-white truncate">{app.job_title}</div>
                        <div className="text-slate-400 truncate">{app.company}</div>
                        <div className="flex items-center justify-between text-[11px] text-indigo-400 font-semibold pt-1">
                          <span>{app.match_percentage}% Match</span>
                          <span className="text-slate-500">{app.applied_date || 'Recent'}</span>
                        </div>

                        {/* Quick Status Shift Select */}
                        <div className="pt-2">
                          <select
                            value={app.status}
                            onChange={(e) => handleStatusChange(app.id, e.target.value)}
                            className="w-full px-2 py-1 bg-slate-900 border border-slate-800 rounded text-[11px] text-slate-300 focus:outline-none"
                          >
                            {KANBAN_STATUSES.map((st) => (
                              <option key={st} value={st}>{st}</option>
                            ))}
                          </select>
                        </div>

                        <button
                          onClick={() => handleViewHistory(app.id)}
                          className="w-full text-center text-[10px] text-slate-500 hover:text-slate-300 pt-1"
                        >
                          View Status History
                        </button>
                      </div>
                    ))}

                    {statusApps.length === 0 && (
                      <div className="h-24 rounded-xl border border-dashed border-slate-800 flex items-center justify-center text-[11px] text-slate-600 italic">
                        Empty
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Log Application Modal */}
      {selectedJobForApp && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <form onSubmit={handleCreateApplication} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 max-w-md w-full space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Track Application</h3>
              <button type="button" onClick={() => setSelectedJobForApp(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-200">{selectedJobForApp.title}</p>
              <p className="text-xs text-slate-400">{selectedJobForApp.company} • {selectedJobForApp.location}</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Initial Status</label>
              <select
                value={appStatus}
                onChange={(e) => setAppStatus(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200"
              >
                {KANBAN_STATUSES.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Notes / Referral Details</label>
              <textarea
                value={appNotes}
                onChange={(e) => setAppNotes(e.target.value)}
                placeholder="Applied via company portal, referral from LinkedIn..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 h-20"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setSelectedJobForApp(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs"
              >
                Save Application
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Audit History Modal */}
      {selectedHistoryAppId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 max-w-md w-full space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Status History Log</h3>
              <button onClick={() => setSelectedHistoryAppId(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 text-xs max-h-60 overflow-y-auto">
              {historyItems.map((item) => (
                <div key={item.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between font-semibold text-indigo-300">
                    <span>{item.from_status ? `${item.from_status} → ${item.to_status}` : `Initialized as ${item.to_status}`}</span>
                    <span className="text-[10px] text-slate-500">{new Date(item.changed_at).toLocaleDateString()}</span>
                  </div>
                  {item.notes && <p className="text-slate-400 text-[11px]">{item.notes}</p>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
