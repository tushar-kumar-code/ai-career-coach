export interface APIResponse<T> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  database: string;
  ai_provider: string;
}

// ----------------------------------------------------
// Career Discovery Assessment Types
// ----------------------------------------------------

export interface QuestionOption {
  id: string;
  text: string;
  archetype?: string;
}

export interface Question {
  id: string;
  dimension: string;
  question_type: string;
  question_text: string;
  options: QuestionOption[];
  order_index: number;
}

export interface AssessmentSession {
  session_id: string;
  current_step: number;
  total_questions: number;
  is_completed: boolean;
  current_question?: Question;
  answers_count: number;
}

export interface SupportedStrength {
  strength_name: string;
  evidence_reason: string;
}

export interface CareerMatch {
  slug: string;
  title: string;
  match_percentage: number;
  confidence_percentage: number;
  why_recommended: string[];
  supporting_strengths: string[];
  potential_challenges: string[];
  learning_gaps: string[];
}

export interface CareerDiscoveryAIAnalysis {
  primary_archetype: string;
  top_strengths: SupportedStrength[];
  interest_profile: string[];
  work_style_summary: string;
  motivation_profile: string;
  recommended_careers: CareerMatch[];
  alternative_careers: string[];
}

export interface AssessmentResultData {
  session_id: string;
  selected_target_career?: string;
  archetype: string;
  analysis: CareerDiscoveryAIAnalysis;
  completed_at?: string;
}

export interface CareerRoleCatalogItem {
  id: string;
  slug: string;
  title: string;
  description: string;
  difficulty_level: string;
  required_skills: string[];
  preferred_strengths: string[];
  interest_areas: string[];
  work_style: string;
  responsibilities: string[];
  learning_areas: string[];
}

// ----------------------------------------------------
// Resume Intelligence Types
// ----------------------------------------------------

export interface ATSBreakdown {
  overall_ats_score: number;
  formatting_score: number;
  keyword_score: number;
  skills_score: number;
  experience_score: number;
  readability_score: number;
}

export interface TargetCareerMatch {
  target_career_name: string;
  match_percentage: number;
  matching_skills: string[];
  missing_skills: string[];
  experience_alignment: string;
  recommendation: string;
}

export interface ParsedContactInfo {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
  portfolio: string;
}

export interface ExtractedSkill {
  name: string;
  category: string;
  proficiency_estimated: number;
  source: string;
  confidence_level: string;
}

export interface BulletImprovement {
  original_text: string;
  improved_text: string;
  explanation: string;
}

export interface ResumeAnalysisData {
  id: string;
  filename: string;
  ats_score: number;
  ats_breakdown: ATSBreakdown;
  target_match: TargetCareerMatch;
  contact_info: ParsedContactInfo;
  extracted_skills: ExtractedSkill[];
  formatting_risk_flags: string[];
  improvement_suggestions: BulletImprovement[];
}

// ----------------------------------------------------
// Skill Intelligence Types
// ----------------------------------------------------

export interface UserSkill {
  id: string;
  skill_name: string;
  normalized_name: string;
  category: string;
  proficiency_percent: number;
  proficiency_level: string; // Beginner, Intermediate, Advanced
  confidence_score: number;
  confidence_status: string; // Claimed, Supported, Verified
  target_required_level?: string;
  gap_status: string; // Matched, Partially Matched, Missing, Weak
  priority: string; // High, Medium, Low
  priority_reason?: string;
  evidence_sources: string[];
  last_evaluated_at?: string;
}

export interface SkillGap {
  skill_name: string;
  category: string;
  current_proficiency: string;
  required_proficiency: string;
  gap_status: string;
  priority: string;
  priority_reason: string;
}

export interface SkillEvidence {
  id: string;
  source: string;
  description: string;
  confidence_weight: number;
  evidence_date?: string;
}

export interface SkillProfileData {
  user_id: string;
  target_career: string;
  total_skills_count: number;
  verified_count: number;
  supported_count: number;
  claimed_count: number;
  strong_skills: UserSkill[];
  skills_to_improve: UserSkill[];
  missing_skills: SkillGap[];
  recommended_next_skills: UserSkill[];
}

export interface SkillDetailData {
  skill: UserSkill;
  evidence_records: SkillEvidence[];
  target_career_requirement: string;
  recommended_next_action: string;
}
