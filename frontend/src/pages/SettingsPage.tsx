// src/pages/SettingsPage.tsx — Placeholder for Phase 7
import { Settings, Info } from 'lucide-react';

export function SettingsPage() {
  return (
    <div className="p-8 max-w-2xl mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-8">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
        >
          <Settings size={18} style={{ color: 'var(--accent)' }} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Settings</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Global analysis configuration</p>
        </div>
      </div>

      <div
        className="card p-5 flex items-start gap-3"
        style={{ borderColor: 'rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.03)' }}
      >
        <Info size={16} style={{ color: 'var(--accent)', marginTop: 2, flexShrink: 0 }} />
        <div>
          <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
            Coming in Phase 7
          </p>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            Per-project configuration (excluded directories, file size limits, enabled languages)
            is already available via <code className="mono text-[11px] px-1 py-0.5 rounded" style={{ background: 'var(--bg-hover)' }}>PATCH /api/v1/projects/{'{id}'}/config</code>.
            The settings UI will surface these controls in Phase 7.
          </p>
        </div>
      </div>
    </div>
  );
}
