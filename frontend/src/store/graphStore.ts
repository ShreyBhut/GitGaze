// src/store/graphStore.ts
// Zustand store for graph canvas UI state (Phase 5 will populate the graph data here)
import { create } from 'zustand';
import type { FileNode, DependencyEdge, GraphData } from '../types';

interface SelectedNode {
  node: FileNode;
  position: { x: number; y: number };
}

interface GraphState {
  // Active snapshot being viewed
  activeSnapshotId: string | null;
  setActiveSnapshotId: (id: string | null) => void;

  // Raw graph data from the API
  graphData: GraphData | null;
  setGraphData: (data: GraphData | null) => void;

  // Inspector panel — which node is selected
  selectedNode: SelectedNode | null;
  setSelectedNode: (node: SelectedNode | null) => void;

  // Layout — whether the inspector panel is open
  inspectorOpen: boolean;
  setInspectorOpen: (open: boolean) => void;

  // Search / filter state
  searchQuery: string;
  setSearchQuery: (q: string) => void;

  // Highlighted node (hover)
  highlightedNodeId: string | null;
  setHighlightedNodeId: (id: string | null) => void;

  // Reset everything (e.g. when switching projects)
  reset: () => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  activeSnapshotId: null,
  setActiveSnapshotId: (id) => set({ activeSnapshotId: id }),

  graphData: null,
  setGraphData: (data) => set({ graphData: data }),

  selectedNode: null,
  setSelectedNode: (node) => set({ selectedNode: node, inspectorOpen: node !== null }),

  inspectorOpen: false,
  setInspectorOpen: (open) => set({ inspectorOpen: open }),

  searchQuery: '',
  setSearchQuery: (q) => set({ searchQuery: q }),

  highlightedNodeId: null,
  setHighlightedNodeId: (id) => set({ highlightedNodeId: id }),

  reset: () =>
    set({
      activeSnapshotId: null,
      graphData: null,
      selectedNode: null,
      inspectorOpen: false,
      searchQuery: '',
      highlightedNodeId: null,
    }),
}));
