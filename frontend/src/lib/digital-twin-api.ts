/**
 * Digital Twin API Client
 * =======================
 * All TypeScript API functions for the Career Digital Twin + Progress Engine.
 * Follows existing api-client.ts pattern (request helper + base URL).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const result = await res.json();
  if (!result.success) {
    throw new Error(result.message || result.error || 'Digital twin request failed');
  }
  return result.data as T;
}

import type {
  CareerDigitalTwinData,
  ReadinessScoreData,
  ReadinessSnapshotData,
  GapAnalysisData,
  NextBestAction,
  UserAchievementData,
  WeeklyCareerReportData,
} from './types';

const DT_BASE = '/digital-twin';

/** Get the full Career Digital Twin profile (all sub-scores, gaps, next action). */
export async function getDigitalTwinProfile(): Promise<CareerDigitalTwinData> {
  return request<CareerDigitalTwinData>(`${DT_BASE}/profile`, { cache: 'no-store' });
}

/** Get the current career readiness scores only (lightweight). */
export async function getReadinessScore(): Promise<ReadinessScoreData> {
  return request<ReadinessScoreData>(`${DT_BASE}/readiness`, { cache: 'no-store' });
}

/** Get historical daily readiness snapshots (last 30 days). */
export async function getReadinessHistory(): Promise<ReadinessSnapshotData[]> {
  return request<ReadinessSnapshotData[]>(`${DT_BASE}/readiness/history`, { cache: 'no-store' });
}

/** Get prioritized career gap analysis. */
export async function getGapAnalysis(): Promise<GapAnalysisData> {
  return request<GapAnalysisData>(`${DT_BASE}/gaps`, { cache: 'no-store' });
}

/** Get the single best next action recommendation. */
export async function getNextBestAction(): Promise<NextBestAction> {
  return request<NextBestAction>(`${DT_BASE}/next-action`, { cache: 'no-store' });
}

/** Get all earned achievements. */
export async function getAchievements(): Promise<UserAchievementData[]> {
  return request<UserAchievementData[]>(`${DT_BASE}/achievements`, { cache: 'no-store' });
}

/** Get the weekly career progress report. */
export async function getWeeklyReport(): Promise<WeeklyCareerReportData> {
  return request<WeeklyCareerReportData>(`${DT_BASE}/weekly-report`, { cache: 'no-store' });
}

/** Manually save a readiness snapshot for today. */
export async function saveReadinessSnapshot(): Promise<{ snapshot_date: string; overall_readiness_score: number }> {
  return request(`${DT_BASE}/snapshot`, { method: 'POST' });
}
