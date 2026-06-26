import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { FiSettings, FiInfo } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';

export default function RepositorySettings() {
  const { repoId } = useParams();
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
        { label: 'Settings' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <h1 className="page-title">{repo.name} — Settings</h1>
      </div>

      <RepositoryTabs repoId={repoId} />

      <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginTop: '2rem' }}>
        <FiSettings size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
        <h3 style={{ marginBottom: '0.75rem' }}>Repository Settings</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
          Repository settings will be available in a future update. This section will allow webhook configuration, branch protection rules, and integration management.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          <FiInfo size={14} />
          <span>Webhook and integration configuration coming soon.</span>
        </div>
      </div>
    </div>
  );
}
