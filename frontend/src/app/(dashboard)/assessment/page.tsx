'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { getLocalizedQuestion } from '@/lib/assessment-translations';
import { 
  Compass, 
  CheckCircle2, 
  ArrowRight, 
  Brain, 
  Sparkles, 
  Loader2, 
  Award, 
  Target, 
  BookOpen, 
  Briefcase, 
  X, 
  ShieldCheck, 
  RotateCcw,
  Pencil,
  GraduationCap,
  Zap,
  Star,
  Rocket,
  Flame,
  Plus,
  Check,
  ChevronRight,
  Layers,
  HelpCircle,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { 
  startAssessment,
  startAssessmentRetake,
  submitAnswer, 
  completeAssessment, 
  getAssessmentResult, 
  getCareerCatalog, 
  selectTargetCareer,
  submitDirectCareerGoal
} from '@/lib/api-client';
import { 
  AssessmentSession, 
  AssessmentResultData, 
  CareerMatch, 
  CareerRoleCatalogItem,
  DirectCareerGoalPayload,
  DirectCareerGoalResult
} from '@/lib/types';

// Curated popular career roles with their default tech skills for direct track
const POPULAR_DIRECT_ROLES = [
  {
    title: 'Frontend Developer',
    slug: 'frontend-developer',
    icon: '💻',
    category: 'Web & UI',
    skills: ['HTML', 'CSS', 'JavaScript', 'React', 'TypeScript', 'Tailwind CSS', 'Git', 'Next.js', 'REST APIs']
  },
  {
    title: 'Backend Developer',
    slug: 'backend-developer',
    icon: '⚙️',
    category: 'Engineering',
    skills: ['Python', 'Node.js', 'FastAPI', 'PostgreSQL', 'REST APIs', 'Docker', 'Git', 'Redis', 'SQL']
  },
  {
    title: 'Fullstack Developer',
    slug: 'fullstack-developer',
    icon: '🌐',
    category: 'Full-Stack',
    skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'SQL', 'Git', 'REST APIs', 'MongoDB', 'Docker']
  },
  {
    title: 'Data Analyst',
    slug: 'data-analyst',
    icon: '📊',
    category: 'Data & Analytics',
    skills: ['Python', 'SQL', 'Excel', 'PowerBI', 'Tableau', 'Pandas', 'Statistics', 'Data Visualization']
  },
  {
    title: 'Machine Learning / AI Engineer',
    slug: 'ai-ml-engineer',
    icon: '🤖',
    category: 'AI & Data',
    skills: ['Python', 'NumPy', 'Pandas', 'Machine Learning', 'Deep Learning', 'PyTorch', 'TensorFlow', 'LLMs / Prompting']
  },
  {
    title: 'Cloud & DevOps Engineer',
    slug: 'cloud-devops',
    icon: '☁️',
    category: 'Infrastructure',
    skills: ['Linux', 'Git', 'Docker', 'Kubernetes', 'AWS', 'CI/CD Pipelines', 'Terraform', 'Bash Scripting']
  },
  {
    title: 'Cyber Security Analyst',
    slug: 'cybersecurity',
    icon: '🛡️',
    category: 'Security',
    skills: ['Networking Fundamentals', 'Linux', 'Security Protocols', 'Wireshark', 'Vulnerability Assessment', 'Ethical Hacking']
  },
  {
    title: 'Mobile App Developer',
    slug: 'mobile-developer',
    icon: '📱',
    category: 'Mobile Apps',
    skills: ['Flutter', 'React Native', 'Dart', 'JavaScript', 'Mobile UI/UX', 'REST APIs', 'Git', 'State Management']
  },
  {
    title: 'UI/UX Designer',
    slug: 'ui-ux-designer',
    icon: '🎨',
    category: 'Design & Product',
    skills: ['Figma', 'User Research', 'Wireframing', 'Prototyping', 'Design Systems', 'Responsive Design', 'Usability Testing']
  },
  {
    title: 'QA / Software Tester',
    slug: 'qa-tester',
    icon: '🧪',
    category: 'Quality Assurance',
    skills: ['Manual Testing', 'Selenium', 'Python / Java', 'API Testing (Postman)', 'Test Automation', 'Jira', 'Bug Tracking']
  }
];

