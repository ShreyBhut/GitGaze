// src/features/inspector/InspectorPanel.tsx
// Side panel displayed when a node is selected in the graph canvas.
import { X, FileCode2, BarChart2, ArrowRight, Code2, Hash } from 'lucide-react';
import type { FileNode } from '../../types';
import { AISummaryPanel } from './AISummaryPanel';

interface Props {
  snapshotId: string;
  node: FileNode;
  onClose: () => void;
}

// ─── Language label → color ───────────────────────────────────────────────

const LANG_COLORS: Record<string, string> = {
  '.py': '#3b82f6', '.ts': '#60a5fa', '.tsx': '#818cf8',
  '.js': '#f59e0b', '.jsx': '#fbbf24', '.css': '#34d399',
};

function langColor(lang: string | null) {
  return lang ? (LANG_COLORS[lang] ?? '#64748b') : '#64748b';
}

// ─── Component ───────────────────────────────────────────────────────────────

export function InspectorPanel({ snapshotId, node, onClose }: Props) {
  const parts = node.file_path.split('/');
  const filename = parts[parts.length - 1];
  const color = langColor(node.language);

  const metrics = node.metrics ?? { loc: 0, sloc: 0, comments: 0, blanks: 0 };
  const maxMetric = Math.max(metrics.loc, 1);

  return (
    <div
      className="animate-slide-right"
      style={{
        width: 300,
        height: '100%',
        background: 'var(--bg-elevated)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div
        style={{
          padding: '14px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
        }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            background: `${color}18`,
            border: `1px solid ${color}33`,
          }}
        >
          <FileCode2 size={15} style={{ color }} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--text-primary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={filename}
          >
            {filename}
          </div>
          <div
            style={{
              fontSize: 9,
              fontFamily: 'monospace',
              color: 'var(--text-muted)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              marginTop: 2,
            }}
            title={node.file_path}
          >
            {node.file_path}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            padding: 4,
            borderRadius: 6,
            flexShrink: 0,
          }}
          title="Close inspector"
        >
          <X size={15} />
        </button>
      </div>

      {/* ── Scrollable body ──────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>

        {/* Language badge */}
        {node.language && (
          <div style={{ marginBottom: 16 }}>
            <SectionLabel icon={<Hash size={11} />} text="Language" />
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '3px 10px',
                borderRadius: 20,
                fontSize: 11,
                fontWeight: 600,
                background: `${color}18`,
                color,
                border: `1px solid ${color}33`,
              }}
            >
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: color }} />
              {node.language}
            </span>
          </div>
        )}

        {/* AI Summary */}
        {node.node_type === 'file' && (
          <AISummaryPanel snapshotId={snapshotId} nodeId={node.id} />
        )}

        {/* ── Metrics ─────────────────────────────────────────────────────── */}
        <div style={{ marginBottom: 16 }}>
          <SectionLabel icon={<BarChart2 size={11} />} text="Metrics" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: 'Lines of Code',   value: metrics.loc,      key: 'loc'      },
              { label: 'Source Lines',    value: metrics.sloc,     key: 'sloc'     },
              { label: 'Comments',        value: metrics.comments, key: 'comments' },
              { label: 'Blank Lines',     value: metrics.blanks,   key: 'blanks'   },
            ].map(({ label, value }) => (
              <div key={label}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 11,
                    marginBottom: 4,
                    color: 'var(--text-secondary)',
                  }}
                >
                  <span>{label}</span>
                  <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>{value}</span>
                </div>
                <div
                  style={{
                    height: 4,
                    borderRadius: 2,
                    background: 'var(--bg-hover)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.round((value / maxMetric) * 100)}%`,
                      background: `linear-gradient(90deg, var(--accent), var(--accent-hover))`,
                      borderRadius: 2,
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Imports ──────────────────────────────────────────────────────── */}
        {node.imports && node.imports.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <SectionLabel
              icon={<ArrowRight size={11} />}
              text={`Imports (${node.imports.length})`}
            />
            <div
              style={{
                background: 'var(--bg-base)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                overflow: 'hidden',
                maxHeight: 160,
                overflowY: 'auto',
              }}
            >
              {node.imports.map((imp, i) => (
                <div
                  key={i}
                  style={{
                    padding: '5px 10px',
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: 'var(--text-secondary)',
                    borderBottom: i < node.imports.length - 1 ? '1px solid var(--border)' : undefined,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span style={{ color: 'var(--accent)', opacity: 0.6, fontSize: 9 }}>›</span>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{imp}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Functions ────────────────────────────────────────────────────── */}
        {node.functions && node.functions.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <SectionLabel
              icon={<Code2 size={11} />}
              text={`Functions (${node.functions.length})`}
            />
            <div
              style={{
                background: 'var(--bg-base)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                overflow: 'hidden',
                maxHeight: 180,
                overflowY: 'auto',
              }}
            >
              {node.functions.map((fn, i) => (
                <div
                  key={i}
                  style={{
                    padding: '6px 10px',
                    fontSize: 11,
                    borderBottom: i < node.functions.length - 1 ? '1px solid var(--border)' : undefined,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'monospace',
                      color: 'var(--text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '65%',
                    }}
                    title={fn.name}
                  >
                    {fn.name}
                  </span>
                  <span
                    style={{
                      fontSize: 9,
                      color: 'var(--text-muted)',
                      fontFamily: 'monospace',
                      flexShrink: 0,
                    }}
                  >
                    L{fn.start_line}–{fn.end_line}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Reusable section label ───────────────────────────────────────────────

function SectionLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 10,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        color: 'var(--text-muted)',
        marginBottom: 8,
      }}
    >
      {icon}
      {text}
    </div>
  );
}
