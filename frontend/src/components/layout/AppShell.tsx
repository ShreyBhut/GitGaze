import { useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { FolderGit2, BarChart3, Settings, Zap, LogIn, LogOut } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const navItems = [
  { to: '/projects', icon: FolderGit2, label: 'Projects' },
  { to: '/analysis',  icon: BarChart3,  label: 'Analysis'  },
  { to: '/settings',  icon: Settings,   label: 'Settings'  },
];

export function AppShell() {
  const { user, isLoading, checkAuth, login, logout } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

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
            <Zap size={14} className="text-black" />
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
                    ? 'text-black'
                    : 'hover:text-primary'
                }`
              }
              style={({ isActive }) =>
                isActive
                  ? { background: 'var(--accent)', boxShadow: '0 0 12px var(--accent-glow)', color: 'black' }
                  : { color: 'var(--text-secondary)' }
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
          {isLoading ? (
            <div className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>Loading...</div>
          ) : user ? (
            <div className="flex items-center gap-3">
              <img src={user.avatar_url} alt={user.username} className="w-8 h-8 rounded-full border border-zinc-700" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold truncate" style={{ color: 'var(--text-primary)' }}>{user.username}</p>
                <p className="text-[10px] truncate" style={{ color: 'var(--text-muted)' }}>GitHub User</p>
              </div>
              <button
                onClick={logout}
                className="btn-ghost w-8 h-8 p-0 rounded-lg shrink-0 flex items-center justify-center text-zinc-400 hover:text-white"
                title="Log out"
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button
              onClick={login}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all"
              style={{ background: 'white', color: 'black' }}
            >
              <LogIn size={14} />
              Login with GitHub
            </button>
          )}
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
