// src/pages/AnalysisPage.tsx
// Shows SSE progress when a snapshot is running, then the graph placeholder.
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, BarChart3, FileCode2, GitBranch, Network } from 'lucide-react';
import { snapshotsApi, projectsApi, queryKeys } from '../lib/api';
import { AnalysisProgress } from '../components/analysis/AnalysisProgress';
import { useGraphStore } from '../store/graphStore';
import { useEffect } from 'react';

export function AnalysisPage() {
  const { projectId, snapshotId } = useParams<{ projectId: string; snapshotId: string }>();
  const navigate = useNavigate();
  const { setActiveSnapshotId, setGraphData, reset } = useGraphStore();

  // Load project info
  const { data: project } = useQuery({
    queryKey: queryKeys.project(projectId!),
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  });

  // Poll snapshot status until completed
  const { data: snapshot, refetch: refetchSnapshot } = useQuery({
    queryKey: queryKeys.snapshot(snapshotId!),
    queryFn: () => snapshotsApi.get(snapshotId!),
    enabled: !!snapshotId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'processing' ? 2000 : false;
    },
  });

  // Load graph once completed
  const { data: graphData } = useQuery({
    queryKey: queryKeys.graph(snapshotId!),
    queryFn: () => snapshotsApi.getGraph(snapshotId!),
    enabled: snapshot?.status === 'completed',
  });

  useEffect(() => {
    if (snapshotId) setActiveSnapshotId(snapshotId);
    return () => reset();
  }, [snapshotId, setActiveSnapshotId, reset]);

  useEffect(() => {
    if (graphData) setGraphData(graphData);
  }, [graphData, setGraphData]);

  const isRunning = snapshot?.status === 'pending' || snapshot?.status === 'processing';
  const isComplete = snapshot?.status === 'completed';

  return (
    <div className="p-8 max-w-5xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6">
        <Link
          to="/projects"
          className="btn-ghost text-xs px-2 py-1.5 h-7"
          style={{ color: 'var(--text-muted)' }}
        >
          <ArrowLeft size={12} /> Projects
        </Link>
        <span style={{ color: 'var(--text-muted)' }}>/</span>
        <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
          {project?.name ?? 'Loading…'}
        </span>
        <span style={{ color: 'var(--text-muted)' }}>/</span>
        <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
          {snapshotId?.slice(0, 8)}…
        </span>
      </div>

      {/* Page title */}
      <div className="flex items-center gap-3 mb-8">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)' }}
        >
          <BarChart3 size={18} style={{ color: 'var(--accent)' }} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
            Analysis
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {project?.name} · {new Date(snapshot?.created_at ?? '').toLocaleString()}
          </p>
        </div>
      </div>

      {/* Progress */}
      {(isRunning || snapshot?.status === 'failed') && snapshotId && (
        <div className="mb-6">
          <AnalysisProgress
            snapshotId={snapshotId}
            onComplete={() => refetchSnapshot()}
            onError={(msg) => console.error('Analysis error:', msg)}
          />
        </div>
      )}

      {/* Stats when complete */}
      {isComplete && graphData && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { icon: FileCode2, label: 'Files', value: graphData.node_count },
            { icon: GitBranch, label: 'Dependencies', value: graphData.edge_count },
            {
              icon: Network,
              label: 'Languages',
              value: [...new Set(graphData.nodes.map((n) => n.language).filter(Boolean))].length,
            },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="card p-4 text-center">
              <Icon size={18} className="mx-auto mb-2" style={{ color: 'var(--accent)' }} />
              <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{value}</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Graph canvas placeholder (Phase 5) */}
      {isComplete && (
        <div
          className="card rounded-xl overflow-hidden"
          style={{ height: '480px', display: 'flex', flexDirection: 'column' }}
        >
          <div
            className="flex items-center gap-2 px-5 py-3 border-b text-xs font-medium"
            style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
          >
            <Network size={13} />
            Dependency Graph — coming in Phase 5
          </div>
          <div
            className="flex-1 flex flex-col items-center justify-center gap-3"
            style={{ background: 'var(--bg-base)' }}
          >
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
            >
              <Network size={24} style={{ color: 'var(--text-muted)' }} />
            </div>
            <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              Graph visualisation
            </p>
            <p className="text-xs text-center max-w-xs" style={{ color: 'var(--text-muted)' }}>
              The React Flow canvas will render here in Phase 5.
              {graphData && ` ${graphData.node_count} nodes and ${graphData.edge_count} edges are ready.`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
