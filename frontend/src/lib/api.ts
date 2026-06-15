// src/lib/api.ts — Typed API client for all GitGaze v1 endpoints
import type {
  Project,
  ProjectsListResponse,
  AnalysisConfig,
  Snapshot,
  CreateSnapshotResponse,
  GraphData,
} from '../types';

const BASE = 'http://localhost:8000/api/v1';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const authApi = {
  getMe: (): Promise<{ id: string; username: string; avatar_url: string }> =>
    request(`${BASE}/auth/me`),
  logout: (): Promise<void> =>
    request(`${BASE}/auth/logout`, { method: 'POST' }),
};

// ---------------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------------
export const projectsApi = {
  list: (): Promise<ProjectsListResponse> =>
    request(`${BASE}/projects`),

  create: (name: string, github_url: string): Promise<Project> =>
    request(`${BASE}/projects`, {
      method: 'POST',
      body: JSON.stringify({ name, github_url }),
    }),

  get: (id: string): Promise<Project> =>
    request(`${BASE}/projects/${id}`),

  delete: (id: string): Promise<void> =>
    request(`${BASE}/projects/${id}`, { method: 'DELETE' }),

  deleteAll: (): Promise<void> =>
    request(`${BASE}/projects`, { method: 'DELETE' }),

  updateConfig: (id: string, config: Partial<AnalysisConfig>): Promise<AnalysisConfig> =>
    request(`${BASE}/projects/${id}/config`, {
      method: 'PATCH',
      body: JSON.stringify(config),
    }),
};

// ---------------------------------------------------------------------------
// Snapshots
// ---------------------------------------------------------------------------
export const snapshotsApi = {
  create: (projectId: string): Promise<CreateSnapshotResponse> =>
    request(`${BASE}/projects/${projectId}/snapshots`, { method: 'POST' }),

  list: (projectId: string): Promise<{ snapshots: Snapshot[]; total: number }> =>
    request(`${BASE}/projects/${projectId}/snapshots`),

  get: (snapshotId: string): Promise<Snapshot> =>
    request(`${BASE}/snapshots/${snapshotId}`),

  getGraph: (snapshotId: string): Promise<GraphData> =>
    request(`${BASE}/snapshots/${snapshotId}/graph`),

  savePositions: (
    snapshotId: string,
    positions: Record<string, { x: number; y: number }>
  ): Promise<{ updated: number }> =>
    request(`${BASE}/snapshots/${snapshotId}/graph/positions`, {
      method: 'PATCH',
      body: JSON.stringify(positions),
    }),

  getSummary: (snapshotId: string, nodeId: string, detailLevel: string = 'concise'): Promise<{ summary: string; cached: boolean }> =>
    request(`${BASE}/snapshots/${snapshotId}/nodes/${nodeId}/summary?detail_level=${detailLevel}`),

  /**
   * Returns a native EventSource for the SSE progress stream.
   * Caller is responsible for calling .close() when done.
   */
  progressStream: (snapshotId: string): EventSource =>
    new EventSource(`http://localhost:8000/api/v1/snapshots/${snapshotId}/progress`),
};

// ---------------------------------------------------------------------------
// TanStack Query keys (centralised so invalidations stay in sync)
// ---------------------------------------------------------------------------
export const queryKeys = {
  projects: () => ['projects'] as const,
  project: (id: string) => ['projects', id] as const,
  snapshots: (projectId: string) => ['snapshots', projectId] as const,
  snapshot: (id: string) => ['snapshot', id] as const,
  graph: (snapshotId: string) => ['graph', snapshotId] as const,
};
