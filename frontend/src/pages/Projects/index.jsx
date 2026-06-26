import { useState, useEffect, useCallback } from 'react';
import * as projectService from '../../services/projectService';
import { DataTable } from '../../components/Tables/DataTable';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjects = useCallback(async () => {
    try {
      const data = await projectService.getProjects();
      setProjects(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const columns = [
    { key: 'id', label: 'ID', style: { color: 'var(--text-secondary)' }, render: (row) => `#${row.id}` },
    { key: 'name', label: 'Name', render: (row) => <strong>{row.name}</strong> },
    {
      key: 'repository_url',
      label: 'Repository',
      render: (row) => (
        <a href={row.repository_url} target="_blank" rel="noreferrer" style={{color: 'var(--accent-color)', textDecoration: 'none'}}>
          {row.repository_url}
        </a>
      ),
    },
    { key: 'description', label: 'Description', style: { color: 'var(--text-secondary)' } },
  ];

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchProjects} />;
  if (!projects.length) return <EmptyState message="No projects found" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-subtitle">Manage connected repositories and services.</p>
        </div>
      </div>
      <DataTable columns={columns} data={projects} />
    </div>
  );
}
