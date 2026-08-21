'use client';

import { useEffect, useState } from 'react';
import {
  TrendingUp, ShieldCheck, Award, FileText, Mic, MapPin, Briefcase,
  Zap, AlertTriangle, CheckCircle, ArrowRight, Sparkles, Star,
  BarChart2, Target, Code, Compass, Flag, Send, ChevronUp, ChevronDown
} from 'lucide-react';
import Link from 'next/link';
import {
  getDigitalTwinProfile,
  getReadinessHistory,
  getWeeklyReport,
  getAchievements,
} from '@/lib/digital-twin-api';
import type {
  CareerDigitalTwinData,
  ReadinessSnapshotData,
  WeeklyCareerReportData,
  UserAchievementData,
} from '@/lib/types';

// Icon map for achievement keys
const ICON_MAP: Record<string, React.ElementType> = {
  'file-text': FileText,
  'shield-check': ShieldCheck,
  'award': Award,
  'zap': Zap,
  'map': MapPin,
  'check-circle': CheckCircle,
  'flag': Flag,
  'code': Code,
  'mic': Mic,
  'trending-up': TrendingUp,
  'bar-chart-2': BarChart2,
  'send': Send,
  'star': Star,
  'compass': Compass,
};

// Sub-score labels and colors
const SUB_SCORE_CONFIG = [
  { key: 'skill_readiness', label: 'Skill Readiness', icon: Award, color: 'indigo', weight: '30%' },
  { key: 'resume_readiness', label: 'Resume & ATS', icon: FileText, color: 'purple', weight: '20%' },
  { key: 'interview_readiness', label: 'Interview Readiness', icon: Mic, color: 'pink', weight: '20%' },
  { key: 'roadmap_progress', label: 'Roadmap Progress', icon: MapPin, color: 'blue', weight: '15%' },
  { key: 'job_match_readiness', label: 'Job Match', icon: Briefcase, color: 'emerald', weight: '10%' },
  { key: 'portfolio_readiness', label: 'Portfolio', icon: Code, color: 'amber', weight: '5%' },
] as const;

