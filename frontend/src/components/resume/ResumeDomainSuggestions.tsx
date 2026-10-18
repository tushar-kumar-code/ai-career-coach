'use client';

import React from 'react';
import Link from 'next/link';
import { 
  Sparkles, 
  Cpu, 
  Server, 
  Smartphone, 
  Globe, 
  Database, 
  Cloud, 
  ShieldCheck, 
  ArrowRight, 
  Compass, 
  CheckCircle2, 
  Target, 
  Briefcase,
  TrendingUp,
  Layers
} from 'lucide-react';
import { ResumeAnalysisData, ResumeDomainSuggestion } from '@/lib/types';

interface ResumeDomainSuggestionsProps {
  resumeData: ResumeAnalysisData;
}

export default function ResumeDomainSuggestions({ resumeData }: ResumeDomainSuggestionsProps) {
  // If backend provided suggested_domains, use them; otherwise run client-side synthesis fallback
  const suggestions: ResumeDomainSuggestion[] = React.useMemo(() => {
    if (resumeData.suggested_domains && resumeData.suggested_domains.length > 0) {
      return resumeData.suggested_domains;
    }
    return synthesizeClientDomainSuggestions(resumeData);
  }, [resumeData]);

  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  const getDomainIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('ai') || n.includes('intelligence') || n.includes('machine learning')) {
      return <Cpu className="w-5 h-5 text-purple-400" />;
    }
    if (n.includes('backend') || n.includes('api') || n.includes('distributed')) {
      return <Server className="w-5 h-5 text-blue-400" />;
    }
    if (n.includes('mobile') || n.includes('android') || n.includes('flutter') || n.includes('ios')) {
      return <Smartphone className="w-5 h-5 text-emerald-400" />;
    }
    if (n.includes('full-stack') || n.includes('web') || n.includes('frontend')) {
      return <Globe className="w-5 h-5 text-cyan-400" />;
    }
    if (n.includes('data') || n.includes('analytics') || n.includes('scientist')) {
      return <Database className="w-5 h-5 text-amber-400" />;
    }
    if (n.includes('cloud') || n.includes('devops')) {
      return <Cloud className="w-5 h-5 text-sky-400" />;
    }
    if (n.includes('security') || n.includes('cyber')) {
      return <ShieldCheck className="w-5 h-5 text-rose-400" />;
    }
    return <Layers className="w-5 h-5 text-indigo-400" />;
  };

  const getBadgeColor = (pct: number) => {
    if (pct >= 85) {
      return 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300';
    }
    if (pct >= 70) {
      return 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300';
    }
    return 'bg-amber-500/15 border-amber-500/30 text-amber-300';
  };

  return (
    <section className="space-y-4">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-white tracking-tight flex items-center space-x-2">
              <span>AI Career Domain Suggestions</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">
                Based on Resume Profile
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified skills, real project technologies, and practical roles analyzed to determine your strongest career tracks.
            </p>
          </div>
        </div>

        <Link
          href="/roadmap"
          className="self-start sm:self-auto inline-flex items-center space-x-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
        >
          <span>Explore All Roadmaps</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Domain Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {suggestions.map((dom, idx) => {
          const isTopMatch = idx === 0;

          return (
            <div
              key={idx}
              className={`p-6 rounded-2xl border transition-all duration-200 flex flex-col justify-between space-y-5 ${
                isTopMatch
                  ? 'bg-gradient-to-br from-indigo-950/40 via-slate-900 to-purple-950/30 border-indigo-500/40 shadow-xl shadow-indigo-950/20'
                  : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700/80'
              }`}
            >
              {/* Card Header */}
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 shrink-0">
                      {getDomainIcon(dom.domain_name)}
                    </div>
                    <div>
                      {isTopMatch && (
                        <span className="inline-block text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-0.5">
                          ⭐ Top Recommended Track
                        </span>
                      )}
                      <h3 className="text-base font-bold text-white leading-snug">
                        {dom.domain_name}
                      </h3>
                    </div>
                  </div>

                  {/* Match Percentage Badge */}
                  <div className={`px-2.5 py-1 rounded-full text-xs font-bold border shrink-0 ${getBadgeColor(dom.match_percentage)}`}>
                    {dom.match_percentage}% Fit
                  </div>
                </div>

                {/* Fit Reason */}
                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 leading-relaxed font-normal">
                  <strong className="text-slate-200 block mb-1 font-semibold flex items-center space-x-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Why This Domain Fits You:</span>
                  </strong>
                  <span>{dom.fit_reason}</span>
                </div>
              </div>

              {/* Matched Skills Chips */}
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Matched Resume Competencies:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {dom.matched_skills && dom.matched_skills.length > 0 ? (
                    dom.matched_skills.map((sk, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-medium text-emerald-300 flex items-center space-x-1"
                      >
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        <span>{sk}</span>
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 italic">Foundational technical capabilities</span>
                  )}
                </div>
              </div>

              {/* Target Job Roles */}
              {dom.recommended_roles && dom.recommended_roles.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                    Target Roles in this Domain:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {dom.recommended_roles.map((role, rIdx) => (
                      <span
                        key={rIdx}
                        className="px-2 py-0.5 rounded-md bg-slate-800/80 border border-slate-700/80 text-[11px] font-semibold text-slate-200"
                      >
                        {role}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Next Growth Areas */}
              {dom.growth_areas && dom.growth_areas.length > 0 && (
                <div className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-500/20 space-y-1">
                  <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider flex items-center space-x-1">
                    <Target className="w-3 h-3 text-indigo-400" />
                    <span>Recommended Next Skills to Master:</span>
                  </span>
                  <ul className="text-[11px] text-slate-300 space-y-0.5 list-disc list-inside">
                    {dom.growth_areas.map((gap, gIdx) => (
                      <li key={gIdx} className="leading-relaxed">
                        {gap}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                <Link
                  href="/interview"
                  className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition"
                >
                  <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                  <span>Practice Interview</span>
                </Link>

                <Link
                  href="/roadmap"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm"
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>Start Domain Roadmap</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/**
 * Client-side synthesis fallback if viewing cached analysis before backend upgrade.
 */
function synthesizeClientDomainSuggestions(resumeData: ResumeAnalysisData): ResumeDomainSuggestion[] {
  const skillList: string[] = [];
  (resumeData.extracted_skills || []).forEach(s => {
    if (s && s.name) {
      skillList.push(s.name.toLowerCase().trim());
    }
  });

  const projects = resumeData.projects || [];
  const experience = resumeData.experience || [];

  let fullCorpus = '';
  projects.forEach(p => {
    fullCorpus += ` ${p.title} ${p.description} ${(p.technologies || []).join(' ')}`;
  });
  experience.forEach(e => {
    fullCorpus += ` ${e.role} ${e.company} ${e.description} ${(e.key_achievements || []).join(' ')}`;
  });
  fullCorpus = fullCorpus.toLowerCase();

  const hasSkill = (sk: string) => {
    const clean = sk.toLowerCase().trim();
    if (skillList.indexOf(clean) !== -1) return true;
    for (let i = 0; i < skillList.length; i++) {
      const s = skillList[i];
      if (s.indexOf(clean) !== -1 || clean.indexOf(s) !== -1) return true;
    }
    return fullCorpus.indexOf(clean) !== -1;
  };

  const domainConfigs = [
    {
      domain_name: 'Artificial Intelligence & Machine Learning',
      core_skills: ['Python', 'PyTorch', 'TensorFlow', 'TensorFlow Lite', 'LLMs', 'LLaMA', 'MediaPipe', 'RAG', 'ChromaDB', 'OpenCV'],
      recommended_roles: ['AI / Machine Learning Engineer', 'LLM Applications Developer', 'Edge AI Specialist'],
      growth_areas: ['LangChain / LlamaIndex Agentic Workflows', 'Model Quantization (GGUF, TensorRT)'],
      keywords: ['ai', 'rag', 'llm', 'llama', 'mediapipe', 'pytorch', 'tensorflow', 'model']
    },
    {
      domain_name: 'Backend & Cloud API Systems',
      core_skills: ['Python', 'FastAPI', 'REST APIs', 'Java', 'Firebase', 'PostgreSQL', 'SQL', 'Docker', 'Git'],
      recommended_roles: ['Backend Systems Engineer', 'API & Microservices Architect', 'Python Backend Developer'],
      growth_areas: ['Distributed Message Streaming (Kafka / RabbitMQ)', 'Redis Caching Clusters'],
      keywords: ['fastapi', 'backend', 'api', 'firebase', 'sql', 'database', 'server']
    },
    {
      domain_name: 'Mobile & Cross-Platform Development',
      core_skills: ['Flutter', 'Android', 'Android SDK', 'Java', 'Kotlin', 'XML', 'Mobile UI'],
      recommended_roles: ['Mobile Application Developer (Flutter / Android)', 'On-Device Mobile AI Engineer'],
      growth_areas: ['Advanced State Management (Riverpod / BLoC)', 'Declarative Android Jetpack Compose'],
      keywords: ['flutter', 'android', 'mobile', 'app', 'sign language']
    },
    {
      domain_name: 'Full-Stack & Web Engineering',
      core_skills: ['JavaScript', 'TypeScript', 'React', 'HTML', 'CSS', 'Tailwind CSS', 'FastAPI'],
      recommended_roles: ['Full Stack Developer', 'Frontend Web Engineer'],
      growth_areas: ['Next.js App Router & Server Actions', 'Automated E2E Testing with Playwright'],
      keywords: ['fullstack', 'web', 'frontend', 'react', 'vis.js']
    }
  ];

  const results: ResumeDomainSuggestion[] = [];

  domainConfigs.forEach(cfg => {
    const matched = cfg.core_skills.filter(hasSkill);
    const hasProjectProof = cfg.keywords.some(kw => fullCorpus.includes(kw));

    let score = matched.length * 12;
    if (hasProjectProof) score += 30;

    let matchPct = 40;
    if (score >= 60) matchPct = Math.min(96, score + 15);
    else if (score >= 35) matchPct = Math.min(84, score + 18);
    else if (matched.length > 0) matchPct = 55;

    if (matchPct >= 45 || hasProjectProof) {
      results.push({
        domain_name: cfg.domain_name,
        match_percentage: matchPct,
        fit_reason: hasProjectProof 
          ? `Hands-on practical implementation demonstrated in project portfolio with core competencies in ${matched.slice(0, 3).join(', ') || 'modern toolsets'}.`
          : `Strong technical capabilities matching domain requirements with verified skills in ${matched.slice(0, 3).join(', ')}.`,
        matched_skills: matched,
        recommended_roles: cfg.recommended_roles,
        growth_areas: cfg.growth_areas
      });
    }
  });

  results.sort((a, b) => b.match_percentage - a.match_percentage);
  return results.slice(0, 4);
}
