// src/features/graph/nodes/FileNode.tsx
// Custom React Flow node for a single file in the dependency graph.
import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { FileNode as FileNodeData } from '../../../types';

// ─── Language config ─────────────────────────────────────────────────────────

const LANG_CONFIG: Record<string, { color: string; label: string }> = {
  '.py':  { color: '#3b82f6', label: 'py'  },
  '.ts':  { color: '#60a5fa', label: 'ts'  },
  '.tsx': { color: '#818cf8', label: 'tsx' },
  '.js':  { color: '#f59e0b', label: 'js'  },
  '.jsx': { color: '#fbbf24', label: 'jsx' },
  '.css': { color: '#34d399', label: 'css' },
  '.html':{ color: '#fb923c', label: 'html'},
  '.json':{ color: '#a78bfa', label: 'json'},
  '.md':  { color: '#94a3b8', label: 'md'  },
};

function getLangConfig(lang: string | null) {
  return lang ? (LANG_CONFIG[lang] ?? { color: '#475569', label: lang.slice(1) }) : { color: '#475569', label: '?' };
}

// ─── Component ───────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const FileNodeComponent = memo(({ data, selected }: NodeProps<any>) => {
  const fileData = data as FileNodeData;
  const parts = fileData.file_path.split('/');
  const filename = parts[parts.length - 1];
  const dir = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
  const { color, label } = getLangConfig(fileData.language);

  const loc = fileData.metrics?.loc ?? 0;
  const importCount = fileData.imports?.length ?? 0;
  const fnCount = fileData.functions?.length ?? 0;

  return (
    <div
      style={{
        background: selected
          ? 'rgba(17,29,53,0.98)'
          : 'rgba(13,21,38,0.95)',
        border: `1px solid ${selected ? 'var(--accent)' : 'rgba(99,130,201,0.18)'}`,
        boxShadow: selected
          ? '0 0 0 2px rgba(99,102,241,0.35), 0 4px 20px rgba(0,0,0,0.5)'
          : '0 2px 8px rgba(0,0,0,0.35)',
        borderRadius: 10,
        padding: '10px 14px',
        width: 220,
        cursor: 'pointer',
        transition: 'border-color 0.15s, box-shadow 0.15s',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Target handle (left — receives imports) */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: color,
          border: 'none',
          width: 8,
          height: 8,
          borderRadius: '50%',
        }}
      />

      {/* ── Header row ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: dir ? 3 : 6 }}>
        {/* Language dot */}
        <div
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: color,
            flexShrink: 0,
            boxShadow: `0 0 6px ${color}80`,
          }}
        />
        {/* Filename */}
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: 'var(--text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 1,
          }}
          title={filename}
        >
          {filename}
        </span>
        {/* Language badge */}
        <span
          style={{
            fontSize: 9,
            fontFamily: 'var(--font-mono, monospace)',
            background: `${color}22`,
            color: color,
            border: `1px solid ${color}44`,
            borderRadius: 4,
            padding: '1px 5px',
            flexShrink: 0,
            letterSpacing: '0.03em',
          }}
        >
          {label}
        </span>
      </div>

      {/* Directory path */}
      {dir && (
        <div
          style={{
            fontSize: 9,
            color: 'var(--text-muted)',
            fontFamily: 'monospace',
            marginBottom: 6,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            opacity: 0.7,
          }}
          title={dir}
        >
          {dir}/
        </div>
      )}

      {/* ── Metrics row ────────────────────────────────────────────────── */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          fontSize: 10,
          color: 'var(--text-muted)',
          borderTop: '1px solid rgba(99,130,201,0.1)',
          paddingTop: 6,
        }}
      >
        <MetricChip label="LOC" value={loc} />
        {importCount > 0 && <MetricChip label="imp" value={importCount} />}
        {fnCount > 0 && <MetricChip label="fn" value={fnCount} />}
      </div>

      {/* Source handle (right — emits imports) */}
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: color,
          border: 'none',
          width: 8,
          height: 8,
          borderRadius: '50%',
        }}
      />
    </div>
  );
});
FileNodeComponent.displayName = 'FileNodeComponent';

function MetricChip({ label, value }: { label: string; value: number }) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <span style={{ opacity: 0.55 }}>{label}</span>
      <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{value}</span>
    </span>
  );
}
