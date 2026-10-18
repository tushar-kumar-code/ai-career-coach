import {
  APIResponse,
  HealthStatus,
  AssessmentSession,
  AssessmentResultData,
  CareerRoleCatalogItem,
  DirectCareerGoalPayload,
  DirectCareerGoalResult,
  ResumeAnalysisData,
  BulletImprovement,
  ExtractedSkill,
  SkillProfileData,
  UserSkill,
  SkillGap,
  SkillDetailData,
  RoadmapData,
  RoadmapSkillRequest,
  FocusSkillResultData,
  DailyTasksData,
  RoadmapProgressData,
  RoadmapPhase,
  LevelTestResponse,
  LevelTestSubmitResponse,
  JobData,
  JobMatchAnalysis,
  SavedJobData,
  JobApplicationData,
  ApplicationHistoryItem,
  InterviewSessionData,
  InterviewEvaluationData,
  InterviewFinalReportData,
  InterviewReadinessData,
  PracticeSuggestion,
  RoadmapTaskLearningContent,
  PlacementChecklistData,
  StudentCareerBriefData,
  ChatResponseData,
  TestKeyResponseData,
  AIConfigStatusData,
  UserAuthData,
  AuthResponseData,
  AssessmentStatusData,
  SuggestedDomainsData,
  PracticeContextData,
  InteractiveDrillQuestion,
  DrillEvaluationData
} from './types';
import { terminalLogger } from './terminal-logger';

export function resolveApiBaseUrl(): string {
  let raw = (process.env.NEXT_PUBLIC_API_URL || '').trim();

  // If missing, or literally configured with placeholder like <backend-render-url>
  const isInvalidOrPlaceholder = !raw || raw.includes('<') || raw.includes('>') || raw.includes('backend-render-url');
  
  if (isInvalidOrPlaceholder) {
    if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
      raw = 'https://ai-career-coach-backend-qkha.onrender.com/api/v1';
    } else {
      raw = 'http://127.0.0.1:8000/api/v1';
    }
  }

  // Prepend https:// if protocol is missing (e.g. from Render property: host)
  if (!raw.startsWith('http://') && !raw.startsWith('https://')) {
    raw = `https://${raw}`;
  }

  return raw.endsWith('/api/v1') 
    ? raw.replace(/\/+$/, '') 
    : `${raw.replace(/\/+$/, '')}/api/v1`;
}

export const BASE_URL = resolveApiBaseUrl();

export function getSavedAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export async function getFreshAuthToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null;
  try {
    const { auth } = await import('./firebase');
    if (!auth.currentUser && typeof auth.authStateReady === 'function') {
      await auth.authStateReady();
    }
    if (auth?.currentUser) {
      const freshToken = await auth.currentUser.getIdToken();
      if (freshToken) {
        saveAuthToken(freshToken);
        return freshToken;
      }
    }
  } catch {}
  return getSavedAuthToken();
}

export function saveAuthToken(token: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('auth_token', token);
}

export function clearAuthToken() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  localStorage.removeItem('cached_resume_analysis');
}

export function getSavedAIConfig() {
  if (typeof window === 'undefined') return { provider: 'groq', apiKey: '', model: '' };
  return {
    provider: localStorage.getItem('ai_provider') || 'groq',
    apiKey: localStorage.getItem('ai_api_key') || '',
    model: localStorage.getItem('ai_model') || '',
  };
}

export function saveAIConfig(provider: string, apiKey: string, model?: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('ai_provider', provider);
  localStorage.setItem('ai_api_key', apiKey);
  if (model) {
    localStorage.setItem('ai_model', model);
  }
}

