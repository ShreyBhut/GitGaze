// src/components/projects/ProjectCard.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, Play, ChevronRight, Clock, CheckCircle2, XCircle, Loader2, FolderGit2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, snapshotsApi, queryKeys } from '../../lib/api';
import type { Project, SnapshotStatus } from '../../types';

interface Props {
  project: Project;
}

function StatusBadge({ status }: { status: SnapshotStatus | undefined }) {
  if (!status) return <span className="badge badge-muted">No analysis</span>;
  const map: Record<SnapshotStatus, { cls: string; icon: React.ReactNode; label: string }> = {
    pending:    { cls: 'badge-muted',    icon: <Clock size={10} />,       label: 'Pending' },
    processing: { cls: 'badge-info',     icon: <Loader2 size={10} className="animate-spin" />, label: 'Running' },
    completed:  { cls: 'badge-success',  icon: <CheckCircle2 size={10} />,label: 'Complete' },
    failed:     { cls: 'badge-danger',   icon: <XCircle size={10} />,     label: 'Failed' },
  };
  const { cls, icon, label } = map[status];
  return <span className={`badge ${cls}`}>{icon}{label}</span>;
}

export function ProjectCard({ project }: Props) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => projectsApi.delete(project.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.projects() }),
  });

  const analyzeMutation = useMutation({
    mutationFn: () => snapshotsApi.create(project.id),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: queryKeys.projects() });
      navigate(`/analysis/${project.id}/${data.snapshot_id}`);
    },
  });

  const shortPath = project.path.length > 48
    ? '…' + project.path.slice(-48)
    : project.path;

  return (
    <div className="card p-5 flex flex-col gap-4 group animate-fade-in">
      {/* Top row */}
      <div className="flex items-start gap-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
          style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)' }}
        >
          <FolderGit2 size={16} style={{ color: 'var(--accent)' }} />
        </div>
        <div className="flex-1 min-w-0">
          <h3
            className="font-semibold text-sm truncate"
            style={{ color: 'var(--text-primary)' }}
            title={project.name}
          >
            {project.name}
          </h3>
          <p
            className="text-xs font-mono mt-0.5 truncate"
            style={{ color: 'var(--text-muted)' }}
            title={project.path}
          >
            {shortPath}
          </p>
        </div>
        <StatusBadge status={project.latest_snapshot?.status} />
      </div>

      {/* Meta */}
      <div
        className="text-xs flex items-center gap-1"
        style={{ color: 'var(--text-muted)' }}
      >
        <Clock size={11} />
        <span>Added {new Date(project.created_at).toLocaleDateString()}</span>
        {project.latest_snapshot?.completed_at && (
          <>
            <span className="mx-1 opacity-40">·</span>
            <span>Analysed {new Date(project.latest_snapshot.completed_at).toLocaleDateString()}</span>
          </>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t" style={{ borderColor: 'var(--border)' }}>
        {/* Analyse button */}
        <button
          id={`analyze-${project.id}`}
          className="btn-primary flex-1 text-xs py-1.5 h-8"
          onClick={() => analyzeMutation.mutate()}
          disabled={analyzeMutation.isPending}
        >
          {analyzeMutation.isPending
            ? <><Loader2 size={12} className="animate-spin" />Starting…</>
            : <><Play size={12} />Analyse</>
          }
        </button>

        {/* View last result */}
        {project.latest_snapshot?.status === 'completed' && (
          <button
            className="btn-ghost flex-1 text-xs py-1.5 h-8"
            onClick={() => navigate(`/analysis/${project.id}/${project.latest_snapshot!.id}`)}
          >
            View graph <ChevronRight size={12} />
          </button>
        )}

        {/* Delete */}
        {confirmDelete ? (
          <div className="flex gap-1">
            <button
              className="btn-danger text-xs py-1 px-2 h-8"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Confirm'}
            </button>
            <button className="btn-ghost text-xs px-2 h-8" onClick={() => setConfirmDelete(false)}>
              Cancel
            </button>
          </div>
        ) : (
          <button
            id={`delete-${project.id}`}
            className="btn-ghost w-8 h-8 p-0 rounded-lg text-xs opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ color: 'var(--danger)' }}
            onClick={() => setConfirmDelete(true)}
            title="Delete project"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
