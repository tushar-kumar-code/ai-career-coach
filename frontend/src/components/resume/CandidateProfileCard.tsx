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
  Layers
} from 'lucide-react';
import { ResumeAnalysisData } from '@/lib/types';

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
    if (headline && (lower === headline || lower.startsWith(headline + ' |'))) {
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

export default function CandidateProfileCard({ resumeData, compact = false }: CandidateProfileCardProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'about' | 'skills' | 'experience' | 'projects' | 'education'>('all');

  const about = resumeData.about_user || resumeData.contact_info;
  const skills = resumeData.extracted_skills || [];
  const experience = resumeData.experience || [];
  const projects = resumeData.projects || [];
  const education = resumeData.education || [];
  const certifications = resumeData.certifications || [];

  const cleanedSummary = cleanProfessionalSummary(about?.summary, about);

  // Group skills by category
  const skillsByCategory: Record<string, typeof skills> = {};
  skills.forEach((sk) => {
    const cat = sk.category || 'General';
    if (!skillsByCategory[cat]) skillsByCategory[cat] = [];
    skillsByCategory[cat].push(sk);
  });

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
            {[
              { id: 'all', label: 'Complete Overview', icon: Layers },
              { id: 'about', label: 'About & Summary', icon: User },
              { id: 'skills', label: `Skills (${skills.length})`, icon: Code2 },
              { id: 'experience', label: `Experience (${experience.length})`, icon: Briefcase },
              { id: 'projects', label: `Projects (${projects.length})`, icon: FolderGit2 },
              { id: 'education', label: `Education & Certs (${education.length + certifications.length})`, icon: GraduationCap },
            ].map((tab) => {
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
        {(activeTab === 'all' || activeTab === 'projects') && projects.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <FolderGit2 className="w-4 h-4" />
              <span>Projects & Portfolio ({projects.length})</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {projects.map((proj, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-800/30 border border-slate-800 space-y-2 flex flex-col justify-between">
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
                      <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
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

        {/* 5. Education & Certifications Part-wise */}
        {(activeTab === 'all' || activeTab === 'education') && (education.length > 0 || certifications.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {education.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
                  <GraduationCap className="w-4 h-4" />
                  <span>Education ({education.length})</span>
                </div>

                <div className="space-y-2.5">
                  {education.map((edu, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-white">
                          {edu.degree || 'Degree'}
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
                          Grade/GPA: {edu.grade}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {certifications.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-purple-400 text-xs font-bold uppercase tracking-wider">
                  <Award className="w-4 h-4" />
                  <span>Certifications ({certifications.length})</span>
                </div>

                <div className="space-y-2.5">
                  {certifications.map((cert, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1">
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
                          <span>Credential Link</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
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