export function clearSavedAIConfig() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('ai_api_key');
  localStorage.removeItem('ai_provider');
  localStorage.removeItem('ai_model');
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const method = (options?.method || 'GET').toUpperCase();
  const startTime = Date.now();
  const isHealth = endpoint.includes('/health');

  if (!isHealth) {
    terminalLogger.api(`Starting ${method} ${endpoint}`);
  }

  const aiConfig = getSavedAIConfig();
  const token = await getFreshAuthToken();

  const customHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const lang = typeof window !== 'undefined' ? (localStorage.getItem('ai_career_language') || 'en') : 'en';
  customHeaders['X-Language-Preference'] = lang;
  customHeaders['Accept-Language'] = lang;

  if (token) {
    customHeaders['Authorization'] = `Bearer ${token}`;
  }

  if (aiConfig.apiKey) {
    customHeaders['X-AI-API-Key'] = aiConfig.apiKey;
    customHeaders['X-AI-Provider'] = aiConfig.provider;
    if (aiConfig.model) {
      customHeaders['X-AI-Model'] = aiConfig.model;
    }
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, {
      headers: {
        ...customHeaders,
        ...options?.headers,
      },
      ...options,
    });
  } catch (err: any) {
    const duration = Date.now() - startTime;
    terminalLogger.error(`Network Error ${method} ${endpoint} after ${duration}ms: ${err?.message || 'Connection failed'}`);
    if (err?.message === 'Failed to fetch' || err?.name === 'TypeError') {
      throw new Error(`Backend server is not reachable at ${BASE_URL}. Please ensure your backend is running.`);
    }
    throw err;
  }

  let result: any = null;
  try {
    result = await response.json();
  } catch (e) {
    result = null;
  }

  const duration = Date.now() - startTime;

  if (!response.ok || (result && result.success === false)) {
    const errorMsg =
      result?.detail ||
      result?.message ||
      result?.error ||
      `Server error (${response.status})`;
    const errorStr = typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg);
    terminalLogger.error(`Failed ${method} ${endpoint} (${response.status} in ${duration}ms): ${errorStr}`);
    throw new Error(errorStr);
  }

  if (!isHealth) {
    terminalLogger.api(`Success ${method} ${endpoint} (200 OK in ${duration}ms)`);
  }

  return (result?.data !== undefined ? result.data : result) as T;
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
export async function startAssessment(userLevel?: string): Promise<AssessmentSession> {
  return request<AssessmentSession>('/assessment/start', {
    method: 'POST',
    body: JSON.stringify({ user_level: userLevel || 'beginner', retake: false }),
    cache: 'no-store',
  });
}

export async function startAssessmentRetake(userLevel?: string): Promise<AssessmentSession> {
  return request<AssessmentSession>('/assessment/start', {
    method: 'POST',
    body: JSON.stringify({ user_level: userLevel || 'beginner', retake: true }),
    cache: 'no-store',
  });
}

export async function submitAnswer(
  sessionId: string,
  questionId: string,
  selectedOptionId: string,
  customAnswer?: string
): Promise<AssessmentSession> {
  return request<AssessmentSession>('/assessment/answer', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      selected_option_id: selectedOptionId,
      custom_answer: customAnswer || null,
    }),
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

export async function getSuggestedDomains(): Promise<SuggestedDomainsData | null> {
  try {
    return await request<SuggestedDomainsData>('/assessment/suggested-domains', { cache: 'no-store' });
  } catch (err) {
    return null;
  }
}

