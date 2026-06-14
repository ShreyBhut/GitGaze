// src/features/graph/GraphCanvas.tsx
// Main React Flow canvas: Dagre layout, custom nodes, position persistence.
import { useCallback, useEffect, useMemo, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeMouseHandler,
  type OnNodeDrag,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from '@dagrejs/dagre';
import { LayoutGrid, RefreshCw } from 'lucide-react';

import type { GraphData, FileNode as FileNodeData } from '../../types';
import { FileNodeComponent } from './nodes/FileNode';
import { snapshotsApi } from '../../lib/api';

// ─── Constants ───────────────────────────────────────────────────────────────

const NODE_W = 220;
const NODE_H = 72;

const nodeTypes = { fileNode: FileNodeComponent };

// ─── Dagre layout ────────────────────────────────────────────────────────────

function computeDagreLayout(
  nodes: Node[],
  edges: Edge[],
  direction: 'LR' | 'TB' = 'LR',
): Node[] {
  const g = new dagre.graphlib.Graph({ multigraph: false });
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 100,
    marginx: 30,
    marginy: 30,
  });

  nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
  edges.forEach((e) => {
    if (g.hasNode(e.source) && g.hasNode(e.target)) {
      g.setEdge(e.source, e.target);
    }
  });

  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    if (!pos) return n;
    return {
      ...n,
      position: { x: pos.x - NODE_W / 2, y: pos.y - NODE_H / 2 },
    };
  });
}

// ─── Graph data → React Flow nodes/edges ─────────────────────────────────────

function buildRFData(graphData: GraphData): { nodes: Node[]; edges: Edge[] } {
  const hasSavedPositions = graphData.nodes.some(
    (n) => n.pos_x !== null && n.pos_x !== undefined,
  );

  const rfNodes: Node[] = graphData.nodes.map((n) => ({
    id: n.id,
    type: 'fileNode',
    data: n as unknown as Record<string, unknown>,
    position: {
      x: n.pos_x ?? 0,
      y: n.pos_y ?? 0,
    },
  }));

  const rfEdges: Edge[] = graphData.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    animated: true,
    style: {
      stroke: '#ffffff',
      strokeWidth: 1.5,
    },
    markerEnd: {
      type: 'arrowclosed' as const,
      color: '#ffffff',
      width: 12,
      height: 12,
    },
  }));

  if (!hasSavedPositions) {
    const layouted = computeDagreLayout(rfNodes, rfEdges);
    return { nodes: layouted, edges: rfEdges };
  }

  return { nodes: rfNodes, edges: rfEdges };
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface Props {
  graphData: GraphData;
  snapshotId: string;
  onNodeSelect: (node: FileNodeData | null) => void;
}

// ─── Component ───────────────────────────────────────────────────────────────

export function GraphCanvas({ graphData, snapshotId, onNodeSelect }: Props) {
  const initial = useMemo(() => buildRFData(graphData), [graphData]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, , onEdgesChange] = useEdgesState(initial.edges);

  // Re-sync when graphData changes (e.g. new snapshot loaded)
  useEffect(() => {
    const next = buildRFData(graphData);
    setNodes(next.nodes);
  }, [graphData, setNodes]);

  // ── Position persistence ────────────────────────────────────────────────
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const persistPositions = useCallback(
    (currentNodes: Node[]) => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(async () => {
        const positions = Object.fromEntries(
          currentNodes.map((n) => [n.id, { x: n.position.x, y: n.position.y }]),
        );
        try {
          await snapshotsApi.savePositions(snapshotId, positions);
        } catch {
          // Silent fail — positions are cosmetic, not critical
        }
      }, 800); // debounce 800 ms
    },
    [snapshotId],
  );

  const handleNodeDragStop: OnNodeDrag = useCallback(
    (_event, _node, currentNodes) => {
      persistPositions(currentNodes);
    },
    [persistPositions],
  );

  // ── Node selection → inspector ──────────────────────────────────────────
  const handleNodeClick: NodeMouseHandler = useCallback(
    (_event, rfNode) => {
      const fileData = rfNode.data as unknown as FileNodeData;
      onNodeSelect(fileData);
    },
    [onNodeSelect],
  );

  const handlePaneClick = useCallback(() => onNodeSelect(null), [onNodeSelect]);

  // ── Re-layout button ────────────────────────────────────────────────────
  const handleRelayout = useCallback(() => {
    const relayouted = computeDagreLayout([...nodes], [...edges]);
    setNodes(relayouted);
    persistPositions(relayouted);
  }, [nodes, edges, setNodes, persistPositions]);

  // ─── MiniMap node color ─────────────────────────────────────────────────
  const miniMapNodeColor = useCallback((n: Node) => {
    const lang = (n.data as unknown as FileNodeData).language;
    const MAP: Record<string, string> = {
      '.py': '#3b82f6', '.ts': '#60a5fa', '.tsx': '#818cf8',
      '.js': '#f59e0b', '.jsx': '#fbbf24',
    };
    return lang ? (MAP[lang] ?? '#475569') : '#475569';
  }, []);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={handleNodeDragStop}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.08}
        maxZoom={2}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        style={{ background: '#18181b' }}
        proOptions={{ hideAttribution: true }}
      >
        {/* Dot grid background */}
        <Background
          variant={BackgroundVariant.Dots}
          gap={28}
          size={1.5}
          color="rgba(255,255,255,0.15)"
        />

        {/* Zoom / fit controls */}
        <Controls
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid #000000',
            borderRadius: 10,
            overflow: 'hidden',
          }}
        />

        {/* Mini-map */}
        <MiniMap
          nodeColor={miniMapNodeColor}
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid #000000',
            borderRadius: 10,
          }}
          maskColor="rgba(2,8,23,0.7)"
        />

        {/* Top-right panel: stats + re-layout */}
        <Panel position="top-right">
          <div
            style={{
              display: 'flex',
              gap: 8,
              alignItems: 'center',
            }}
          >
            {/* Stats pill */}
            <div
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 20,
                padding: '5px 12px',
                fontSize: 11,
                color: 'var(--text-muted)',
                display: 'flex',
                gap: 10,
              }}
            >
              <span>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                  {graphData.node_count}
                </span>{' '}
                nodes
              </span>
              <span style={{ opacity: 0.4 }}>·</span>
              <span>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                  {graphData.edge_count}
                </span>{' '}
                edges
              </span>
            </div>

            {/* Re-layout button */}
            <button
              onClick={handleRelayout}
              title="Reset Dagre layout"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: '6px 10px',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                fontSize: 11,
              }}
            >
              <LayoutGrid size={13} />
              <span>Re-layout</span>
            </button>
          </div>
        </Panel>

        {/* Bottom-center: hint */}
        <Panel position="bottom-center">
          <div
            style={{
              fontSize: 10,
              color: 'var(--text-muted)',
              background: 'var(--bg-elevated)',
              border: '1px solid #000000',
              borderRadius: 8,
              padding: '4px 10px',
              opacity: 0.7,
            }}
          >
            Click a node to inspect · Drag to reposition (auto-saved)
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
