// src/pages/ProjectsPage.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, FolderGit2, RefreshCw, Search } from 'lucide-react';
import { projectsApi, queryKeys } from '../lib/api';
import { ProjectCard } from '../components/projects/ProjectCard';
import { AddProjectModal } from '../components/projects/AddProjectModal';

export function ProjectsPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: queryKeys.projects(),
    queryFn: projectsApi.list,
  });

  const filtered = (data?.projects ?? []).filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.path.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-5xl mx-auto animate-fade-in">
      {/* Page header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            Projects
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            {data?.total ?? 0} registered repositor{data?.total === 1 ? 'y' : 'ies'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn-ghost w-9 h-9 p-0 rounded-lg"
            onClick={() => refetch()}
            title="Refresh"
          >
            <RefreshCw size={15} className={isFetching ? 'animate-spin' : ''} />
          </button>
          <button
            id="add-project-btn"
            className="btn-primary"
            onClick={() => setModalOpen(true)}
          >
            <Plus size={15} />
            Add Repository
          </button>
        </div>
      </div>

      {/* Search */}
      {(data?.total ?? 0) > 0 && (
        <div className="relative mb-6">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: 'var(--text-muted)' }}
          />
          <input
            className="input pl-9"
            placeholder="Filter by name or path…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-5 space-y-3">
              <div className="skeleton h-4 w-2/3" />
              <div className="skeleton h-3 w-full" />
              <div className="skeleton h-3 w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {isError && (
        <div
          className="card p-6 text-center"
          style={{ borderColor: 'rgba(244,63,94,0.3)', background: 'rgba(244,63,94,0.05)' }}
        >
          <p className="text-sm" style={{ color: 'var(--danger)' }}>
            Failed to load projects. Is the backend running?
          </p>
          <button className="btn-ghost mt-3 text-sm" onClick={() => refetch()}>
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && (data?.total ?? 0) === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
          >
            <FolderGit2 size={28} style={{ color: 'var(--text-muted)' }} />
          </div>
          <h2 className="text-base font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
            No repositories yet
          </h2>
          <p className="text-sm mb-6 max-w-xs" style={{ color: 'var(--text-muted)' }}>
            Add a local repository to start visualising its dependency graph.
          </p>
          <button className="btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={15} />
            Add your first repository
          </button>
        </div>
      )}

      {/* Project grid */}
      {!isLoading && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      {/* No search results */}
      {!isLoading && (data?.total ?? 0) > 0 && filtered.length === 0 && (
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            No projects match "<span style={{ color: 'var(--text-secondary)' }}>{search}</span>"
          </p>
        </div>
      )}

      <AddProjectModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
