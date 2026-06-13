// src/components/analysis/AnalysisProgress.tsx
// Consumes the SSE /snapshots/{id}/progress stream and displays a live progress bar.
import { useEffect, useRef, useState } from 'react';
import { CheckCircle2, XCircle, Loader2, Radio } from 'lucide-react';
import type { ProgressEvent } from '../../types';

interface Props {
  snapshotId: string;
  onComplete?: (snapshotId: string) => void;
  onError?: (message: string) => void;
}

interface LogLine {
  id: number;
  stage: string;
  message: string;
  pct: number;
}

export function AnalysisProgress({ snapshotId, onComplete, onError }: Props) {
  const [pct, setPct] = useState(0);
  const [stage, setStage] = useState('Connecting…');
  const [status, setStatus] = useState<'running' | 'done' | 'error'>('running');
  const [errorMsg, setErrorMsg] = useState('');
  const [log, setLog] = useState<LogLine[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);
  const counterRef = useRef(0);

  useEffect(() => {
    const es = new EventSource(
      `http://localhost:8000/api/v1/snapshots/${snapshotId}/progress`
    );
    esRef.current = es;

    es.onmessage = (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);

      if (event.type === 'progress') {
        setPct(event.pct);
        setStage(event.message);
        setLog((prev) => [
          ...prev,
          { id: counterRef.current++, stage: event.stage, message: event.message, pct: event.pct },
        ]);
      } else if (event.type === 'done') {
        setPct(100);
        setStage('Analysis complete!');
        setStatus('done');
        es.close();
        onComplete?.(snapshotId);
      } else if (event.type === 'error') {
        setErrorMsg(event.message);
        setStatus('error');
        es.close();
        onError?.(event.message);
      }
    };

    es.onerror = () => {
      setErrorMsg('Lost connection to server.');
      setStatus('error');
      es.close();
    };

    return () => es.close();
  }, [snapshotId, onComplete, onError]);

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [log]);

  const statusIcon =
    status === 'done' ? (
      <CheckCircle2 size={18} style={{ color: 'var(--success)' }} />
    ) : status === 'error' ? (
      <XCircle size={18} style={{ color: 'var(--danger)' }} />
    ) : (
      <Loader2 size={18} className="animate-spin" style={{ color: 'var(--accent)' }} />
    );

  return (
    <div className="card p-5 space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        {statusIcon}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate" style={{ color: 'var(--text-primary)' }}>
            {status === 'error' ? 'Analysis Failed' : stage}
          </p>
          <p className="text-xs font-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>
            {snapshotId.slice(0, 8)}…
          </p>
        </div>
        {status === 'running' && (
          <div className="flex items-center gap-1.5">
            <Radio size={12} style={{ color: 'var(--accent)' }} className="animate-pulse" />
            <span className="text-xs font-medium" style={{ color: 'var(--accent)' }}>Live</span>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
          <span>{pct}%</span>
          {status === 'done' && <span style={{ color: 'var(--success)' }}>Complete</span>}
          {status === 'error' && <span style={{ color: 'var(--danger)' }}>Failed</span>}
        </div>
        <div
          className="h-2 rounded-full overflow-hidden"
          style={{ background: 'var(--bg-hover)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${pct}%`,
              background:
                status === 'error'
                  ? 'var(--danger)'
                  : status === 'done'
                  ? 'var(--success)'
                  : `linear-gradient(90deg, var(--accent), var(--accent-hover))`,
              boxShadow: status === 'running' ? '0 0 8px var(--accent-glow)' : undefined,
            }}
          />
        </div>
      </div>

      {/* Error message */}
      {status === 'error' && errorMsg && (
        <div
          className="rounded-lg px-3 py-2 text-xs font-mono"
          style={{ background: 'rgba(244,63,94,0.08)', color: 'var(--danger)', border: '1px solid rgba(244,63,94,0.2)' }}
        >
          {errorMsg}
        </div>
      )}

      {/* Log output */}
      {log.length > 0 && (
        <div
          className="rounded-lg p-3 space-y-1 max-h-36 overflow-y-auto"
          style={{ background: 'var(--bg-base)', border: '1px solid var(--border)' }}
        >
          {log.map((line) => (
            <div key={line.id} className="flex items-baseline gap-2 text-xs font-mono leading-5">
              <span
                className="shrink-0 w-8 text-right"
                style={{ color: 'var(--accent)' }}
              >
                {line.pct}%
              </span>
              <span style={{ color: 'var(--text-muted)' }}>{line.stage}</span>
              <span className="truncate" style={{ color: 'var(--text-secondary)' }}>{line.message}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      )}
    </div>
  );
}