export async function getAssessmentStatus(): Promise<AssessmentStatusData> {
  try {
    return await request<AssessmentStatusData>('/assessment/status', { cache: 'no-store' });
  } catch (err) {
    return {
      has_completed_assessment: false,
      target_career: null,
      primary_archetype: null,
      job_readiness_score: 0,
    };
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

export async function submitDirectCareerGoal(payload: DirectCareerGoalPayload): Promise<DirectCareerGoalResult> {
  return request<DirectCareerGoalResult>('/assessment/direct-goal', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// Resume APIs
export async function uploadResumeFile(file: File, jobDescription?: string): Promise<ResumeAnalysisData> {
  const formData = new FormData();
  formData.append('file', file);
  if (jobDescription && jobDescription.trim().length >= 20) {
    formData.append('job_description', jobDescription.trim());
  }

  const token = await getFreshAuthToken();
  const aiConfig = getSavedAIConfig();
  const lang = typeof window !== 'undefined' ? (localStorage.getItem('ai_career_language') || 'en') : 'en';

  const customHeaders: Record<string, string> = {
    'X-Language-Preference': lang,
    'Accept-Language': lang,
  };

  if (token) {
    customHeaders['Authorization'] = `Bearer ${token}`;
  }

  if (aiConfig.apiKey) {
    customHeaders['X-AI-API-Key'] = aiConfig.apiKey;
    customHeaders['X-AI-Provider'] = aiConfig.provider;
    if (aiConfig.model) {
      customHeaders['X-AI-Model'] = aiConfig.model;
    }
  }

  const response = await fetch(`${BASE_URL}/resume/upload`, {
    method: 'POST',
    headers: customHeaders,
    body: formData,
  });

  let result: any = null;
  try {
    result = await response.json();
  } catch (e) {
    result = null;
  }

  if (!response.ok || (result && result.success === false)) {
    const errorMsg =
      result?.detail ||
      result?.message ||
      result?.error ||
      'Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye.';
    const errorStr = typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg);
    throw new Error(errorStr);
  }

  if (typeof window !== 'undefined' && result.data) {
    try {
      localStorage.setItem('cached_resume_analysis', JSON.stringify(result.data));
    } catch (e) {
      // ignore
    }
  }

  return result.data as ResumeAnalysisData;
}

export async function matchJobDescription(jobDescription: string): Promise<ResumeAnalysisData> {
  const result = await request<ResumeAnalysisData>('/resume/match-jd', {
    method: 'POST',
    body: JSON.stringify({ job_description: jobDescription }),
  });
  if (result && typeof window !== 'undefined') {
    try {
      localStorage.setItem('cached_resume_analysis', JSON.stringify(result));
    } catch (e) {
      // ignore
    }
  }
  return result;
}

export async function getResumeAnalysis(): Promise<ResumeAnalysisData | null> {
  try {
    const data = await request<ResumeAnalysisData>('/resume/analysis', { cache: 'no-store' });
    if (data && typeof window !== 'undefined') {
      try {
        localStorage.setItem('cached_resume_analysis', JSON.stringify(data));
      } catch (e) {
        // ignore
      }
    }
    return data;
  } catch (err) {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('cached_resume_analysis');
      if (cached) {
        try {
          return JSON.parse(cached) as ResumeAnalysisData;
        } catch (e) {
          // ignore
        }
      }
    }
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
  target_role?: string;
  career_goal?: string;
  track_pace?: string;
  target_phases_count?: number;
  domain_requirement?: string;
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
  target_role?: string;
  career_goal?: string;
  track_pace?: string;
  target_phases_count?: number;
  domain_requirement?: string;
}): Promise<RoadmapData> {
  return request<RoadmapData>('/roadmap/preferences', {
    method: 'PUT',
    body: JSON.stringify(prefs),
  });
}

export async function addCustomRoadmapPhase(data: {
  title: string;
  description?: string;
  topics?: string[];
  estimated_minutes?: number;
}): Promise<RoadmapData> {
  return request<RoadmapData>('/roadmap/phases/custom', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function generateLevelTest(phaseId: string): Promise<LevelTestResponse> {
  return request<LevelTestResponse>(`/roadmap/phases/${phaseId}/generate-test`, {
    method: 'POST',
  });
}

export async function submitLevelTest(
  phaseId: string,
  answers: Record<string, string>
): Promise<LevelTestSubmitResponse> {
  return request<LevelTestSubmitResponse>(`/roadmap/phases/${phaseId}/submit-test`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
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
  topic_focus?: string;
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


export async function focusSkillOnRoadmap(skillName: string): Promise<FocusSkillResultData> {
  return request<FocusSkillResultData>('/roadmap/focus-skill', {
    method: 'POST',
    body: JSON.stringify({ skill_name: skillName }),
  });
}

// Roadmap Skill Request & Ingestion APIs
export async function createRoadmapSkillRequest(
  skillName: string,
  source: string = 'Skill Matrix',
  priority: string = 'Medium'
): Promise<RoadmapSkillRequest> {
  return request<RoadmapSkillRequest>('/roadmap/requests', {
    method: 'POST',
    body: JSON.stringify({
      skill_name: skillName,
      source,
      priority,
    }),
  });
}

export async function getRoadmapSkillRequests(status: string = 'pending'): Promise<RoadmapSkillRequest[]> {
  try {
    return await request<RoadmapSkillRequest[]>(`/roadmap/requests?status=${status}`, { cache: 'no-store' });
  } catch (err) {
    console.warn('Failed to fetch roadmap skill requests:', err);
    return [];
  }
}

export async function acceptRoadmapSkillRequest(
  requestId: string,
  targetPhaseNumber?: number
): Promise<{ request_id: string; status: string; phase_number: number; phase_title: string; task_id: string; task_title: string; message?: string }> {
  return request(`/roadmap/requests/${requestId}/accept`, {
    method: 'POST',
    body: JSON.stringify({
      target_phase_number: targetPhaseNumber,
    }),
  });
}

export async function rejectRoadmapSkillRequest(
  requestId: string
): Promise<{ request_id: string; status: string }> {
  return request(`/roadmap/requests/${requestId}/reject`, {
    method: 'POST',
  });
}

// Phase 3 — Micro Practice & Learning Resource APIs
export async function getPracticeSuggestions(): Promise<PracticeSuggestion[]> {
  try {
    return await request<PracticeSuggestion[]>('/roadmap/practice/suggest', { cache: 'no-store' });
  } catch {
    return [];
  }
}

export async function getTaskLearningContent(taskId: string): Promise<RoadmapTaskLearningContent> {
  return request<RoadmapTaskLearningContent>(`/roadmap/tasks/${taskId}/learn`, { cache: 'no-store' });
}

export interface RoadmapAssistantRequest {
  message: string;
  history?: { role: string; content: string }[];
  current_phase_id?: string;
  current_task_id?: string;
}

export interface RoadmapAssistantResponse {
  response: string;
  provider: string;
  suggested_actions?: string[];
}

export async function askRoadmapAssistant(
  payload: RoadmapAssistantRequest
): Promise<RoadmapAssistantResponse> {
  return request<RoadmapAssistantResponse>('/roadmap/assistant', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getPracticeContext(): Promise<PracticeContextData> {
  return request<PracticeContextData>('/practice/context', { cache: 'no-store' });
}

export async function generatePracticeDrill(
  topic: string,
  difficulty = 'Intermediate',
  questionCount = 3
): Promise<InteractiveDrillQuestion[]> {
  return request<InteractiveDrillQuestion[]>('/practice/drill/generate', {
    method: 'POST',
    body: JSON.stringify({ topic, difficulty, question_count: questionCount }),
  });
}

export async function evaluatePracticeDrillQuestion(payload: {
  question_id: string;
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  user_answer: string;
}): Promise<DrillEvaluationData> {
  return request<DrillEvaluationData>('/practice/drill/evaluate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function startMicroPractice(topic: string, targetRole?: string): Promise<InterviewSessionData> {
  return request<InterviewSessionData>('/interview/start', {
    method: 'POST',
    body: JSON.stringify({
      mode: 'Mixed',
      target_role: targetRole || 'Software Developer',
      difficulty: 'Beginner',
      question_count: 3,
      topic_focus: topic,
    }),
  });
}

// Phase 4 — College Placement Readiness & Student Brief APIs
export async function getPlacementChecklist(): Promise<PlacementChecklistData> {
  return request<PlacementChecklistData>('/placement/checklist', { cache: 'no-store' });
}

export async function getStudentCareerBrief(): Promise<StudentCareerBriefData> {
  return request<StudentCareerBriefData>('/placement/brief', { cache: 'no-store' });
}

// AI Career Coach Chat API
export async function sendChatMessage(
  message: string,
  history?: Array<{ role: 'user' | 'assistant' | 'ai'; content: string }>,
  targetRole?: string
): Promise<ChatResponseData> {
  return request<ChatResponseData>('/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      history,
      target_role: targetRole,
    }),
  });
}

// AI Configuration & Key Testing APIs
export async function testApiKey(
  provider: string,
  apiKey: string,
  model?: string
): Promise<TestKeyResponseData> {
  return request<TestKeyResponseData>('/settings/test-key', {
    method: 'POST',
    body: JSON.stringify({
      provider,
      api_key: apiKey,
      model,
    }),
  });
}

export async function getAIConfigStatus(): Promise<AIConfigStatusData> {
  return request<AIConfigStatusData>('/settings/ai-config', { cache: 'no-store' });
}

// User Authentication APIs
export async function loginUser(email: string, password: string): Promise<AuthResponseData> {
  const result = await request<AuthResponseData>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (result.access_token) {
    saveAuthToken(result.access_token);
    if (typeof window !== 'undefined' && result.user) {
      localStorage.setItem('auth_user', JSON.stringify(result.user));
    }
  }
  return result;
}

export async function registerUser(email: string, password: string, fullName?: string): Promise<AuthResponseData> {
  const result = await request<AuthResponseData>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (result.access_token) {
    saveAuthToken(result.access_token);
    if (typeof window !== 'undefined' && result.user) {
      localStorage.setItem('auth_user', JSON.stringify(result.user));
    }
  }
  return result;
}

export async function demoLoginUser(): Promise<AuthResponseData> {
  const result = await request<AuthResponseData>('/auth/demo-login', {
    method: 'POST',
  });
  if (result.access_token) {
    saveAuthToken(result.access_token);
    if (typeof window !== 'undefined' && result.user) {
      localStorage.setItem('auth_user', JSON.stringify(result.user));
    }
  }
  return result;
}

export async function getMe(): Promise<UserAuthData> {
  return request<UserAuthData>('/auth/me', { cache: 'no-store' });
}

export async function notifyLoginEvent(): Promise<void> {
  try {
    await request('/auth/login-notify', { method: 'POST' });
  } catch {}
}

export async function resetPassword(email: string, newPassword: string): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ email, new_password: newPassword }),
  });
}

// 2FA / OTP APIs
export async function sendOtp(email: string, purpose: 'login' | 'reset' = 'login'): Promise<{ email: string; message: string; dev_code?: string }> {
  return request<{ email: string; message: string; dev_code?: string }>('/auth/send-otp', {
    method: 'POST',
    body: JSON.stringify({ email, purpose }),
  });
}

export async function verifyOtpLogin(email: string, otp: string): Promise<AuthResponseData> {
  const result = await request<AuthResponseData>('/auth/verify-otp-login', {
    method: 'POST',
    body: JSON.stringify({ email, otp }),
  });
  if (result.access_token) {
    saveAuthToken(result.access_token);
    if (typeof window !== 'undefined' && result.user) {
      localStorage.setItem('auth_user', JSON.stringify(result.user));
    }
  }
  return result;
}

export async function verifyOtpReset(email: string, otp: string, newPassword: string): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>('/auth/verify-otp-reset', {
    method: 'POST',
    body: JSON.stringify({ email, otp, new_password: newPassword }),
  });
}




