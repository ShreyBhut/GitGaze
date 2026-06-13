// src/components/layout/AppShell.tsx
import { NavLink, Outlet } from 'react-router-dom';
import { FolderGit2, BarChart3, Settings, Zap } from 'lucide-react';

const navItems = [
  { to: '/projects', icon: FolderGit2, label: 'Projects' },
  { to: '/analysis',  icon: BarChart3,  label: 'Analysis'  },
  { to: '/settings',  icon: Settings,   label: 'Settings'  },
];

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        className="flex flex-col w-56 shrink-0 border-r"
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: 'var(--accent)', boxShadow: '0 0 12px var(--accent-glow)' }}
          >
            <Zap size={14} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
              GitGaze
            </p>
            <p className="text-[10px] font-medium" style={{ color: 'var(--text-muted)' }}>
              v0.2.0
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'text-white'
                    : 'hover:text-white'
                }`
              }
              style={({ isActive }) =>
                isActive
                  ? { background: 'var(--accent)', boxShadow: '0 0 12px var(--accent-glow)', color: 'white' }
                  : { color: 'var(--text-secondary)' }
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t text-[10px]" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
          Repository Analysis System
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
