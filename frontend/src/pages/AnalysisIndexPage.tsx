import { BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';

export function AnalysisIndexPage() {
  return (
    <div
      className="animate-fade-in"
      style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-base)',
      }}
    >
      <div style={{ textAlign: 'center', maxWidth: 300 }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}
        >
          <BarChart3 size={24} style={{ color: 'var(--text-muted)' }} />
        </div>
        <h2
          style={{
            fontSize: 16,
            fontWeight: 600,
            color: 'var(--text-primary)',
            marginBottom: 8,
          }}
        >
          No Analysis Selected
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 24, lineHeight: 1.5 }}>
          Please select a repository from the Projects page to view its dependency graph and metrics.
        </p>
        <Link to="/projects" className="btn-primary">
          Go to Projects
        </Link>
      </div>
    </div>
  );
}
