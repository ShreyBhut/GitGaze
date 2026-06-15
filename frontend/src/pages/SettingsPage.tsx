// src/pages/SettingsPage.tsx
import { Settings, User, LogOut, Trash2, Cpu } from 'lucide-react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authApi, projectsApi } from '../lib/api';

export function SettingsPage() {
  const [detailLevel, setDetailLevel] = useState(localStorage.getItem('ai_detail_level') || 'concise');

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.getMe,
    retry: false
  });

  const handleToggleDetailLevel = (level: string) => {
    setDetailLevel(level);
    localStorage.setItem('ai_detail_level', level);
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      window.location.href = '/login';
    } catch (e) {
      console.error(e);
      window.location.href = '/login';
    }
  };

  const handleDeleteAll = async () => {
    if (confirm("Are you absolutely sure you want to delete all projects and data? This cannot be undone.")) {
      try {
        await projectsApi.deleteAll();
        window.location.reload();
      } catch (e) {
        alert("Failed to delete projects.");
      }
    }
  };

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
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Global app configuration and account</p>
        </div>
      </div>

      <div className="flex flex-col gap-6">
        {/* AI Settings */}
        <section className="card p-5" style={{ borderColor: 'rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.03)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={18} style={{ color: 'var(--accent)' }} />
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>AI Settings</h2>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>AI Summary Detail Level</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Choose whether AI summaries should be concise overviews or highly detailed explanations.</p>
            </div>
            
            <div className="flex items-center gap-2 p-1 rounded-lg" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
              <button 
                onClick={() => handleToggleDetailLevel('concise')}
                className="px-3 py-1 text-xs rounded-md transition-colors"
                style={{ 
                  background: detailLevel === 'concise' ? 'var(--bg-hover)' : 'transparent',
                  color: detailLevel === 'concise' ? 'var(--text-primary)' : 'var(--text-muted)'
                }}
              >
                Concise
              </button>
              <button 
                onClick={() => handleToggleDetailLevel('detailed')}
                className="px-3 py-1 text-xs rounded-md transition-colors"
                style={{ 
                  background: detailLevel === 'detailed' ? 'var(--bg-hover)' : 'transparent',
                  color: detailLevel === 'detailed' ? 'var(--text-primary)' : 'var(--text-muted)'
                }}
              >
                Detailed
              </button>
            </div>
          </div>
        </section>

        {/* Account Settings */}
        <section className="card p-5" style={{ borderColor: 'rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.03)' }}>
          <div className="flex items-center gap-2 mb-4">
            <User size={18} style={{ color: 'var(--accent)' }} />
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Account</h2>
          </div>
          
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Connected GitHub Account</p>
              {user ? (
                <div className="flex items-center gap-3 mt-3">
                  <img src={user.avatar_url} alt={user.username} className="w-10 h-10 rounded-full border border-gray-700" />
                  <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>@{user.username}</span>
                </div>
              ) : (
                <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>No account connected.</p>
              )}
            </div>
            
            {user && (
              <button 
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--border)' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
              >
                <LogOut size={16} /> Sign Out
              </button>
            )}
          </div>
        </section>

        {/* Danger Zone */}
        <section className="card p-5 border border-red-500/20" style={{ background: 'rgba(239, 68, 68, 0.05)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Trash2 size={18} className="text-red-500" />
            <h2 className="text-lg font-semibold text-red-500">Danger Zone</h2>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-400 mb-1">Delete All Data</p>
              <p className="text-xs text-red-500/70">Permanently remove all your projects, snapshots, and AI summaries.</p>
            </div>
            
            <button 
              onClick={handleDeleteAll}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 transition-colors"
            >
              Delete Everything
            </button>
          </div>
        </section>

      </div>
    </div>
  );
}
