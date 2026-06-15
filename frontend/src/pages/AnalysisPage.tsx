// src/pages/AnalysisPage.tsx
// Full analysis view: SSE progress → stats → interactive graph canvas + inspector panel.
import { useCallback, useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, BarChart3, FileCode2, GitBranch, Layers, Search } from 'lucide-react';
import { ReactFlowProvider } from '@xyflow/react';

import { snapshotsApi, projectsApi, queryKeys } from '../lib/api';
import { AnalysisProgress } from '../components/analysis/AnalysisProgress';
import { GraphCanvas } from '../features/graph/GraphCanvas';
import { InspectorPanel } from '../features/inspector/InspectorPanel';
import { useGraphStore } from '../store/graphStore';
import type { FileNode } from '../types';

export function AnalysisPage() {
  const { projectId, snapshotId } = useParams<{
    projectId: string;
    snapshotId: string;
  }>();
  const { setActiveSnapshotId, setGraphData, graphData: storeGraph, reset } = useGraphStore();
  const [selectedNode, setSelectedNode] = useState<FileNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  // ── Project info ───────────────────────────────────────────────────────
  const { data: project } = useQuery({
    queryKey: queryKeys.project(projectId!),
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  });

  // ── Poll snapshot status until completed ──────────────────────────────
  const { data: snapshot, refetch: refetchSnapshot } = useQuery({
    queryKey: queryKeys.snapshot(snapshotId!),
    queryFn: () => snapshotsApi.get(snapshotId!),
    enabled: !!snapshotId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'processing' ? 2000 : false;
    },
  });

  // ── Load graph once completed ──────────────────────────────────────────
  const { data: graphData } = useQuery({
    queryKey: queryKeys.graph(snapshotId!),
    queryFn: () => snapshotsApi.getGraph(snapshotId!),
    enabled: snapshot?.status === 'completed',
  });

  // ── Sync to Zustand store ──────────────────────────────────────────────
  useEffect(() => {
    if (snapshotId) setActiveSnapshotId(snapshotId);
    return () => reset();
  }, [snapshotId, setActiveSnapshotId, reset]);

  useEffect(() => {
    if (graphData) setGraphData(graphData);
  }, [graphData, setGraphData]);

  // ── Node selection ─────────────────────────────────────────────────────
  const handleNodeSelect = useCallback((node: FileNode | null) => {
    setSelectedNode(node);
  }, []);

  const isRunning =
    snapshot?.status === 'pending' || snapshot?.status === 'processing';
  const isComplete = snapshot?.status === 'completed';
  const isFailed = snapshot?.status === 'failed';

  const activeGraph = graphData ?? storeGraph;
  const uniqueLangs = activeGraph
    ? [...new Set(activeGraph.nodes.map((n) => n.language).filter(Boolean))]
    : [];

  const searchResults = useMemo(() => {
    if (!activeGraph || !searchQuery.trim()) return [];
    const query = searchQuery.toLowerCase();
    return activeGraph.nodes
      .filter((n) => n.file_path.toLowerCase().includes(query))
      .slice(0, 10);
  }, [activeGraph, searchQuery]);

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* ── Top bar ──────────────────────────────────────────────────────── */}
      <div
        style={{
          padding: '12px 24px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          flexShrink: 0,
        }}
      >
        {/* Breadcrumb */}
        <Link
          to="/projects"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            color: 'var(--text-muted)',
            textDecoration: 'none',
            fontSize: 12,
          }}
        >
          <ArrowLeft size={13} /> Projects
        </Link>
        <span style={{ color: 'var(--border)', fontSize: 12 }}>/</span>
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
          {project?.name ?? '…'}
        </span>
        <span style={{ color: 'var(--border)', fontSize: 12 }}>/</span>
        <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
          {snapshotId?.slice(0, 8)}…
        </span>

        <div style={{ flex: 1 }} />

        {/* Search bar */}
        {isComplete && activeGraph && (
          <div style={{ position: 'relative', width: 220 }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search size={14} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
                style={{
                  width: '100%',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 16,
                  padding: '5px 12px 5px 30px',
                  fontSize: 11,
                  color: 'var(--text-primary)',
                  outline: 'none',
                }}
              />
            </div>
            {isSearchFocused && searchResults.length > 0 && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  marginTop: 6,
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  padding: 4,
                  boxShadow: 'var(--shadow-md)',
                  zIndex: 100,
                  maxHeight: 300,
                  overflowY: 'auto',
                }}
              >
                {searchResults.map((node) => (
                  <div
                    key={node.id}
                    onClick={() => {
                      handleNodeSelect(node);
                      setSearchQuery('');
                      setIsSearchFocused(false);
                    }}
                    style={{
                      padding: '6px 10px',
                      cursor: 'pointer',
                      borderRadius: 6,
                      fontSize: 12,
                      color: 'var(--text-primary)',
                      borderBottom: '1px solid var(--border)',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-hover)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {node.file_path.split('/').pop()}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {node.file_path}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Stats pills (shown when complete) */}
        {isComplete && activeGraph && (
          <div style={{ display: 'flex', gap: 8 }}>
            <StatPill icon={<FileCode2 size={11} />} value={activeGraph.node_count} label="files" />
            <StatPill icon={<GitBranch size={11} />} value={activeGraph.edge_count} label="deps" />
            <StatPill icon={<Layers size={11} />} value={uniqueLangs.length} label="langs" />
          </div>
        )}

        {/* Status badge */}
        {snapshot && (
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '3px 10px',
              borderRadius: 20,
              ...(isComplete
                ? { background: 'rgba(34,211,160,0.12)', color: 'var(--success)' }
                : isFailed
                ? { background: 'rgba(244,63,94,0.12)', color: 'var(--danger)' }
                : { background: 'rgba(255,255,255,0.12)', color: 'var(--text-primary)' }),
            }}
          >
            {snapshot.status}
          </span>
        )}
      </div>

      {/* ── Progress overlay (when running / failed) ──────────────────── */}
      {(isRunning || isFailed) && snapshotId && (
        <div style={{ padding: '20px 24px', flexShrink: 0 }}>
          <AnalysisProgress
            snapshotId={snapshotId}
            onComplete={() => refetchSnapshot()}
            onError={(msg) => console.error('Analysis error:', msg)}
          />
        </div>
      )}

      {/* ── Graph area (canvas + inspector side by side) ──────────────── */}
      {isComplete && activeGraph && (
        <div
          style={{
            flex: 1,
            display: 'flex',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* React Flow needs ReactFlowProvider when used outside a ReactFlow instance */}
          <ReactFlowProvider>
            <div style={{ flex: 1, minWidth: 0 }}>
              <GraphCanvas
                graphData={activeGraph}
                snapshotId={snapshotId!}
                selectedNodeId={selectedNode?.id}
                onNodeSelect={handleNodeSelect}
              />
            </div>
          </ReactFlowProvider>

          {/* Inspector panel slides in when a node is selected */}
          {selectedNode && (
            <InspectorPanel
              snapshotId={snapshotId!}
              node={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          )}
        </div>
      )}

      {/* ── Pending state (waiting for first poll) ────────────────────── */}
      {!isRunning && !isComplete && !isFailed && (
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <BarChart3
              size={32}
              style={{ color: 'var(--text-muted)', margin: '0 auto 12px' }}
            />
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
              Loading snapshot…
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function StatPill({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 5,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: 16,
        padding: '3px 10px',
        fontSize: 11,
        color: 'var(--text-muted)',
      }}
    >
      {icon}
      <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{value}</span>
      <span>{label}</span>
    </div>
  );
}
