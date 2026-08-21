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
  proficiency_level: string;
  confidence_score: number;
  confidence_status: string;
  target_required_level?: string;
  gap_status: string;
  priority: string;
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

// ----------------------------------------------------
// Roadmap System Types
// ----------------------------------------------------

export interface RoadmapTask {
  id: string;
  title: string;
  skill: string;
  estimated_minutes: number;
  why_matters: string;
  practice_activity: string;
  completed: boolean;
  completed_at?: string;
}

export interface RoadmapProject {
  id: string;
  title: string;
  objective: string;
  skills_practiced: string[];
  difficulty: string;
  expected_outcome: string;
  resume_relevance: string;
  completed: boolean;
}

export interface RoadmapMilestone {
  id: string;
  title: string;
  criteria: string;
  completed: boolean;
}

export interface RoadmapSkillItem {
  name: string;
  status: string;
  priority: string;
  level: string;
}

export interface RoadmapPhase {
  phase_id: string;
  name: string;
  description: string;
  estimated_weeks: number;
  skills: RoadmapSkillItem[];
  learning_objectives: string[];
  tasks: RoadmapTask[];
  projects: RoadmapProject[];
  milestones: RoadmapMilestone[];
}

export interface RoadmapData {
  id: string;
  user_id: string;
  target_career_id?: string;
  target_role: string;
  user_level: string;
  overall_progress_percent: number;
  is_active: boolean;
  is_outdated: boolean;
  hours_per_day: number;
  days_per_week: number;
  preferred_learning_style: string;
  total_estimated_weeks: number;
  phases: RoadmapPhase[];
  completed_task_ids: string[];
  completed_milestone_ids: string[];
  completed_project_ids: string[];
}

export interface DailyTasksData {
  roadmap_id: string;
  target_role: string;
  current_phase_name: string;
  hours_budget: number;
  today_focus_title: string;
  why_it_matters: string;
  tasks: RoadmapTask[];
}

export interface RoadmapProgressData {
  roadmap_id: string;
  target_role: string;
  overall_progress_percent: number;
  completed_tasks_count: number;
  total_tasks_count: number;
  completed_projects_count: number;
  total_projects_count: number;
  completed_milestones_count: number;
  total_milestones_count: number;
  is_outdated: boolean;
}

// ----------------------------------------------------
// Job Intelligence System Types
// ----------------------------------------------------

export interface JobData {
  id: string;
  provider_id?: string;
  provider_name: string;
  title: string;
  company: string;
  location: string;
  is_remote: boolean;
  employment_type: string;
  experience_level: string;
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  education_requirements: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;
  source_url?: string;
  posted_date?: string;
  is_saved?: boolean;
  application_status?: string;
}

export interface JobMatchBreakdown {
  overall_score: number;
  skill_score: number;
  career_alignment_score: number;
  resume_score: number;
  experience_score: number;
  roadmap_score: number;
  readiness_status: string; // READY, NEARLY READY, NEEDS SKILL DEVELOPMENT, LOW MATCH
  readiness_explanation: string;
}

export interface RoadmapGapConnection {
  skill_name: string;
  gap_level: string;
  roadmap_phase: string;
  estimated_weeks: number;
  match_boost_percent: number;
}

export interface JobMatchAnalysis {
  job: JobData;
  match_breakdown: JobMatchBreakdown;
  matching_skills: string[];
  missing_skills: string[];
  strong_matches_explanation: string[];
  missing_gaps_explanation: string[];
  roadmap_connections: RoadmapGapConnection[];
  recommendation: string;
}

export interface SavedJobData {
  id: string;
  user_id: string;
  job_id: string;
  notes?: string;
  saved_at: string;
  job: JobData;
}

