import {
  APIResponse,
  HealthStatus,
  AssessmentSession,
  AssessmentResultData,
  CareerRoleCatalogItem,
  ResumeAnalysisData,
  BulletImprovement,
  ExtractedSkill,
  SkillProfileData,
  UserSkill,
  SkillGap,
  SkillDetailData,
  RoadmapData,
  DailyTasksData,
  RoadmapProgressData,
  RoadmapPhase,
  JobData,
  JobMatchAnalysis,
  SavedJobData,
  JobApplicationData,
  ApplicationHistoryItem,
  InterviewSessionData,
  InterviewEvaluationData,
  InterviewFinalReportData,
  InterviewReadinessData
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  const result: APIResponse<T> = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || result.error || `HTTP error ${response.status}`);
  }
  return result.data as T;
}

export async function fetchHealthStatus(): Promise<HealthStatus> {
  try {
    return await request<HealthStatus>('/health', { cache: 'no-store' });
  } catch (error) {
    console.error('API Client health error:', error);
    return {
      status: 'error',
      version: '1.0.0',
      environment: 'offline',
      database: 'disconnected',
      ai_provider: 'unavailable',
    };
  }
}

// Assessment APIs
export async function startAssessment(): Promise<AssessmentSession> {
  return request<AssessmentSession>('/assessment/start', { method: 'POST', cache: 'no-store' });
}

export async function submitAnswer(sessionId: string, questionId: string, selectedOptionId: string): Promise<AssessmentSession> {
  return request<AssessmentSession>('/assessment/answer', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, question_id: questionId, selected_option_id: selectedOptionId }),
  });
}

export async function completeAssessment(sessionId: string): Promise<any> {
  return request<any>(`/assessment/complete?session_id=${sessionId}`, { method: 'POST' });
}

export async function getAssessmentResult(): Promise<AssessmentResultData | null> {
  try {
    return await request<AssessmentResultData>('/assessment/result', { cache: 'no-store' });
  } catch (err) {
    return null;
  }
}

export async function getCareerCatalog(): Promise<CareerRoleCatalogItem[]> {
  return request<CareerRoleCatalogItem[]>('/assessment/careers');
}

export async function getCareerDetails(slug: string): Promise<CareerRoleCatalogItem> {
  return request<CareerRoleCatalogItem>(`/assessment/careers/${slug}`);
}

export async function selectTargetCareer(slug: string): Promise<{ target_career: string; slug: string }> {
  return request<{ target_career: string; slug: string }>('/assessment/target-career', {
    method: 'POST',
    body: JSON.stringify({ career_slug: slug }),
  });
}

// Resume APIs
export async function uploadResumeFile(file: File): Promise<ResumeAnalysisData> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/resume/upload`, {
    method: 'POST',
    body: formData,
  });

  const result: APIResponse<ResumeAnalysisData> = await response.json();
  if (!response.ok || !result.success) {
    throw new Error(result.message || result.error || 'Failed to upload and analyze resume');
  }
  return result.data as ResumeAnalysisData;
}

export async function getResumeAnalysis(): Promise<ResumeAnalysisData | null> {
  try {
    return await request<ResumeAnalysisData>('/resume/analysis', { cache: 'no-store' });
  } catch (err) {
    return null;
  }
}

export async function getResumeImprovements(): Promise<BulletImprovement[]> {
  return request<BulletImprovement[]>('/resume/improve', { method: 'POST' });
}

export async function getResumeSkills(): Promise<ExtractedSkill[]> {
  return request<ExtractedSkill[]>('/resume/skills');
}

// Skill Intelligence APIs
export async function getSkillProfile(): Promise<SkillProfileData> {
  return request<SkillProfileData>('/skills/profile', { cache: 'no-store' });
}

export async function getSkillGaps(): Promise<SkillGap[]> {
  return request<SkillGap[]>('/skills/gaps', { cache: 'no-store' });
}

export async function getRecommendedSkills(): Promise<UserSkill[]> {
  return request<UserSkill[]>('/skills/recommended', { cache: 'no-store' });
}

export async function getSkillDetails(skillId: string): Promise<SkillDetailData> {
  return request<SkillDetailData>(`/skills/${skillId}`, { cache: 'no-store' });
}

export async function recalculateSkills(): Promise<SkillProfileData> {
  return request<SkillProfileData>('/skills/recalculate', { method: 'POST' });
}

// Roadmap System APIs
export async function getCurrentRoadmap(): Promise<RoadmapData | null> {
  try {
    return await request<RoadmapData>('/roadmap/current', { cache: 'no-store' });
  } catch (err) {
    return null;
  }
}

export async function generateRoadmap(params?: {
  user_level?: string;
  hours_per_day?: number;
  days_per_week?: number;
  preferred_learning_style?: string;
  target_career_id?: string;
}): Promise<RoadmapData> {
  return request<RoadmapData>('/roadmap/generate', {
    method: 'POST',
    body: JSON.stringify(params || {}),
  });
}

export async function getTodayTasks(): Promise<DailyTasksData> {
  return request<DailyTasksData>('/roadmap/today', { cache: 'no-store' });
}

export async function completeRoadmapTask(taskId: string): Promise<RoadmapProgressData> {
  return request<RoadmapProgressData>(`/roadmap/tasks/${taskId}/complete`, {
    method: 'POST',
  });
}

export async function uncompleteRoadmapTask(taskId: string): Promise<RoadmapProgressData> {
  return request<RoadmapProgressData>(`/roadmap/tasks/${taskId}/uncomplete`, {
    method: 'POST',
  });
}

export async function recalculateRoadmap(): Promise<RoadmapData> {
  return request<RoadmapData>('/roadmap/recalculate', { method: 'POST' });
}

export async function updateRoadmapPreferences(prefs: {
  hours_per_day: number;
  days_per_week: number;
  preferred_learning_style: string;
  user_level: string;
}): Promise<RoadmapData> {
  return request<RoadmapData>('/roadmap/preferences', {
    method: 'PUT',
    body: JSON.stringify(prefs),
  });
}

// Job Intelligence System APIs
export async function searchJobs(params?: {
  query?: string;
  location?: string;
  remote_only?: boolean;
  experience_level?: string;
}): Promise<JobData[]> {
  const queryParams = new URLSearchParams();
  if (params?.query) queryParams.append('query', params.query);
  if (params?.location) queryParams.append('location', params.location);
  if (params?.remote_only !== undefined) queryParams.append('remote_only', String(params.remote_only));
  if (params?.experience_level) queryParams.append('experience_level', params.experience_level);

  const url = `/jobs/search${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return request<JobData[]>(url, { cache: 'no-store' });
}

