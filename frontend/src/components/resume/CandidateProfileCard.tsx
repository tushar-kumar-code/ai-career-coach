'use client';

import React, { useState } from 'react';
import { 
  User, 
  Briefcase, 
  GraduationCap, 
  Code2, 
  FolderGit2, 
  Award, 
  Mail, 
  Phone, 
  MapPin, 
  Linkedin, 
  Github, 
  Globe, 
  ExternalLink, 
  Sparkles, 
  CheckCircle2,
  Calendar,
  Layers,
  Trophy,
  Globe2,
  BookOpen,
  Users2
} from 'lucide-react';
import { 
  ResumeAnalysisData, 
  ResumeProjectItem, 
  ResumeCertificationItem, 
  ResumeAchievementItem,
  ResumeLanguageItem,
  ResumeExtracurricularItem,
  ResumePublicationItem
} from '@/lib/types';

interface CandidateProfileCardProps {
  resumeData: ResumeAnalysisData;
  compact?: boolean;
}

export function cleanProfessionalSummary(
  rawSummary?: string,
  contactInfo?: {
    name?: string;
    headline?: string;
    email?: string;
    phone?: string;
    location?: string;
    github?: string;
    linkedin?: string;
    portfolio?: string;
  }
): string {
  if (!rawSummary || !rawSummary.trim()) return '';

  const name = contactInfo?.name?.trim().toLowerCase() || '';
  const email = contactInfo?.email?.trim().toLowerCase() || '';
  const phone = contactInfo?.phone?.replace(/\D/g, '') || '';
  const headline = contactInfo?.headline?.trim().toLowerCase() || '';
  const location = contactInfo?.location?.trim().toLowerCase() || '';

  const lines = rawSummary.split(/\r?\n/);
  const cleanedLines: string[] = [];

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;

    const lower = line.toLowerCase();

    // 1. Skip Candidate Name
    if (name && (lower === name || lower.startsWith(name + ' -') || lower.startsWith(name + ' |'))) {
      continue;
    }

    // 2. Skip Headline / Role
    if (headline && (lower === headline || lower.startsWith(headline + ' |') || lower.startsWith(headline + ' -'))) {
      continue;
    }

    // 2b. Skip Standalone Role / Designation Titles (e.g. Software Engineer, Developer, etc.)
    const isRoleTitle =
      /^(aspiring|junior|senior|lead|entry[-\s]?level|associate)?\s*(software|web|full[-\s]?stack|frontend|backend|mobile|android|ios|devops|cloud|data|ai|ml|machine[-\s]?learning|deep[-\s]?learning|python|java|react|node|c\+\+|system|systems|qa|test|testing|cyber|security|network|database|computer[-\s]?science)?\s*(engineer|developer|programmer|architect|specialist|analyst|scientist|student|intern|fresher|consultant|professional|coder)s?$/i.test(line) ||
      (/^[a-zA-Z\s/-]{2,45}$/.test(line) && line.split(/\s+/).length <= 4 && /(engineer|developer|programmer|architect|specialist|analyst|scientist|student|intern|fresher)/i.test(line) && !/[.,;!?]/.test(line));

    if (isRoleTitle) {
      continue;
    }

    // 3. Skip URLs, GitHub, LinkedIn, emails
    if (
      lower.includes('http://') ||
      lower.includes('https://') ||
      lower.includes('github.com') ||
      lower.includes('linkedin.com') ||
      (email && lower.includes(email)) ||
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/.test(line)
    ) {
      const words = line.split(/\s+/);
      const isHeaderLine =
        lower.includes('|') ||
        lower.includes('github') ||
        lower.includes('linkedin') ||
        words.length < 15;
      if (isHeaderLine) {
        continue;
      }
    }

    // 4. Skip Phone numbers and contact pipe lines
    const digitsOnly = line.replace(/\D/g, '');
    if (phone && digitsOnly.length >= 7 && digitsOnly.includes(phone)) {
      continue;
    }
    if (
      (lower.includes('|') || lower.includes('•')) &&
      (lower.includes('phone') || lower.includes('mail') || lower.includes('@') || digitsOnly.length >= 10)
    ) {
      continue;
    }

    // 5. Skip Location
    if (location && lower === location) {
      continue;
    }

    // 6. Skip header title text like "Profile Summary" / "About Me"
    if (/^(curriculum vitae|resume|profile summary|professional summary|about me|summary)[\s:]*$/i.test(line)) {
      continue;
    }

    // 7. Skip pure separators
    if (/^[|\-•/,\s]+$/.test(line)) {
      continue;
    }

    cleanedLines.push(rawLine.trim());
  }

  return cleanedLines.length > 0 ? cleanedLines.join('\n\n').trim() : rawSummary.trim();
}

