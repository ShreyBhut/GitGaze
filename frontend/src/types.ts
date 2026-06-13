// src/types.ts — Shared TypeScript types for GitGaze frontend

export interface Project {
  id: string;
  name: string;
  path: string;
  created_at: string;
  latest_snapshot: SnapshotSummary | null;
  config?: AnalysisConfig;
}

export interface SnapshotSummary {
  id: string;
  status: SnapshotStatus;
  created_at: string;
  completed_at: string | null;
}

export type SnapshotStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Snapshot {
  id: string;
  project_id: string;
  status: SnapshotStatus;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  file_count?: number;
}

export interface AnalysisConfig {
  excluded_dirs: string[];
  enabled_languages: string[];
  max_file_size_kb: number;
}

export interface FileNode {
  id: string;
  file_path: string;
  node_type: 'file' | 'dir';
  language: string | null;
  metrics: {
    loc: number;
    sloc: number;
    comments: number;
    blanks: number;
  };
  imports: string[];
  functions: Array<{ name: string; start_line: number; end_line: number }>;
}

export interface DependencyEdge {
  id: string;
  source: string;
  target: string;
  import_string: string;
  edge_type: 'import' | 'require';
}

export interface GraphData {
  snapshot_id: string;
  node_count: number;
  edge_count: number;
  nodes: FileNode[];
  edges: DependencyEdge[];
}

// SSE Progress event types
export type ProgressEvent =
  | { type: 'progress'; stage: string; pct: number; message: string }
  | { type: 'done'; snapshot_id: string }
  | { type: 'error'; message: string };

export interface CreateSnapshotResponse {
  snapshot_id: string;
  project_id: string;
  status: SnapshotStatus;
  progress_url: string;
  graph_url: string;
}

export interface ProjectsListResponse {
  projects: Project[];
  total: number;
}
