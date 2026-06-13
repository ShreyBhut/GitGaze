// src/components/projects/AddProjectModal.tsx
import { useState, useRef, useEffect } from 'react';
import { FolderOpen, X, Loader2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, queryKeys } from '../../lib/api';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function AddProjectModal({ open, onClose }: Props) {
  const [name, setName] = useState('');
  const [path, setPath] = useState('');
  const [error, setError] = useState('');
  const nameRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  // Focus name input when modal opens
  useEffect(() => {
    if (open) {
      setTimeout(() => nameRef.current?.focus(), 50);
      setName('');
      setPath('');
      setError('');
    }
  }, [open]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const mutation = useMutation({
    mutationFn: () => projectsApi.create(name.trim(), path.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projects() });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name.trim()) return setError('Project name is required.');
    if (!path.trim()) return setError('Repository path is required.');
    mutation.mutate();
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(2,8,23,0.7)', backdropFilter: 'blur(4px)' }}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div
          className="card w-full max-w-md animate-fade-in"
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)' }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)' }}
              >
                <FolderOpen size={15} style={{ color: 'var(--accent)' }} />
              </div>
              <h2 id="modal-title" className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
                Add Repository
              </h2>
            </div>
            <button
              onClick={onClose}
              className="btn-ghost w-8 h-8 rounded-lg p-0"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
            <div>
              <label htmlFor="proj-name" className="label">Project Name</label>
              <input
                id="proj-name"
                ref={nameRef}
                className="input"
                placeholder="My Awesome Project"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="off"
                spellCheck={false}
              />
            </div>

            <div>
              <label htmlFor="proj-path" className="label">Repository Path</label>
              <input
                id="proj-path"
                className="input font-mono text-xs"
                placeholder="C:/Users/you/repos/my-project"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                autoComplete="off"
                spellCheck={false}
              />
              <p className="mt-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>
                Absolute path to the repository root on this machine.
              </p>
            </div>

            {/* Error */}
            {error && (
              <div
                className="rounded-lg px-3 py-2 text-xs"
                style={{ background: 'rgba(244,63,94,0.08)', color: 'var(--danger)', border: '1px solid rgba(244,63,94,0.2)' }}
              >
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button type="button" onClick={onClose} className="btn-ghost flex-1">
                Cancel
              </button>
              <button
                type="submit"
                id="add-project-submit"
                className="btn-primary flex-1"
                disabled={mutation.isPending}
              >
                {mutation.isPending ? (
                  <><Loader2 size={14} className="animate-spin" /> Adding…</>
                ) : (
                  'Add Project'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
