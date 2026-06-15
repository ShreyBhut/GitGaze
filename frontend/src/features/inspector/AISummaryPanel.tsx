import { useState, useEffect } from 'react';
import { Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { snapshotsApi } from '../../lib/api';

export function AISummaryPanel({ snapshotId, nodeId }: { snapshotId: string; nodeId: string }) {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCached, setIsCached] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function fetchSummary() {
      setIsLoading(true);
      setError(null);
      setSummary(null);
      try {
        const detailLevel = localStorage.getItem('ai_detail_level') || 'concise';
        const res = await snapshotsApi.getSummary(snapshotId, nodeId, detailLevel);
        if (isMounted) {
          setSummary(res.summary);
          setIsCached(res.cached);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load AI summary');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    if (snapshotId && nodeId) {
      fetchSummary();
    }

    return () => {
      isMounted = false;
    };
  }, [snapshotId, nodeId]);

  return (
    <div style={{ marginBottom: 16 }}>
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
        <Sparkles size={11} style={{ color: '#a855f7' }} />
        AI Summary {isCached && <span style={{ opacity: 0.5 }}>(Cached)</span>}
      </div>

      <div
        style={{
          background: 'var(--bg-base)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: '12px',
          fontSize: 12,
          lineHeight: 1.5,
          color: 'var(--text-primary)',
        }}
      >
        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 11 }}>
            <Loader2 size={14} className="animate-spin" style={{ color: '#a855f7' }} />
            Analyzing code structure...
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, color: '#ef4444' }}>
            <AlertCircle size={14} style={{ marginTop: 2, flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {summary && !isLoading && !error && (
          <div 
            style={{ 
              overflowX: 'hidden', 
              fontSize: 12, 
              lineHeight: 1.6,
              wordWrap: 'break-word'
            }}
            dangerouslySetInnerHTML={{
              __html: summary
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/### (.*?)\n/g, '<h3 style="font-size: 13px; font-weight: 600; margin: 8px 0 4px 0; color: var(--text-primary);">$1</h3>\n')
                .replace(/## (.*?)\n/g, '<h2 style="font-size: 14px; font-weight: 600; margin: 8px 0 4px 0; color: var(--text-primary);">$1</h2>\n')
                .replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight: 600; color: var(--text-primary);">$1</strong>')
                .replace(/\*(.*?)\*/g, '<em style="font-style: italic;">$1</em>')
                .replace(/`(.*?)`/g, '<code style="background: var(--bg-hover); padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 11px;">$1</code>')
                .replace(/\n\* (.*?)(?=\n|$)/g, '\n<li style="margin-left: 16px; list-style-type: disc; margin-bottom: 4px;">$1</li>')
                .replace(/\n- (.*?)(?=\n|$)/g, '\n<li style="margin-left: 16px; list-style-type: disc; margin-bottom: 4px;">$1</li>')
                .replace(/\n\n/g, '<br/><br/>')
                .replace(/\n/g, '<br/>')
            }}
          />
        )}
      </div>
    </div>
  );
}