/** Fallback extractor to parse projects from text if database array was 0 */
function extractFallbackProjects(rawText?: string, formattedText?: string): ResumeProjectItem[] {
  const text = formattedText || rawText || '';
  if (!text.trim()) return [];

  const projectRegex = /(?:###?\s*(?:Projects|Academic Projects|Personal Projects|Key Projects)|(?:^|\n)(?:PROJECTS|ACADEMIC PROJECTS|PERSONAL PROJECTS|KEY PROJECTS)[\s\-_=*:]*\n)([\s\S]*?)(?=\n(?:###?\s+[A-Z]|(?:EXPERIENCE|EDUCATION|SKILLS|CERTIFICATIONS|ACHIEVEMENTS|LANGUAGES|PUBLICATIONS)[\s\-_=*:]*\n)|$)/i;
  const match = text.match(projectRegex);
  if (!match || !match[1]) return [];

  const sectionText = match[1].trim();
  const rawBlocks = sectionText.split(/\n\s*\n/);
  const results: ResumeProjectItem[] = [];

  for (const block of rawBlocks) {
    const lines = block.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (!lines.length) continue;
    let titleLine = lines[0].replace(/^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*/, '').trim();
    if (!titleLine || titleLine.length < 3) continue;

    let technologies: string[] = [];
    const techMatch = titleLine.match(/[\(\[]([^\)\]]+)[\)\]]/);
    if (techMatch) {
      technologies = techMatch[1].split(/[,|/]/).map(t => t.trim()).filter(t => t.length < 25);
      titleLine = titleLine.replace(/[\(\[][^\)\]]+[\)\]]/, '').trim();
    }

    const linkMatch = block.match(/https?:\/\/[^\s\)]+/);
    const link = linkMatch ? linkMatch[0] : '';
    const desc = lines.slice(1).join('\n') || titleLine;

    results.push({
      title: titleLine || 'Project',
      role: 'Developer',
      technologies,
      description: desc,
      link
    });
  }
  return results;
}