export async function getRecommendedJobs(): Promise<JobMatchAnalysis[]> {
  return request<JobMatchAnalysis[]>('/jobs/recommended', { cache: 'no-store' });
}

export async function getSavedJobs(): Promise<SavedJobData[]> {
  return request<SavedJobData[]>('/jobs/saved', { cache: 'no-store' });
}

export async function getJobDetails(jobId: string): Promise<JobData> {
  return request<JobData>(`/jobs/${jobId}`, { cache: 'no-store' });
}

export async function getJobMatchAnalysis(jobId: string): Promise<JobMatchAnalysis> {
  return request<JobMatchAnalysis>(`/jobs/${jobId}/match`, { cache: 'no-store' });
}

export async function saveJob(jobId: string, notes?: string): Promise<SavedJobData> {
  const query = notes ? `?notes=${encodeURIComponent(notes)}` : '';
  return request<SavedJobData>(`/jobs/${jobId}/save${query}`, { method: 'POST' });
}

export async function deleteSavedJob(jobId: string): Promise<boolean> {
  return request<boolean>(`/jobs/${jobId}/save`, { method: 'DELETE' });
}

export async function getUserApplications(statusFilter?: string): Promise<JobApplicationData[]> {
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
  return request<JobApplicationData[]>(`/jobs/applications/all${query}`, { cache: 'no-store' });
}

export async function createJobApplication(data: {
  job_id: string;
  status?: string;
  applied_date?: string;
  interview_date?: string;
  notes?: string;
  source_url?: string;
}): Promise<JobApplicationData> {
  return request<JobApplicationData>('/jobs/applications', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateJobApplication(
  applicationId: string,
  data: {
    status?: string;
    applied_date?: string;
    interview_date?: string;
    notes?: string;
  }
): Promise<JobApplicationData> {
  return request<JobApplicationData>(`/jobs/applications/${applicationId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteJobApplication(applicationId: string): Promise<boolean> {
  return request<boolean>(`/jobs/applications/${applicationId}`, { method: 'DELETE' });
}

export async function getApplicationHistory(applicationId: string): Promise<ApplicationHistoryItem[]> {
  return request<ApplicationHistoryItem[]>(`/jobs/applications/${applicationId}/history`, { cache: 'no-store' });
}

// AI Mock Interview System APIs
export async function startInterviewSession(params: {
  mode: string;
  target_role?: string;
  difficulty?: string;
  question_count?: number;
  job_id?: string;
}): Promise<InterviewSessionData> {
  return request<InterviewSessionData>('/interview/start', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getInterviewSession(sessionId: string): Promise<InterviewSessionData> {
  return request<InterviewSessionData>(`/interview/session/${sessionId}`, { cache: 'no-store' });
}

export async function submitInterviewAnswer(sessionId: string, answerText: string): Promise<InterviewEvaluationData> {
  return request<InterviewEvaluationData>(`/interview/session/${sessionId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer_text: answerText }),
  });
}

export async function nextInterviewQuestion(sessionId: string): Promise<InterviewSessionData> {
  return request<InterviewSessionData>(`/interview/session/${sessionId}/next`, { method: 'POST' });
}

export async function completeInterviewSession(sessionId: string): Promise<InterviewFinalReportData> {
  return request<InterviewFinalReportData>(`/interview/session/${sessionId}/complete`, { method: 'POST' });
}

export async function getInterviewHistory(): Promise<InterviewSessionData[]> {
  return request<InterviewSessionData[]>('/interview/history', { cache: 'no-store' });
}

export async function getInterviewResults(sessionId: string): Promise<InterviewFinalReportData> {
  return request<InterviewFinalReportData>(`/interview/session/${sessionId}/results`, { cache: 'no-store' });
}

export async function getInterviewReadiness(): Promise<InterviewReadinessData> {
  return request<InterviewReadinessData>('/interview/readiness', { cache: 'no-store' });
}
