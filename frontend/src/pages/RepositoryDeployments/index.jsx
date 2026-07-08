import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  FiLayers, FiInfo, FiCheck, FiX, FiClock, FiLoader,
  FiExternalLink, FiRefreshCw
} from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';

const STATUS_ICONS = {
  success: <FiCheck size={16} style={{ color: 'var(--success-color)' }} />,
  failed: <FiX size={16} style={{ color: 'var(--danger-color)' }} />,
  running: <FiLoader size={16} style={{ color: 'var(--warning-color)', animation: 'spin 1s linear infinite' }} />,
  aborted: <FiX size={16} style={{ color: 'var(--text-secondary)' }} />,
  queued: <FiClock size={16} style={{ color: 'var(--warning-color)' }} />,
};

const STATUS_BADGE = {
  success: 'success',
  failed: 'danger',
  running: 'warning',
  aborted: 'neutral',
  queued: 'warning',
};

const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '-';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
};

export default function RepositoryDeployments() {
  const { repoId } = useParams();
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [builds, setBuilds] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      const data = await githubService.getRepoDetails(repoId);
      setRepo(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;
  if (!repo) return null;

  return (
    <div>
      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'GitHub', path: '/github' },
        { label: 'Repositories', path: '/github/repos' },
        { label: repo.name, path: `/github/repos/${repoId}` },
        { label: 'Deployments' },
      ]} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
        <h1 className="page-title" style={{ margin: 0 }}>{repo.name} — Deployments</h1>
        <button className="btn" onClick={fetchBuilds}>
          <FiRefreshCw size={16} /> Refresh
        </button>
      </div>

      <RepositoryTabs repoId={repoId} />

      <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginTop: '2rem' }}>
        <FiLayers size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
        <h3 style={{ marginBottom: '0.75rem' }}>No Deployments</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
          No deployment history available.
        </p>
      </div>
    </div>
  );
}