export default function CandidateProfileCard({ resumeData, compact = false }: CandidateProfileCardProps) {
  const [activeTab, setActiveTab] = useState<
    'all' | 'about' | 'skills' | 'experience' | 'projects' | 'education' | 'certifications' | 'achievements' | 'languages_activities'
  >('all');

  const about = resumeData.about_user || resumeData.contact_info;
  const skills = resumeData.extracted_skills || [];
  const experience = resumeData.experience || [];
  
  // Safe project extraction with fallback
  const directProjects = resumeData.projects || [];
  const displayProjects = directProjects.length > 0 
    ? directProjects 
    : extractFallbackProjects(resumeData.raw_text, resumeData.formatted_text);

  const education = resumeData.education || [];
  
  // Safe extraction for all additional sections
  const displayCerts: ResumeCertificationItem[] = 
    (resumeData.certifications && resumeData.certifications.length > 0) 
      ? resumeData.certifications 
      : ((about as any)?.certifications || (resumeData.ats_breakdown as any)?.certifications || []);

  const displayAchievements: ResumeAchievementItem[] = 
    (resumeData.achievements && resumeData.achievements.length > 0)
      ? resumeData.achievements
      : ((about as any)?.achievements || (resumeData.ats_breakdown as any)?.achievements || []);

  const displayLanguages: ResumeLanguageItem[] = 
    (resumeData.languages && resumeData.languages.length > 0)
      ? resumeData.languages
      : ((about as any)?.languages || (resumeData.ats_breakdown as any)?.languages || []);

  const displayPublications: ResumePublicationItem[] = 
    (resumeData.publications && resumeData.publications.length > 0)
      ? resumeData.publications
      : ((about as any)?.publications || (resumeData.ats_breakdown as any)?.publications || []);

  const displayExtracurriculars: ResumeExtracurricularItem[] = 
    (resumeData.extracurriculars && resumeData.extracurriculars.length > 0)
      ? resumeData.extracurriculars
      : ((about as any)?.extracurriculars || (resumeData.ats_breakdown as any)?.extracurriculars || []);

  const cleanedSummary = cleanProfessionalSummary(about?.summary, about);

  // Group skills by category
  const skillsByCategory: Record<string, typeof skills> = {};
  skills.forEach((sk) => {
    const cat = sk.category || 'General';
    if (!skillsByCategory[cat]) skillsByCategory[cat] = [];
    skillsByCategory[cat].push(sk);
  });

  // Dynamic Navigation Tabs
  const navTabs = [
    { id: 'all', label: 'Complete Overview', icon: Layers },
    { id: 'about', label: 'About & Summary', icon: User },
    { id: 'skills', label: `Skills (${skills.length})`, icon: Code2 },
    { id: 'experience', label: `Experience (${experience.length})`, icon: Briefcase },
    { id: 'projects', label: `Projects (${displayProjects.length})`, icon: FolderGit2 },
    { id: 'education', label: `Education (${education.length})`, icon: GraduationCap },
    ...(displayCerts.length > 0 
      ? [{ id: 'certifications', label: `Certifications (${displayCerts.length})`, icon: Award }] 
      : []),
    ...(displayAchievements.length > 0 
      ? [{ id: 'achievements', label: `Achievements (${displayAchievements.length})`, icon: Trophy }] 
      : []),
    ...((displayLanguages.length > 0 || displayExtracurriculars.length > 0 || displayPublications.length > 0)
      ? [{ 
          id: 'languages_activities', 
          label: `Languages & Activities (${displayLanguages.length + displayExtracurriculars.length + displayPublications.length})`, 
          icon: Globe2 
        }]
      : []),
  ];

  return (
    <div className="rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900/60 via-purple-900/50 to-slate-900/80 p-6 border-b border-slate-800 relative">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center text-white font-extrabold text-2xl shadow-lg shadow-indigo-500/30">
              {about?.name ? about.name.charAt(0).toUpperCase() : 'C'}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
                  {about?.name || 'Candidate Profile'}
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Resume Verified</span>
                </span>
              </div>
              <p className="text-sm font-medium text-indigo-300 mt-0.5">
                {about?.headline || resumeData.target_match?.target_career_name || 'Software Professional'}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            {about?.email && (
              <a 
                href={`mailto:${about.email}`}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 transition-colors"
              >
                <Mail className="w-3.5 h-3.5 text-indigo-400" />
                <span>{about.email}</span>
              </a>
            )}
            {about?.phone && (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300">
                <Phone className="w-3.5 h-3.5 text-emerald-400" />
                <span>{about.phone}</span>
              </span>
            )}
            {about?.location && (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300">
                <MapPin className="w-3.5 h-3.5 text-rose-400" />
                <span>{about.location}</span>
              </span>
            )}
            {about?.linkedin && (
              <a 
                href={about.linkedin.startsWith('http') ? about.linkedin : `https://${about.linkedin}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-300 transition-colors"
              >
                <Linkedin className="w-3.5 h-3.5" />
                <span>LinkedIn</span>
                <ExternalLink className="w-3 h-3 opacity-70" />
              </a>
            )}
            {about?.github && (
              <a 
                href={about.github.startsWith('http') ? about.github : `https://${about.github}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 transition-colors"
              >
                <Github className="w-3.5 h-3.5" />
                <span>GitHub</span>
                <ExternalLink className="w-3 h-3 opacity-70" />
              </a>
            )}
            {about?.portfolio && (
              <a 
                href={about.portfolio.startsWith('http') ? about.portfolio : `https://${about.portfolio}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 text-teal-300 transition-colors"
              >
                <Globe className="w-3.5 h-3.5" />
                <span>Portfolio</span>
                <ExternalLink className="w-3 h-3 opacity-70" />
              </a>
            )}
          </div>
        </div>

        {/* Section Navigation Tabs */}
        {!compact && (
          <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-slate-800/80">
            {navTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                      : 'bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-700/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Main Body Content */}
      <div className="p-6 space-y-6">
        {/* 1. About / Summary */}
        {(activeTab === 'all' || activeTab === 'about') && cleanedSummary && (
          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <User className="w-4 h-4" />
              <span>Professional Summary</span>
            </div>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">
              {cleanedSummary}
            </p>
          </div>
        )}

        {/* 2. Extracted Skills Part-wise */}
        {(activeTab === 'all' || activeTab === 'skills') && skills.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
                <Code2 className="w-4 h-4" />
                <span>Extracted Skills Profile ({skills.length} skills identified)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(skillsByCategory).map(([category, catSkills]) => (
                <div key={category} className="p-3.5 rounded-xl bg-slate-800/30 border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 flex items-center justify-between">
                    <span>{category}</span>
                    <span className="text-[10px] text-slate-500 font-normal">{catSkills.length} skills</span>
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {catSkills.map((sk, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-indigo-200 border border-indigo-500/20"
                      >
                        <span>{sk.name}</span>
                        {sk.proficiency_estimated && (
                          <span className="text-[10px] font-bold text-indigo-400">
                            {sk.proficiency_estimated}%
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. Work Experience Part-wise */}
        {(activeTab === 'all' || activeTab === 'experience') && experience.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <Briefcase className="w-4 h-4" />
              <span>Work & Professional Experience ({experience.length})</span>
            </div>

            <div className="space-y-3">
              {experience.map((exp, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-800/30 border border-slate-800 space-y-2 relative pl-5 border-l-2 border-l-indigo-500">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        {exp.role || 'Role / Position'}
                      </h4>
                      <p className="text-xs font-semibold text-indigo-300">
                        {exp.company} {exp.location ? `• ${exp.location}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-slate-400">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      <span>
                        {exp.start_date || 'N/A'} - {exp.is_current ? 'Present' : (exp.end_date || 'Present')}
                      </span>
                      {exp.is_current && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          Current
                        </span>
                      )}
                    </div>
                  </div>

                  {exp.description && (
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {exp.description}
                    </p>
                  )}

                  {exp.key_achievements && exp.key_achievements.length > 0 && (
                    <ul className="space-y-1 mt-2 text-xs text-slate-300 list-disc list-inside">
                      {exp.key_achievements.map((ach, aIdx) => (
                        <li key={aIdx} className="leading-relaxed">
                          {ach}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. Projects Part-wise */}
        {(activeTab === 'all' || activeTab === 'projects') && displayProjects.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <FolderGit2 className="w-4 h-4" />
              <span>Projects & Portfolio ({displayProjects.length})</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {displayProjects.map((proj, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-800/30 border border-slate-800 space-y-2 flex flex-col justify-between hover:border-slate-700 transition-all">
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-bold text-white">
                        {proj.title || 'Project'}
                      </h4>
                      {proj.link && (
                        <a 
                          href={proj.link.startsWith('http') ? proj.link : `https://${proj.link}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-indigo-400 hover:text-indigo-300 inline-flex items-center space-x-1"
                        >
                          <span>View</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    {proj.role && (
                      <p className="text-xs text-indigo-300 font-medium">{proj.role}</p>
                    )}
                    {proj.description && (
                      <p className="text-xs text-slate-300 mt-1.5 leading-relaxed whitespace-pre-line">
                        {proj.description}
                      </p>
                    )}
                  </div>

                  {proj.technologies && proj.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-slate-800/80">
                      {proj.technologies.map((t, tIdx) => (
                        <span key={tIdx} className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5. Education Part-wise */}
        {(activeTab === 'all' || activeTab === 'education') && education.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <GraduationCap className="w-4 h-4" />
              <span>Education & Academic Background ({education.length})</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {education.map((edu, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white">
                      {edu.degree || 'Degree / Qualification'}
                    </h4>
                    {(edu.start_year || edu.end_year) && (
                      <span className="text-[11px] text-slate-400 font-medium">
                        {edu.start_year ? `${edu.start_year} - ` : ''}{edu.end_year || ''}
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-semibold text-indigo-300">
                    {edu.institution}
                  </p>
                  {edu.field_of_study && (
                    <p className="text-[11px] text-slate-400">
                      Field: {edu.field_of_study}
                    </p>
                  )}
                  {edu.grade && (
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 mt-1">
                      Grade/Score: {edu.grade}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 6. Certifications & Licenses Part-wise */}
        {(activeTab === 'all' || activeTab === 'certifications') && displayCerts.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-purple-400 text-xs font-bold uppercase tracking-wider">
              <Award className="w-4 h-4" />
              <span>Certifications & Licenses ({displayCerts.length})</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {displayCerts.map((cert, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1 hover:border-purple-500/30 transition-all">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white">
                      {cert.name}
                    </h4>
                    {cert.issue_date && (
                      <span className="text-[11px] text-slate-400 font-medium">
                        {cert.issue_date}
                      </span>
                    )}
                  </div>
                  {cert.issuer && (
                    <p className="text-xs font-semibold text-purple-300">
                      {cert.issuer}
                    </p>
                  )}
                  {cert.credential_id_or_url && (
                    <a 
                      href={cert.credential_id_or_url.startsWith('http') ? cert.credential_id_or_url : `https://${cert.credential_id_or_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 inline-flex items-center space-x-1 mt-0.5"
                    >
                      <span>Verify Credential</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 7. Achievements & Honors Part-wise */}
        {(activeTab === 'all' || activeTab === 'achievements') && displayAchievements.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
              <Trophy className="w-4 h-4 text-amber-400" />
              <span>Achievements, Honors & Hackathons ({displayAchievements.length})</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {displayAchievements.map((ach, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-1 relative pl-4 border-l-2 border-l-amber-400">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-amber-200">
                      {ach.title}
                    </h4>
                    {ach.year && (
                      <span className="text-[10px] font-semibold text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded">
                        {ach.year}
                      </span>
                    )}
                  </div>
                  {ach.issuer_or_event && (
                    <p className="text-xs font-medium text-amber-300/80">
                      {ach.issuer_or_event}
                    </p>
                  )}
                  {ach.description && ach.description !== ach.title && (
                    <p className="text-xs text-slate-300 leading-relaxed mt-1">
                      {ach.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 8. Languages & Activities Part-wise */}
        {(activeTab === 'all' || activeTab === 'languages_activities') && (
          displayLanguages.length > 0 || displayExtracurriculars.length > 0 || displayPublications.length > 0
        ) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Languages */}
            {displayLanguages.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-teal-400 text-xs font-bold uppercase tracking-wider">
                  <Globe2 className="w-4 h-4 text-teal-400" />
                  <span>Languages Known ({displayLanguages.length})</span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {displayLanguages.map((lang, idx) => (
                    <div 
                      key={idx} 
                      className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-800/50 border border-teal-500/20 text-xs"
                    >
                      <span className="font-semibold text-white">{lang.language}</span>
                      {lang.proficiency && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-300 font-medium">
                          {lang.proficiency}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracurriculars & Leadership */}
            {displayExtracurriculars.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
                  <Users2 className="w-4 h-4 text-cyan-400" />
                  <span>Leadership & Activities ({displayExtracurriculars.length})</span>
                </div>

                <div className="space-y-2">
                  {displayExtracurriculars.map((extra, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-white">{extra.role}</h4>
                        {extra.duration && (
                          <span className="text-[10px] text-slate-400">{extra.duration}</span>
                        )}
                      </div>
                      {extra.organization && (
                        <p className="text-xs text-cyan-300">{extra.organization}</p>
                      )}
                      {extra.description && (
                        <p className="text-xs text-slate-300 leading-relaxed">{extra.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Publications & Research */}
            {displayPublications.length > 0 && (
              <div className="space-y-3 md:col-span-2">
                <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold uppercase tracking-wider">
                  <BookOpen className="w-4 h-4 text-sky-400" />
                  <span>Publications & Research Papers ({displayPublications.length})</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {displayPublications.map((pub, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-white">{pub.title}</h4>
                        {pub.url_or_doi && (
                          <a 
                            href={pub.url_or_doi.startsWith('http') ? pub.url_or_doi : `https://${pub.url_or_doi}`} 
                            target="_blank" 
                            rel="noreferrer"
                            className="text-xs text-sky-400 hover:text-sky-300 inline-flex items-center space-x-1"
                          >
                            <span>Read</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                      {pub.authors_or_journal && (
                        <p className="text-xs text-sky-300">{pub.authors_or_journal}</p>
                      )}
                      {pub.date_or_year && (
                        <span className="text-[10px] text-slate-400">{pub.date_or_year}</span>
                      )}
                      {pub.description && (
                        <p className="text-xs text-slate-300 leading-relaxed mt-1">{pub.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
