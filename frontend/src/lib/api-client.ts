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
  SkillDetailData
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