const COLOR_CLASSES: Record<string, { bar: string; badge: string; text: string }> = {
  indigo: { bar: 'bg-indigo-500', badge: 'bg-indigo-500/20 text-indigo-400', text: 'text-indigo-400' },
  purple: { bar: 'bg-purple-500', badge: 'bg-purple-500/20 text-purple-400', text: 'text-purple-400' },
  pink: { bar: 'bg-pink-500', badge: 'bg-pink-500/20 text-pink-400', text: 'text-pink-400' },
  blue: { bar: 'bg-blue-500', badge: 'bg-blue-500/20 text-blue-400', text: 'text-blue-400' },
  emerald: { bar: 'bg-emerald-500', badge: 'bg-emerald-500/20 text-emerald-400', text: 'text-emerald-400' },
  amber: { bar: 'bg-amber-500', badge: 'bg-amber-500/20 text-amber-400', text: 'text-amber-400' },
};

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const circumference = 2 * Math.PI * 52;
  const strokeDash = (score / 100) * circumference;
  const color = score >= 75 ? '#10b981' : score >= 50 ? '#6366f1' : score >= 25 ? '#f59e0b' : '#ef4444';

  return (
    <div className="flex flex-col items-center space-y-3">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="52" fill="none" stroke="#1e293b" strokeWidth="12" />
        <circle
          cx="70" cy="70" r="52"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${strokeDash} ${circumference}`}
          strokeDashoffset={circumference / 4}
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
        <text x="70" y="66" textAnchor="middle" fill="white" fontSize="28" fontWeight="800">{score}</text>
        <text x="70" y="84" textAnchor="middle" fill="#94a3b8" fontSize="10">/100</text>
      </svg>
      <span className="text-sm font-semibold text-slate-300">{label}</span>
    </div>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span className="text-slate-500 text-xs">No change</span>;
  const Icon = delta > 0 ? ChevronUp : ChevronDown;
  const cls = delta > 0 ? 'text-emerald-400' : 'text-red-400';
  return (
    <span className={`flex items-center text-xs font-semibold ${cls}`}>
      <Icon className="w-3 h-3" />{Math.abs(delta)} pts
    </span>
  );
}

function MiniHistoryChart({ history, dataKey }: { history: ReadinessSnapshotData[]; dataKey: keyof ReadinessSnapshotData }) {
  if (history.length < 2) {
    return <div className="text-xs text-slate-600 italic">Not enough history yet</div>;
  }
  const max = 100;
  const h = 40;
  const w = 180;
  const pts = history.slice(-14);
  const step = w / (pts.length - 1);
  const toY = (v: number) => h - (v / max) * h;
  const points = pts.map((s, i) => `${i * step},${toY(Number(s[dataKey]))}`).join(' ');

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline fill="none" stroke="#6366f1" strokeWidth="2" points={points} />
      {pts.map((s, i) => (
        <circle key={i} cx={i * step} cy={toY(Number(s[dataKey]))} r="2.5" fill="#818cf8" />
      ))}
    </svg>
  );
}

export default function ProgressPage() {
  const [twin, setTwin] = useState<CareerDigitalTwinData | null>(null);
  const [history, setHistory] = useState<ReadinessSnapshotData[]>([]);
  const [report, setReport] = useState<WeeklyCareerReportData | null>(null);
  const [achievements, setAchievements] = useState<UserAchievementData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [twinData, histData, reportData, achData] = await Promise.allSettled([
          getDigitalTwinProfile(),
          getReadinessHistory(),
          getWeeklyReport(),
          getAchievements(),
        ]);

        if (twinData.status === 'fulfilled') setTwin(twinData.value);
        if (histData.status === 'fulfilled') setHistory(histData.value);
        if (reportData.status === 'fulfilled') setReport(reportData.value);
        if (achData.status === 'fulfilled') setAchievements(achData.value);
      } catch (e) {
        setError('Failed to load progress data.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Computing your Career Digital Twin...</p>
        </div>
      </div>
    );
  }

  const subScores = twin?.sub_scores;
  const overallScore = twin?.overall_readiness_score ?? 0;
  const label = twin?.readiness_label ?? 'Not Started';
  const nextAction = twin?.next_action;
  const gaps = twin?.priority_gaps ?? [];
  const strengths = twin?.top_strengths ?? [];
  const criticalSkills = twin?.critical_missing_skills ?? [];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-500/20">
        <div className="flex items-center space-x-3 mb-2">
          <Sparkles className="w-6 h-6 text-indigo-400" />
          <h1 className="text-2xl font-extrabold text-white">Progress & Career Readiness</h1>
        </div>
        <p className="text-sm text-slate-400">
          Live Career Digital Twin — computed from your real skills, resume, interviews, roadmap, and job data.
          {twin?.last_computed_at && (
            <span className="ml-2 text-indigo-400/60">
              Last updated: {new Date(twin.last_computed_at).toLocaleTimeString()}
            </span>
          )}
        </p>
      </div>

      {/* Main Score + Sub-scores */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gauge */}
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center space-y-4">
          <ScoreGauge score={overallScore} label="Career Readiness" />
          <div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
              overallScore >= 75 ? 'bg-emerald-500/20 text-emerald-400' :
              overallScore >= 50 ? 'bg-indigo-500/20 text-indigo-400' :
              overallScore >= 25 ? 'bg-amber-500/20 text-amber-400' :
              'bg-red-500/20 text-red-400'
            }`}>{label}</span>
          </div>
          {twin?.target_career && (
            <div className="flex items-center space-x-2 text-sm text-slate-400">
              <Target className="w-4 h-4 text-indigo-400" />
              <span>{twin.target_career}</span>
            </div>
          )}
          {twin?.primary_archetype && (
            <p className="text-xs text-slate-500">Archetype: {twin.primary_archetype}</p>
          )}
        </div>

        {/* Sub-scores */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-base font-bold text-white mb-5">Readiness Breakdown</h3>
          <div className="space-y-4">
            {SUB_SCORE_CONFIG.map(({ key, label, icon: Icon, color, weight }) => {
              const val = subScores ? subScores[key as keyof typeof subScores] : 0;
              const cc = COLOR_CLASSES[color];
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center space-x-2">
                      <Icon className={`w-4 h-4 ${cc.text}`} />
                      <span className="text-sm text-slate-300 font-medium">{label}</span>
                      <span className="text-[10px] text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded">{weight}</span>
                    </div>
                    <span className="text-sm font-bold text-white">{val}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className={`${cc.bar} h-full rounded-full transition-all duration-700`}
                      style={{ width: `${val}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-slate-600 mt-4">
            Formula: Skill×30% + Resume×20% + Interview×20% + Roadmap×15% + Job Match×10% + Portfolio×5%
          </p>
        </div>
      </div>

      {/* Trend Chart + Weekly Report */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* History trend */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span>Overall Score Trend (Last 14 days)</span>
            </h3>
            {history.length > 0 && (
              <span className="text-xs text-slate-500">{history.length} snapshots</span>
            )}
          </div>
          {history.length >= 2 ? (
            <div className="space-y-4">
              <MiniHistoryChart history={history} dataKey="overall" />
              <div className="grid grid-cols-3 gap-3 mt-4">
                {(['skill', 'resume', 'interview'] as const).map((k) => (
                  <div key={k} className="text-center">
                    <p className="text-xs text-slate-500 mb-1 capitalize">{k}</p>
                    <MiniHistoryChart history={history} dataKey={k} />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-24 text-slate-600 text-sm">
              <BarChart2 className="w-8 h-8 mb-2 opacity-30" />
              <p>Charts appear after 2+ days of activity.</p>
              <p className="text-xs mt-1">Use the platform daily to track your growth.</p>
            </div>
          )}
        </div>

        {/* Weekly Report */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-base font-bold text-white flex items-center space-x-2 mb-4">
            <Flag className="w-4 h-4 text-amber-400" />
            <span>Weekly Career Report</span>
          </h3>
          {report ? (
            <div className="space-y-4">
              <div className="text-xs text-slate-500 mb-3">
                {report.week_start_date} → {report.week_end_date}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <p className="text-xs text-slate-500">Interviews</p>
                  <p className="text-lg font-bold text-white">{report.activity.interviews_completed}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <p className="text-xs text-slate-500">Applications</p>
                  <p className="text-lg font-bold text-white">{report.activity.applications_submitted}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <p className="text-xs text-slate-500">Skills Verified</p>
                  <p className="text-lg font-bold text-white">{report.activity.skills_verified}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <p className="text-xs text-slate-500">Score Change</p>
                  <DeltaBadge delta={report.score_changes.overall_delta} />
                </div>
              </div>
              {report.improvements.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Improvements</p>
                  {report.improvements.slice(0, 3).map((imp, i) => (
                    <div key={i} className="flex items-start space-x-2">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                      <p className="text-xs text-slate-300">{imp}</p>
                    </div>
                  ))}
                </div>
              )}
              {report.recommended_focus && (
                <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                  <p className="text-xs text-indigo-300 font-semibold">Focus Next Week</p>
                  <p className="text-xs text-slate-300 mt-1">{report.recommended_focus}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-sm text-slate-600 italic text-center py-8">Weekly report will appear after your first active day.</div>
          )}
        </div>
      </div>

      {/* Next Best Action */}
      {nextAction && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/30 to-purple-900/30 border border-indigo-500/30">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <Zap className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white">Next Best Action</h3>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  nextAction.impact_level === 'critical' ? 'bg-red-500/20 text-red-400' :
                  nextAction.impact_level === 'high' ? 'bg-amber-500/20 text-amber-400' :
                  'bg-blue-500/20 text-blue-400'
                }`}>{nextAction.impact_level} impact</span>
              </div>
              <h4 className="text-lg font-bold text-indigo-300 mb-2">{nextAction.title}</h4>
              <p className="text-sm text-slate-400 mb-3">{nextAction.why_it_matters}</p>
              <div className="flex items-center space-x-4 text-xs text-slate-500">
                <span>🎯 {nextAction.related_goal}</span>
                <span>📈 {nextAction.expected_impact}</span>
              </div>
            </div>
            <Link
              href={nextAction.action_link}
              className="ml-6 shrink-0 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm flex items-center space-x-2 transition-colors"
            >
              <span>Start</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Strengths + Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strengths */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Top Strengths</span>
          </h3>
          {strengths.length > 0 ? (
            <div className="space-y-3">
              {strengths.slice(0, 5).map((s, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-semibold text-slate-200">{s.name}</span>
                      {s.verified && (
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                    </div>
                    <p className="text-xs text-slate-500">{s.category} · {s.level}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-emerald-400">{s.proficiency}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-600 italic text-center py-6">
              <Award className="w-8 h-8 mx-auto mb-2 opacity-30" />
              Complete the skill assessment to see your strengths.
            </div>
          )}
        </div>

        {/* Priority Gaps */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Priority Gaps</span>
          </h3>
          {gaps.length > 0 ? (
            <div className="space-y-3">
              {gaps.slice(0, 5).map((g, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-slate-200">{g.name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      g.priority === 'Critical' ? 'bg-red-500/20 text-red-400' :
                      g.priority === 'High' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>{g.priority}</span>
                  </div>
                  <p className="text-xs text-slate-500">{g.area} · {g.current_level} → {g.required_level}</p>
                  <p className="text-xs text-slate-400 mt-1">{g.reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-600 italic text-center py-6">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
              No critical gaps found yet. Add skills to see gap analysis.
            </div>
          )}
        </div>
      </div>

      {/* Critical Missing Skills */}
      {criticalSkills.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Critical Missing Skills for Target Role</h3>
          <div className="flex flex-wrap gap-2">
            {criticalSkills.map((skill, i) => (
              <span key={i} className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-semibold">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Achievements */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
          <Star className="w-4 h-4 text-amber-400" />
          <span>Earned Achievements</span>
          <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold">{achievements.length}</span>
        </h3>
        {achievements.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {achievements.map((ach) => {
              const Icon = ICON_MAP[ach.icon] || Award;
              return (
                <div
                  key={ach.achievement_key}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/30 transition-colors"
                  title={ach.evidence_description}
                >
                  <Icon className="w-6 h-6 text-amber-400 mb-2" />
                  <p className="text-sm font-semibold text-slate-200 leading-tight">{ach.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{ach.category}</p>
                  <p className="text-[10px] text-slate-600 mt-1">
                    {ach.earned_at ? new Date(ach.earned_at).toLocaleDateString() : ''}
                  </p>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-sm text-slate-600 italic text-center py-8">
            <Star className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p>No achievements yet. Start using the platform to earn your first badge!</p>
            <p className="text-xs mt-1 text-slate-700">Upload resume, complete a skill assessment, or start a mock interview.</p>
          </div>
        )}
      </div>
    </div>
  );
}