export interface JobApplicationData {
  id: string;
  user_id: string;
  job_id: string;
  job_title: string;
  company: string;
  location: string;
  status: string; // Saved, Applied, Assessment, Interview, Offer, Rejected, Withdrawn
  applied_date?: string;
  interview_date?: string;
  notes?: string;
  source_url?: string;
  match_percentage: number;
  readiness_status: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationHistoryItem {
  id: string;
  application_id: string;
  from_status?: string;
  to_status: string;
  changed_at: string;
  notes?: string;
}

// ----------------------------------------------------
// AI Mock Interview Engine Types
// ----------------------------------------------------

export interface STARAnalysisData {
  situation_feedback?: string;
  task_feedback?: string;
  action_feedback?: string;
  result_feedback?: string;
  star_complete: boolean;
}

export interface InterviewEvaluationData {
  score: number;
  technical_score: number;
  communication_score: number;
  problem_solving_score: number;
  behavioral_score: number;
  resume_knowledge_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_points: string[];
  suggested_improvement: string;
  ideal_answer_outline: string[];
  star_analysis?: STARAnalysisData;
  detected_weak_topic?: string;
}

export interface InterviewQuestionItem {
  question_index: number;
  category: string;
  difficulty: string;
  question_text: string;
  context_tip?: string;
  user_answer?: string;
  score?: number;
  evaluation?: InterviewEvaluationData;
}

export interface InterviewSessionData {
  id: string;
  user_id: string;
  job_id?: string;
  target_role: string;
  mode: string; // Technical, HR, Behavioral, Resume-Based, Job-Specific, Mixed
  difficulty: string; // Beginner, Intermediate, Advanced
  question_count: number;
  current_question_index: number;
  is_completed: boolean;
  current_question?: InterviewQuestionItem;
  overall_score: number;
  category_scores: Record<string, number>;
  readiness_status: string; // EXCELLENT, READY, NEARLY READY, NEEDS PRACTICE
  readiness_explanation?: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewFinalReportData {
  session_id: string;
  target_role: string;
  mode: string;
  difficulty: string;
  overall_score: number;
  technical_score: number;
  communication_score: number;
  problem_solving_score: number;
  behavioral_score: number;
  resume_knowledge_score: number;
  readiness_status: string;
  readiness_explanation: string;
  strong_areas: string[];
  weak_areas: string[];
  recommended_roadmap_topics: string[];
  questions_review: InterviewQuestionItem[];
}

export interface InterviewReadinessData {
  overall_readiness_status: string;
  average_score: number;
  total_interviews_completed: number;
  strongest_mode: string;
  weakest_topic?: string;
  recommendation: string;
}

// ----------------------------------------------------
// Career Digital Twin + Progress & Readiness Engine Types
// ----------------------------------------------------

export interface ReadinessSubScores {
  skill_readiness: number;
  resume_readiness: number;
  interview_readiness: number;
  roadmap_progress: number;
  job_match_readiness: number;
  portfolio_readiness: number;
}

export interface CareerStrength {
  name: string;
  category: string;
  proficiency: number;
  level: string;
  verified: boolean;
}

export interface CareerGap {
  area: string;
  name: string;
  category: string;
  priority: string; // Critical, High, Medium, Low
  current_level: string;
  required_level: string;
  reason: string;
  source: string;
}

export interface NextBestAction {
  action_type: string;
  title: string;
  description: string;
  why_it_matters: string;
  expected_impact: string;
  related_goal: string;
  action_link: string;
  impact_level: string; // critical, high, medium, low
  specific_item?: Record<string, string> | null;
  current_sub_score?: number;
}

export interface CareerDigitalTwinData {
  user_id: string;
  overall_readiness_score: number;
  readiness_label: string;
  sub_scores: ReadinessSubScores;
  target_career?: string;
  primary_archetype?: string;
  experience_level: string;
  top_strengths: CareerStrength[];
  priority_gaps: CareerGap[];
  critical_missing_skills: string[];
  next_action: NextBestAction;
  evidence_summary: Record<string, unknown>;
  last_computed_at?: string;
  snapshot_date?: string;
  achievements?: UserAchievementData[];
  gaps?: GapAnalysisData;
}

export interface ReadinessScoreData {
  overall_readiness_score: number;
  readiness_label: string;
  skill_readiness: number;
  resume_readiness: number;
  interview_readiness: number;
  roadmap_progress: number;
  job_match_readiness: number;
  portfolio_readiness: number;
  evidence_summary: Record<string, unknown>;
  weights: Record<string, number>;
}

export interface ReadinessSnapshotData {
  date: string;
  overall: number;
  skill: number;
  resume: number;
  interview: number;
  roadmap: number;
  job_match: number;
  portfolio: number;
}

export interface GapAnalysisData {
  top_strengths: CareerStrength[];
  priority_gaps: CareerGap[];
  critical_missing_skills: string[];
  total_gaps_found: number;
  total_strengths_found: number;
}

export interface UserAchievementData {
  achievement_key: string;
  title: string;
  description: string;
  icon: string;
  category: string;
  evidence_description?: string;
  earned_at: string;
}

export interface WeeklyReportScoreChanges {
  overall_delta: number;
  skill_delta: number;
  resume_delta: number;
  interview_delta: number;
  roadmap_delta: number;
}

export interface WeeklyReportActivity {
  interviews_completed: number;
  applications_submitted: number;
  skills_verified: number;
}

export interface WeeklyCareerReportData {
  week_start_date: string;
  week_end_date: string;
  score_changes: WeeklyReportScoreChanges;
  activity: WeeklyReportActivity;
  improvements: string[];
  achievements_earned_this_week: UserAchievementData[];
  biggest_weakness?: string;
  recommended_focus?: string;
  current_scores: {
    overall: number;
    skill: number;
    resume: number;
    interview: number;
    roadmap: number;
    job_match: number;
    portfolio: number;
  };
}