export default function AssessmentPage() {
  const { language, t } = useLanguage();
  const { markAssessmentCompleted } = useAuth();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pathways: 'select' (choose track), 'direct' (direct goal & skill gap), 'quiz' (discovery quiz), 'result' (view result)
  const [assessmentMode, setAssessmentMode] = useState<'select' | 'direct' | 'quiz' | 'result'>('select');

  // Direct Track State
  const [selectedRoleTitle, setSelectedRoleTitle] = useState<string>('Frontend Developer');
  const [selectedRoleSlug, setSelectedRoleSlug] = useState<string>('frontend-developer');
  const [isCustomRole, setIsCustomRole] = useState(false);
  const [customRoleInput, setCustomRoleInput] = useState('');
  const [directExperienceLevel, setDirectExperienceLevel] = useState<'scratch' | 'beginner' | 'intermediate' | 'advanced'>('scratch');
  const [knownSkillsList, setKnownSkillsList] = useState<string[]>([]);
  const [newSkillText, setNewSkillText] = useState('');
  const [directSubmitting, setDirectSubmitting] = useState(false);
  const [directResultData, setDirectResultData] = useState<DirectCareerGoalResult | null>(null);

  // Level Selection Screen State for Quiz
  const [showLevelSelect, setShowLevelSelect] = useState(false);
  const [userLevel, setUserLevel] = useState<string>('beginner');

  // Active Quiz Session State
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  // Custom Answer State for Quiz
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customAnswerText, setCustomAnswerText] = useState('');

  // Result & Profile State
  const [result, setResult] = useState<AssessmentResultData | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [targetSuccessMsg, setTargetSuccessMsg] = useState<string | null>(null);

  // Career Comparison Modal State
  const [catalog, setCatalog] = useState<CareerRoleCatalogItem[]>([]);
  const [compareMatch, setCompareMatch] = useState<CareerMatch | null>(null);

  // Load existing result or initialize active assessment session
  useEffect(() => {
    async function init() {
      setLoading(true);
      setError(null);
      try {
        // Fetch career catalog for comparison modal
        const catData = await getCareerCatalog();
        setCatalog(catData);

        // Check if user already has completed result
        const existingResult = await getAssessmentResult();
        if (existingResult && existingResult.analysis && existingResult.selected_target_career) {
          setResult(existingResult);
          setSelectedTarget(existingResult.selected_target_career || null);
          setAssessmentMode('result');
          markAssessmentCompleted();
        } else {
          // Show pathway selection screen
          setAssessmentMode('select');
        }
      } catch (err: any) {
        console.error('Initialization error:', err);
        setError(err.message || 'Failed to connect to Career Discovery API');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Sync available skills when selected career changes in Direct Track
  const currentRoleConfig = POPULAR_DIRECT_ROLES.find(r => r.slug === selectedRoleSlug) || {
    title: selectedRoleTitle,
    slug: 'custom',
    icon: '💼',
    category: 'Technology',
    skills: ['Git', 'Problem Solving', 'Data Structures', 'REST APIs', 'SQL', 'Python', 'JavaScript']
  };

  const toggleSkillSelection = (skillName: string) => {
    setKnownSkillsList(prev => 
      prev.includes(skillName) 
        ? prev.filter(s => s !== skillName)
        : [...prev, skillName]
    );
  };

  const handleAddCustomSkill = () => {
    const trimmed = newSkillText.trim();
    if (trimmed && !knownSkillsList.includes(trimmed)) {
      setKnownSkillsList(prev => [...prev, trimmed]);
      setNewSkillText('');
    }
  };

  // Submit Direct Career Goal with Known Skills & Gap Analysis
  const handleDirectGoalSubmit = async () => {
    const targetCareer = isCustomRole ? customRoleInput.trim() : selectedRoleTitle;
    if (!targetCareer) {
      setError('Please select or enter your target career role.');
      return;
    }
    setDirectSubmitting(true);
    setError(null);
    try {
      const payload: DirectCareerGoalPayload = {
        target_career: targetCareer,
        career_slug: isCustomRole ? undefined : selectedRoleSlug,
        experience_level: directExperienceLevel,
        known_skills: directExperienceLevel === 'scratch' ? [] : knownSkillsList,
        custom_notes: directExperienceLevel === 'scratch' 
          ? 'Starting completely from scratch (0 knowledge)' 
          : `Has knowledge of ${knownSkillsList.length} skills.`
      };

      const resp = await submitDirectCareerGoal(payload);
      setDirectResultData(resp);
      setSelectedTarget(resp.target_career);
      markAssessmentCompleted();
      
      // Update result state so other assessment views reflect this
      const updatedResult = await getAssessmentResult();
      if (updatedResult) {
        setResult(updatedResult);
      }
      setTargetSuccessMsg(`Target career set to ${resp.target_career} with personalized skill gap analysis!`);
    } catch (err: any) {
      console.error('Direct goal error:', err);
      setError(err.message || 'Failed to submit direct career goal.');
    } finally {
      setDirectSubmitting(false);
    }
  };

  // Called after user picks their level for Quiz
  const handleLevelConfirm = async (level: string) => {
    setUserLevel(level);
    setShowLevelSelect(false);
    setLoading(true);
    try {
      const activeSession = await startAssessment(level);
      setSession(activeSession);
      if (activeSession.is_completed) {
        handleCompleteAssessment(activeSession.session_id);
      }
    } catch (err: any) {
      console.error('Start error:', err);
      setError(err.message || 'Failed to start assessment');
    } finally {
      setLoading(false);
    }
  };

  // Handle single question answer submission
  const handleAnswerSubmit = async () => {
    const isCustom = selectedOption === 'custom';
    if (!session || !session.current_question || submitting) return;
    if (!selectedOption) return;
    if (isCustom && !customAnswerText.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const updatedSession = await submitAnswer(
        session.session_id,
        session.current_question.id,
        selectedOption,
        isCustom ? customAnswerText.trim() : undefined
      );

      setSelectedOption(null);
      setCustomAnswerText('');
      setShowCustomInput(false);
      setSession(updatedSession);

      // If assessment reached completion, trigger AI analysis
      if (updatedSession.is_completed || !updatedSession.current_question) {
        await handleCompleteAssessment(session.session_id);
      }
    } catch (err: any) {
      console.error('Answer submission error:', err);
      setError(err.message || 'Failed to record answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Trigger Gemini AI Discovery Analysis
  const handleCompleteAssessment = async (sessionId: string) => {
    setAnalyzing(true);
    setError(null);
    try {
      await completeAssessment(sessionId);
      const latestResult = await getAssessmentResult();
      if (latestResult) {
        setResult(latestResult);
        setSelectedTarget(latestResult.selected_target_career || null);
        setAssessmentMode('result');
        markAssessmentCompleted();
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to complete AI Career Analysis.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Restart / Switch Mode
  const handleRestart = () => {
    setResult(null);
    setDirectResultData(null);
    setCompareMatch(null);
    setSelectedOption(null);
    setCustomAnswerText('');
    setShowCustomInput(false);
    setSession(null);
    setAssessmentMode('select');
  };

  // Called when retake starts after level pick
  const handleRetakeWithLevel = async (level: string) => {
    setUserLevel(level);
    setShowLevelSelect(false);
    setLoading(true);
    try {
      const newSession = await startAssessmentRetake(level);
      setSession(newSession);
      setAssessmentMode('quiz');
    } catch (err: any) {
      setError(err.message || 'Failed to restart assessment session.');
    } finally {
      setLoading(false);
    }
  };

  // Select and persist Target Career
  const handleSetTargetCareer = async (slug: string) => {
    try {
      const resp = await selectTargetCareer(slug);
      setSelectedTarget(resp.target_career);
      markAssessmentCompleted();
      setTargetSuccessMsg(`Target Career set to ${resp.target_career}`);
      setTimeout(() => setTargetSuccessMsg(null), 4000);
    } catch (err: any) {
      console.error('Target career selection error:', err);
      setError(err.message || 'Failed to save target career.');
    }
  };

  // Loading Screen
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">Loading Career Discovery Session...</p>
      </div>
    );
  }

  // ────────────────────────────────────────────────────
  // 1. DUAL PATHWAY SELECTION SCREEN (Choose Direct Track or Discovery Quiz)
  // ────────────────────────────────────────────────────
  if (assessmentMode === 'select') {
    return (
      <div className="max-w-4xl mx-auto space-y-8 pb-12 pt-4">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold uppercase tracking-widest">
            <Compass className="w-3.5 h-3.5" />
            <span>Career Assessment & Goal Setup</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white leading-tight">
            Aap Career Kis Tarah Shuru Karna Chahte Hain?
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xl mx-auto">
            Chahe aapko pehle se pata ho ki aapko kya banna hai, ya aap AI se guidance chahte hain — apna pasandida rasta chuniye:
          </p>
        </div>

        {/* Dual Pathway Choice Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* PATH A: Direct Career Track */}
          <div className="group relative p-7 rounded-3xl border border-[#E7E2D8] dark:border-[#334155] bg-white dark:bg-[#172235] hover:border-[#B89B72]/60 transition-all duration-300 shadow-sm flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-14 h-14 rounded-2xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
                  🎯
                </div>
                <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-[#B89B72]/15 text-[#17324D] dark:text-[#D9C19A] border border-[#B89B72]/30">
                  Fast Track & Skill Gap
                </span>
              </div>

              <div>
                <h3 className="text-xl font-bold text-[#17324D] dark:text-[#F1F5F9] mb-2 group-hover:text-[#B89B72] transition-colors">
                  Mujhe Mera Career Pata Hai
                </h3>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">
                  Agar aapko pata hai ki aapko kis field mein jana hai (jaise <strong>Frontend, Backend, AI/ML, Data Analyst</strong> etc.), toh direct role chuniye aur apni skills batayein.
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-[#E7E2D8] dark:border-[#334155]">
                <div className="flex items-center space-x-2 text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0" />
                  <span>Direct role selection bina lambe test ke</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0" />
                  <span><strong>&quot;Scratch / Kuch nahi aata&quot;</strong> option (0 se roadmap)</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0" />
                  <span>Instant Skill Gap Analysis & Custom Roadmap</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                setDirectResultData(null);
                setAssessmentMode('direct');
              }}
              className="mt-6 w-full py-3.5 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white font-bold text-sm flex items-center justify-center space-x-2 shadow-sm transition-all"
            >
              <span>Direct Career Set Karein</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* PATH B: Career Discovery AI Quiz */}
          <div className="group relative p-7 rounded-3xl border border-[#E7E2D8] dark:border-[#334155] bg-white dark:bg-[#172235] hover:border-[#B89B72]/60 transition-all duration-300 shadow-sm flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-14 h-14 rounded-2xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
                  🧭
                </div>
                <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-[#B89B72]/15 text-[#17324D] dark:text-[#D9C19A] border border-[#B89B72]/30">
                  AI Guided Quiz
                </span>
              </div>

              <div>
                <h3 className="text-xl font-bold text-[#17324D] dark:text-[#F1F5F9] mb-2 group-hover:text-[#B89B72] transition-colors">
                  Mujhe Career Discover Karna Hai
                </h3>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">
                  Agar aap confuse hain ki aapke dimaag, logical instincts aur interests ke hisaab se kaunsa career best fit rahega, toh hamara <strong>AI Career Discovery Quiz</strong> lijiye.
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-[#E7E2D8] dark:border-[#334155]">
                <div className="flex items-center space-x-2 text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0" />
                  <span>5 intuitive questions tailored to your level</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0" />
                  <span>Gemini AI Career Archetype calculation</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0" />
                  <span>Top 3 matched career recommendations with % match</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                setShowLevelSelect(true);
                setAssessmentMode('quiz');
              }}
              className="mt-6 w-full py-3.5 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white font-bold text-sm flex items-center justify-center space-x-2 shadow-sm transition-all"
            >
              <span>Career Discovery Quiz Start Karein</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Note at bottom */}
        {result && (
          <div className="text-center pt-2">
            <button
              onClick={() => setAssessmentMode('result')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold underline underline-offset-4"
            >
              ← Back to previous assessment profile
            </button>
          </div>
        )}
      </div>
    );
  }

  // ────────────────────────────────────────────────────
  // 2. DIRECT CAREER TRACK & SKILL GAP ANALYZER SCREEN
  // ────────────────────────────────────────────────────
  if (assessmentMode === 'direct') {
    return (
      <div className="max-w-4xl mx-auto space-y-8 pb-12 pt-2">
        {/* Top Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setAssessmentMode('select')}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            <span>← Dono Raste Dekhein (Pathways)</span>
          </button>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
            <Target className="w-3.5 h-3.5" />
            <span>Direct Goal Track</span>
          </div>
        </div>

        {/* Result view if direct analysis already completed */}
        {directResultData ? (
          <div className="space-y-6">
            <div className="p-7 rounded-3xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-indigo-950/70 border border-emerald-500/30 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      🎯 Career Goal Set Ho Gaya!
                    </span>
                    <span className="text-xs text-slate-300">
                      Level: <strong className="text-white capitalize">{directResultData.experience_level}</strong>
                    </span>
                  </div>
                  <h2 className="text-2xl font-extrabold text-white">
                    Target Role: <span className="text-emerald-400">{directResultData.target_career}</span>
                  </h2>
                </div>
                <div className="text-right bg-slate-950/60 px-4 py-2.5 rounded-2xl border border-slate-800">
                  <span className="text-xs text-slate-400 font-semibold">Current Readiness</span>
                  <div className="text-2xl font-black text-indigo-400">
                    {directResultData.readiness_score}%
                  </div>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                Aapka career goal hamare project ke saare modules ke sath sync ho chuka hai. 
                {directResultData.experience_level === 'scratch' ? (
                  <> Aapne <strong>Scratch (0 Knowledge)</strong> chuna hai, isliye aapka roadmap bilkul basic Day 1 se start hoga aur har zaroori skill ko step-by-step sikhayega.</>
                ) : (
                  <> Aapki pehchan ki gayi skills ko mark kar diya gaya hai, aur missing skills ke basis par roadmap design kiya gaya hai.</>
                )}
              </p>
            </div>

            {/* Skill Gap Analysis Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Known Skills */}
              <div className="p-6 rounded-2xl bg-slate-900/70 border border-emerald-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Skills You Already Know ({directResultData.known_skills.length})</span>
                  </h3>
                  {directResultData.known_skills.length === 0 && (
                    <span className="text-[11px] text-slate-500">Starting from 0</span>
                  )}
                </div>

                {directResultData.known_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {directResultData.known_skills.map((sk, idx) => (
                      <span key={idx} className="px-3 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs font-semibold text-emerald-300 flex items-center space-x-1.5">
                        <Check className="w-3.5 h-3.5" />
                        <span>{sk}</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 leading-relaxed">
                    Aapne scratch se shuru karna chuna hai. Roadmap aapko pehle basic fundamentals sikhayega taaki aap direct zero se confidence bana sakein.
                  </div>
                )}
              </div>

              {/* Missing Skills / Learning Gaps */}
              <div className="p-6 rounded-2xl bg-slate-900/70 border border-amber-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-2">
                    <Sparkles className="w-4 h-4" />
                    <span>Skills To Learn For This Role ({directResultData.missing_gaps.length})</span>
                  </h3>
                  <span className="text-[11px] text-amber-400/80 font-semibold">Priority Learning</span>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  {directResultData.missing_gaps.map((sk, idx) => (
                    <span key={idx} className="px-3 py-1 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs font-semibold text-amber-300 flex items-center space-x-1.5">
                      <Target className="w-3.5 h-3.5 text-amber-400" />
                      <span>{sk}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Next Action CTAs */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                🚀 Agla Kadam: Roadmap & AI Coaching
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Link
                  href="/roadmap"
                  className="p-4 rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white font-bold text-xs flex flex-col justify-between space-y-2 shadow-sm transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-base">🗺️</span>
                    <ArrowRight className="w-4 h-4 text-[#B89B72]" />
                  </div>
                  <div>
                    <div className="font-extrabold text-sm">Generate Full Roadmap</div>
                    <div className="text-[11px] text-[#D9C19A] font-normal">Week-by-week personalized learning plan</div>
                  </div>
                </Link>

                <Link
                  href="/chat"
                  className="p-4 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-700 text-white font-bold text-xs flex flex-col justify-between space-y-2 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-base">🤖</span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </div>
                  <div>
                    <div className="font-extrabold text-sm">Chat with AI Coach</div>
                    <div className="text-[11px] text-slate-400 font-normal">Get instant study tips & guidance</div>
                  </div>
                </Link>

                <Link
                  href="/resume"
                  className="p-4 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-700 text-white font-bold text-xs flex flex-col justify-between space-y-2 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-base">📄</span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </div>
                  <div>
                    <div className="font-extrabold text-sm">Scan ATS Resume</div>
                    <div className="text-[11px] text-slate-400 font-normal">Match resume against target role</div>
                  </div>
                </Link>
              </div>

              <div className="pt-2 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80">
                <span>Want to adjust your skills or role?</span>
                <button
                  onClick={() => setDirectResultData(null)}
                  className="text-indigo-400 hover:text-indigo-300 font-semibold"
                >
                  ✏️ Edit Career Goal & Skills
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Form for Direct Career & Skill Gap Input */
          <div className="space-y-8">
            {/* Header description */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <h1 className="text-2xl font-extrabold text-white">
                🎯 Direct Career Goal & Skill Gap Setup
              </h1>
              <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                Bataiye aap kis field mein apna career banana chahte hain aur aapko abhi kya kya aata hai. 
                Agar aapko abhi <strong>kuch nahi aata (scratch)</strong>, toh bhi koi chinta nahi — roadmap aapke liye 0 se start karega!
              </p>
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* STEP 1: Select Career Role */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-extrabold flex items-center justify-center border border-indigo-500/30">1</span>
                <h2 className="text-base font-bold text-white">Aapka Target Career Role Kya Hai?</h2>
              </div>

              {/* Popular Role Chips */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5">
                {POPULAR_DIRECT_ROLES.map((role) => {
                  const isSelected = !isCustomRole && selectedRoleSlug === role.slug;
                  return (
                    <button
                      key={role.slug}
                      type="button"
                      onClick={() => {
                        setSelectedRoleTitle(role.title);
                        setSelectedRoleSlug(role.slug);
                        setIsCustomRole(false);
                      }}
                      className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                        isSelected
                          ? 'bg-indigo-600/30 border-indigo-400 text-white shadow-md shadow-indigo-600/20 ring-1 ring-indigo-400'
                          : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <span className="text-lg mb-1">{role.icon}</span>
                      <span className="text-xs font-bold leading-tight">{role.title}</span>
                      <span className="text-[10px] text-slate-400 mt-1">{role.category}</span>
                    </button>
                  );
                })}
              </div>

              {/* Custom Role Input */}
              <div className="pt-2">
                <div className="flex items-center space-x-2 mb-2">
                  <input
                    type="checkbox"
                    id="customRoleCheck"
                    checked={isCustomRole}
                    onChange={(e) => setIsCustomRole(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="customRoleCheck" className="text-xs font-semibold text-slate-300 cursor-pointer">
                    Mera role upar list mein nahi hai — Custom Career Role type karein
                  </label>
                </div>

                {isCustomRole && (
                  <input
                    type="text"
                    value={customRoleInput}
                    onChange={(e) => setCustomRoleInput(e.target.value)}
                    placeholder="e.g. Blockchain Developer, Game Developer, Product Manager, Robotics Engineer..."
                    className="w-full p-3.5 rounded-xl bg-slate-950 border border-indigo-500/40 text-slate-100 text-sm focus:outline-none focus:border-indigo-400 transition-all"
                  />
                )}
              </div>
            </div>

            {/* STEP 2: Current Knowledge Level */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-extrabold flex items-center justify-center border border-indigo-500/30">2</span>
                <h2 className="text-base font-bold text-white">Aapka Current Level Kya Hai? (Aapko kitna aata hai?)</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Scratch Option */}
                <button
                  type="button"
                  onClick={() => {
                    setDirectExperienceLevel('scratch');
                    setKnownSkillsList([]);
                  }}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    directExperienceLevel === 'scratch'
                      ? 'bg-emerald-600/25 border-emerald-400 text-white shadow-md shadow-emerald-500/20 ring-1 ring-emerald-400'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-lg">🌱</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      0 Knowledge
                    </span>
                  </div>
                  <div className="font-extrabold text-sm text-white">Ekdom Scratch Se</div>
                  <div className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    Mujhe abhi kuch nahi aata. Bilkul Day 1 basic fundamentals se start karna hai.
                  </div>
                </button>

                {/* Beginner Option */}
                <button
                  type="button"
                  onClick={() => setDirectExperienceLevel('beginner')}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    directExperienceLevel === 'beginner'
                      ? 'bg-indigo-600/25 border-indigo-400 text-white shadow-md shadow-indigo-500/20 ring-1 ring-indigo-400'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-lg">⚡</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      Basics
                    </span>
                  </div>
                  <div className="font-extrabold text-sm text-white">Thoda Bahut Basics Aata Hai</div>
                  <div className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    Maine syntax ya basic concepts padhe hain. Thodi cheezein aati hain.
                  </div>
                </button>

                {/* Intermediate Option */}
                <button
                  type="button"
                  onClick={() => setDirectExperienceLevel('intermediate')}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    directExperienceLevel === 'intermediate'
                      ? 'bg-purple-600/25 border-purple-400 text-white shadow-md shadow-purple-500/20 ring-1 ring-purple-400'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-lg">🚀</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      Hands-on
                    </span>
                  </div>
                  <div className="font-extrabold text-sm text-white">Projects & Practical Experience</div>
                  <div className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    Mujhe hands-on coding aati hai. Gaps identify karke job ready hona hai.
                  </div>
                </button>
              </div>
            </div>

            {/* STEP 3: Skill Checklist (What do you know?) */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-extrabold flex items-center justify-center border border-indigo-500/30">3</span>
                  <h2 className="text-base font-bold text-white">
                    {directExperienceLevel === 'scratch' 
                      ? 'Skill Baseline'
                      : 'Aapko Inme Se Kya Kya Aata Hai? (Select Known Skills)'}
                  </h2>
                </div>
                {directExperienceLevel !== 'scratch' && (
                  <span className="text-xs text-indigo-400 font-semibold">
                    {knownSkillsList.length} skills selected
                  </span>
                )}
              </div>

              {directExperienceLevel === 'scratch' ? (
                <div className="p-5 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 flex items-start space-x-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-emerald-300">
                      🎉 Zero-Knowledge / Scratch Path Active!
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      Aapko koi bhi skill pehle se aana zaroori nahi hai. Hum aapke target role (<strong>{isCustomRole ? customRoleInput || 'Target Role' : selectedRoleTitle}</strong>) ke saare concepts aur tools ko Phase 1 (Foundation) se schedule karenge.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-xs text-slate-400">
                    Niche diye gaye skills par click karein jo aapko aati hain. Jo skills aap tick karenge, roadmap unhe repeat nahi karega aur aapka time save karega:
                  </p>

                  {/* Suggestion Chips */}
                  <div className="flex flex-wrap gap-2">
                    {currentRoleConfig.skills.map((skillName) => {
                      const isKnown = knownSkillsList.includes(skillName);
                      return (
                        <button
                          key={skillName}
                          type="button"
                          onClick={() => toggleSkillSelection(skillName)}
                          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center space-x-1.5 ${
                            isKnown
                              ? 'bg-emerald-600/30 border-emerald-400 text-emerald-300 shadow-sm shadow-emerald-500/20'
                              : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                          }`}
                        >
                          {isKnown ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Plus className="w-3.5 h-3.5 text-slate-500" />}
                          <span>{skillName}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Add Custom Skill Field */}
                  <div className="pt-2 flex items-center space-x-2">
                    <input
                      type="text"
                      value={newSkillText}
                      onChange={(e) => setNewSkillText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddCustomSkill();
                        }
                      }}
                      placeholder="Koi aur skill jo aapko aati hai? (e.g. C++, Java, Excel, Git) and press Enter..."
                      className="flex-1 p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 transition-all"
                    />
                    <button
                      type="button"
                      onClick={handleAddCustomSkill}
                      className="px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-all flex items-center space-x-1.5 shrink-0"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add Skill</span>
                    </button>
                  </div>

                  {/* Selected Skills Badges List */}
                  {knownSkillsList.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                        Currently Selected Known Skills ({knownSkillsList.length}):
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {knownSkillsList.map((sk) => (
                          <span
                            key={sk}
                            className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-1.5"
                          >
                            <span>{sk}</span>
                            <button
                              type="button"
                              onClick={() => toggleSkillSelection(sk)}
                              className="text-emerald-400/60 hover:text-emerald-300"
                            >
                              &times;
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Submit Action Button */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
              <button
                type="button"
                onClick={() => setAssessmentMode('select')}
                className="w-full sm:w-auto px-5 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white text-xs font-semibold transition-all"
              >
                ← Back
              </button>

              <button
                type="button"
                disabled={directSubmitting}
                onClick={handleDirectGoalSubmit}
                className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-[#17324D] hover:bg-[#102A43] text-white font-extrabold text-sm flex items-center justify-center space-x-2.5 shadow-sm transition-all cursor-pointer"
              >
                {directSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Analyzing Skill Gaps & Setting Goal...</span>
                  </>
                ) : (
                  <>
                    <Target className="w-5 h-5" />
                    <span>Analyze Skill Gap & Lock Career Goal 🚀</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ────────────────────────────────────────────────────
  // 3. QUIZ LEVEL SELECTION SCREEN (Beginner, Intermediate, Advanced)
  // ────────────────────────────────────────────────────
  if (showLevelSelect) {
    const levels = [
      {
        id: 'beginner',
        icon: <GraduationCap className="w-7 h-7" />,
        color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/40',
        activeColor: 'from-emerald-600/30 to-teal-600/20 border-emerald-400 shadow-lg shadow-emerald-500/20',
        iconColor: 'text-emerald-400',
        badge: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30',
        label: '🌱 Beginner',
        sublabel: 'Student ya Fresher',
        desc: 'Maine abhi technology ke baare mein padhna shuru kiya hai ya explore kar raha/rahi hoon. Mujhe zyada technical cheezein nahi pata abhi.',
      },
      {
        id: 'intermediate',
        icon: <Zap className="w-7 h-7" />,
        color: 'from-indigo-500/20 to-purple-500/10 border-indigo-500/40',
        activeColor: 'from-indigo-600/30 to-purple-600/20 border-indigo-400 shadow-lg shadow-indigo-500/20',
        iconColor: 'text-indigo-400',
        badge: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/30',
        label: '⚡ Intermediate',
        sublabel: '1–3 saal ka experience',
        desc: 'Mujhe thodi coding/tech aati hai. Maine kuch projects ya internship kar liye hain. Basic cheezein samajhta/samajhti hoon.',
      },
      {
        id: 'advanced',
        icon: <Star className="w-7 h-7" />,
        color: 'from-amber-500/20 to-orange-500/10 border-amber-500/40',
        activeColor: 'from-amber-600/30 to-orange-600/20 border-amber-400 shadow-lg shadow-amber-500/20',
        iconColor: 'text-amber-400',
        badge: 'text-amber-300 bg-amber-500/10 border-amber-500/30',
        label: '🌟 Advanced',
        sublabel: '3+ saal ka experience',
        desc: 'Main professionally kaam kar raha/rahi hoon ya mujhe tech mein deep knowledge hai. Main technical questions comfortable feel karta/karti hoon.',
      },
    ];

    return (
      <div className="max-w-2xl mx-auto space-y-8 pb-12 pt-4">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold uppercase tracking-widest">
            <Compass className="w-3.5 h-3.5" />
            <span>Career Discovery Assessment</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white leading-tight">
            Aap abhi kahan hain?
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
            Apna current experience level batao taaki hum aapke liye <strong className="text-slate-200">bilkul sahi sawal</strong> taiyaar kar sakein — easy aur relatable.
          </p>
        </div>

        {/* Level Cards */}
        <div className="space-y-4">
          {levels.map((lvl) => {
            const isActive = userLevel === lvl.id;
            return (
              <button
                key={lvl.id}
                onClick={() => setUserLevel(lvl.id)}
                className={`w-full text-left p-5 rounded-2xl border bg-gradient-to-r transition-all duration-200 flex items-start space-x-5 ${
                  isActive ? lvl.activeColor : lvl.color + ' hover:opacity-90'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${isActive ? 'bg-white/10' : 'bg-slate-900/50'} ${lvl.iconColor}`}>
                  {lvl.icon}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-base font-bold text-white">{lvl.label}</span>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${lvl.badge}`}>{lvl.sublabel}</span>
                    {isActive && <CheckCircle2 className="w-4 h-4 text-white ml-auto" />}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{lvl.desc}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setShowLevelSelect(false);
              setAssessmentMode('select');
            }}
            className="px-5 py-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white font-bold text-sm"
          >
            ← Back
          </button>
          <button
            onClick={() => handleLevelConfirm(userLevel)}
            className="flex-1 py-4 rounded-2xl bg-[#17324D] hover:bg-[#102A43] text-white font-bold text-base flex items-center justify-center space-x-3 shadow-sm transition-all"
          >
            <span>Assessment Shuru Karein</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        <p className="text-center text-xs text-slate-600">
          Level baad mein bhi change kiya ja sakta hai — Retake Assessment se.
        </p>
      </div>
    );
  }

  // Gemini AI Analysis Screen
  if (analyzing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 text-center max-w-lg mx-auto p-8 rounded-2xl bg-slate-900/80 border border-slate-800">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
          <Sparkles className="w-8 h-8 animate-pulse text-indigo-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white mb-2">Analyzing Your Career Discovery Profile</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Gemini AI is evaluating your problem solving, logical reasoning, and work style preferences against our 12 structured career role frameworks...
          </p>
        </div>
        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 h-full w-[80%] animate-pulse"></div>
        </div>
      </div>
    );
  }

  // ────────────────────────────────────────────────────
  // 4. RESULTS & CAREER PROFILE VIEW
  // ────────────────────────────────────────────────────
  if (result && result.analysis && assessmentMode === 'result') {
    const { analysis } = result;
    const catalogMap = new Map(catalog.map((c) => [c.slug, c]));
    const matchedCatalogDetails = compareMatch ? catalogMap.get(compareMatch.slug) : null;

    return (
      <div className="max-w-5xl mx-auto space-y-8 pb-12">
        {/* Banner Alert for Target Career Selection */}
        {targetSuccessMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span className="font-semibold">{targetSuccessMsg}</span>
          </div>
        )}

        {/* Transition 1: Assessment -> Resume Action Banner */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-indigo-950/70 border border-emerald-500/30 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Career Goal Active ✨
              </span>
              {selectedTarget && (
                <span className="text-xs text-slate-300 font-semibold">
                  Target: <strong className="text-white">{selectedTarget}</strong>
                </span>
              )}
            </div>
            <h3 className="text-lg font-bold text-white">Next Step: Build Your Learning Roadmap & Scan Resume</h3>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Generate your week-by-week learning roadmap tailored to your exact skill gaps, or upload your resume to test ATS score for {selectedTarget || 'your target career'}.
            </p>
          </div>
          <div className="flex items-center space-x-3 shrink-0">
            <Link
              href="/roadmap"
              className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-lg shadow-indigo-600/30"
            >
              <span>View Roadmap 🗺️</span>
            </Link>
            <Link
              href="/resume"
              className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-lg shadow-emerald-600/30"
            >
              <span>Upload Resume 📄</span>
            </Link>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
            {error}
          </div>
        )}

        {/* Top Header with Dual Controls */}
        <div className="p-8 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900 border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Career Discovery Profile Active</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white">Your AI Career Discovery Profile</h1>
            <p className="text-slate-300 text-xs mt-1">
              Evidence-backed career evaluation powered by AI. You remain in complete control of your target career selection.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              onClick={() => {
                setDirectResultData(null);
                setAssessmentMode('direct');
              }}
              className="px-4 py-2.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 font-semibold text-xs transition-all flex items-center space-x-1.5"
            >
              <Target className="w-4 h-4 text-indigo-400" />
              <span>Direct Goal / Skill Set</span>
            </button>
            <button
              onClick={handleRestart}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-semibold text-xs transition-all flex items-center space-x-1.5"
            >
              <RotateCcw className="w-4 h-4 text-slate-400" />
              <span>Retake Quiz / Change</span>
            </button>
          </div>
        </div>

        {/* Career Archetype & Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Career Archetype</span>
            <h2 className="text-2xl font-bold text-indigo-400">{analysis.primary_archetype}</h2>
            <p className="text-xs text-slate-400 leading-relaxed">{analysis.work_style_summary || 'Focused on building scalable technical solutions and mastering high-impact technologies.'}</p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Motivation & Driver</span>
            <p className="text-sm font-semibold text-slate-200">{analysis.motivation_profile || 'Continuous skill progression and tangible engineering impact'}</p>
            <div className="flex flex-wrap gap-1.5 pt-2">
              {(analysis.interest_profile ?? []).map((interest, idx) => (
                <span key={idx} className="px-2.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300">
                  {interest}
                </span>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Current Selected Target</span>
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-emerald-400 shrink-0" />
              <h2 className="text-xl font-bold text-white">{selectedTarget || 'None Selected'}</h2>
            </div>
            <p className="text-xs text-slate-400">
              Selected target career controls skill gap priorities and personalized roadmap milestones.
            </p>
          </div>
        </div>

        {/* Top Strengths Identified */}
        {analysis.top_strengths && analysis.top_strengths.length > 0 && (
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Identified Core Strengths & Evidence
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {analysis.top_strengths.map((str, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-bold text-white">{str.strength_name}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{str.evidence_reason}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommended Career Roles with Match Scores */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">Recommended Career Paths</h3>
            <span className="text-xs text-slate-400">Select any role to set as your active target career</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(analysis.recommended_careers || []).map((career) => {
              const isSelected = selectedTarget === career.title;
              return (
                <div
                  key={career.slug}
                  className={`p-6 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-500/10'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {career.match_percentage}% Match
                      </span>
                      {isSelected && (
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Active Target</span>
                        </span>
                      )}
                    </div>
                    <h4 className="text-lg font-bold text-white">{career.title}</h4>
                    <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                      {Array.isArray(career.why_recommended) ? career.why_recommended[0] : (career.why_recommended || 'Strong alignment with your core problem-solving instinct.')}
                    </p>
                  </div>

                  <div className="pt-2 flex items-center space-x-2">
                    <button
                      onClick={() => setCompareMatch(career)}
                      className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-all flex items-center justify-center space-x-1"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>Details</span>
                    </button>
                    <button
                      disabled={isSelected}
                      onClick={() => handleSetTargetCareer(career.slug)}
                      className={`flex-1 py-2 px-3 rounded-xl font-semibold text-xs transition-all flex items-center justify-center space-x-1 ${
                        isSelected
                          ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 cursor-default'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/20'
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Target Set</span>
                        </>
                      ) : (
                        <>
                          <Target className="w-3.5 h-3.5" />
                          <span>Set Target</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* CAREER COMPARISON MODAL */}
        {compareMatch && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <span className="text-xs text-indigo-400 font-bold uppercase tracking-wider">Career Role Detailed Comparison</span>
                  <h3 className="text-2xl font-bold text-white flex items-center space-x-3 mt-1">
                    <span>{compareMatch.title}</span>
                    <span className="px-2.5 py-0.5 rounded text-xs font-extrabold bg-indigo-500/20 text-indigo-300">
                      {compareMatch.match_percentage}% Match
                    </span>
                  </h3>
                </div>
                <button
                  onClick={() => setCompareMatch(null)}
                  className="p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {matchedCatalogDetails && (
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-4 rounded-xl border border-slate-800">
                  {matchedCatalogDetails.description}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Required Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(matchedCatalogDetails?.required_skills || compareMatch.supporting_strengths || []).map((sk, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-slate-200 font-medium">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Target Learning Gaps</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(compareMatch.learning_gaps || []).map((gap, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 font-medium">
                        {gap}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex justify-end space-x-3">
                <button
                  onClick={() => setCompareMatch(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    handleSetTargetCareer(compareMatch.slug);
                    setCompareMatch(null);
                  }}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/20"
                >
                  Confirm as Target Career
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ────────────────────────────────────────────────────
  // 5. QUIZ QUESTIONS VIEW
  // ────────────────────────────────────────────────────
  const currentQ = session?.current_question;
  const currentStep = session?.current_step || 1;
  const totalQ = session?.total_questions || 5;
  const progressPct = Math.min(100, Math.round(((currentStep - 1) / totalQ) * 100));

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-6 rounded-2xl bg-slate-900/60 border border-slate-800 gap-4">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <button
              onClick={() => setAssessmentMode('select')}
              className="text-xs text-slate-400 hover:text-white underline underline-offset-2"
            >
              ← Back to Modes
            </button>
            <span className="text-slate-600">•</span>
            <div className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              <Compass className="w-3.5 h-3.5" />
              <span>{t('assessment.title', 'Career Discovery Quiz')}</span>
            </div>
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            {t('assessment.questionStep', 'Question')} {currentStep} {t('assessment.of', 'of')} {totalQ}: {currentQ?.dimension || 'General Discovery'}
          </h1>
        </div>
        <div className="sm:text-right shrink-0">
          <span className="text-xs text-slate-400 font-semibold">{progressPct}% {t('common.active', 'Complete')}</span>
          <div className="w-44 bg-slate-800 h-2.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 h-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100 leading-relaxed">
                {currentQ.question_text}
              </h2>
              <p className="text-xs text-slate-400 mt-2">
                {t('assessment.instruction', 'Please select the option that best describes your instinctual approach:')}
              </p>
            </div>
          </div>

          {/* Options List */}
          <div className="space-y-3 pt-2">
            {currentQ.options.map((option) => {
              const isSelected = selectedOption === option.id;
              return (
                <button
                  key={option.id}
                  onClick={() => {
                    setSelectedOption(option.id);
                    setShowCustomInput(false);
                    setCustomAnswerText('');
                  }}
                  disabled={submitting}
                  className={`w-full text-left p-4 rounded-xl border transition-all duration-200 flex items-center justify-between ${
                    isSelected
                      ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <span
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                        isSelected ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {option.id}
                    </span>
                    <span className="text-sm font-medium leading-relaxed">{option.text}</span>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="w-5 h-5 text-indigo-400 shrink-0 ml-2" />
                  )}
                </button>
              );
            })}

            {/* Custom Answer Option */}
            <div className="mt-1">
              <button
                onClick={() => {
                  const next = !showCustomInput;
                  setShowCustomInput(next);
                  if (next) {
                    setSelectedOption('custom');
                  } else {
                    setSelectedOption(null);
                    setCustomAnswerText('');
                  }
                }}
                disabled={submitting}
                className={`w-full text-left p-4 rounded-xl border transition-all duration-200 flex items-center space-x-4 ${
                  selectedOption === 'custom'
                    ? 'bg-purple-600/20 border-purple-500 text-white shadow-md shadow-purple-500/10'
                    : 'bg-slate-950/60 border-slate-700 border-dashed text-slate-400 hover:border-slate-500 hover:text-slate-300'
                }`}
              >
                <span className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                  selectedOption === 'custom' ? 'bg-purple-500 text-white' : 'bg-slate-800 text-slate-400'
                }`}>
                  <Pencil className="w-4 h-4" />
                </span>
                <span className="text-sm font-medium">Koi option suit nahi karta? Apna khud ka jawab likhein</span>
                {selectedOption === 'custom' && <CheckCircle2 className="w-5 h-5 text-purple-400 shrink-0 ml-auto" />}
              </button>

              {showCustomInput && (
                <div className="mt-3 space-y-2">
                  <textarea
                    value={customAnswerText}
                    onChange={(e) => setCustomAnswerText(e.target.value)}
                    placeholder="Yahan apna jawab likhein... (jaise: 'Mujhe graphic design mein zyada interest hai' ya 'Main gaming apps banana chahta hoon')"
                    rows={3}
                    disabled={submitting}
                    className="w-full p-4 rounded-xl bg-slate-950 border border-purple-500/40 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-purple-400 resize-none transition-all"
                  />
                  <p className="text-[11px] text-slate-600 pl-1">Aapka jawab AI ko aapke career ko better samajhne mein madad karega.</p>
                </div>
              )}
            </div>
          </div>

          {/* Action Footer */}
          <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Your response will calibrate your Career Digital Twin profile.
            </p>
            <button
              disabled={!selectedOption || (selectedOption === 'custom' && !customAnswerText.trim()) || submitting}
              onClick={handleAnswerSubmit}
              className={`px-6 py-3 rounded-xl font-semibold text-sm flex items-center space-x-2 transition-all ${
                selectedOption && !submitting
                  ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t('assessment.submitting', 'Recording Answer...')}</span>
                </>
              ) : (
                <>
                  <span>
                    {currentStep === totalQ
                      ? t('assessment.submitBtn', 'Complete Assessment & Generate AI Analysis ✨')
                      : t('assessment.nextBtn', 'Next Question →')}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}