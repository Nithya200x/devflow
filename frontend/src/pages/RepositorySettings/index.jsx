import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { FiSettings, FiGithub, FiShield, FiGitBranch } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

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

      <div className="glass-panel" style={{ padding: '2rem', marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiSettings /> Repository Configuration
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
            <FiGithub size={20} style={{ color: 'var(--text-secondary)' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>GitHub Webhook</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Not configured. Webhooks enable automatic event-driven deployment triggers.</div>
            </div>
            <span className="badge neutral">Pending</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
            <FiShield size={20} style={{ color: 'var(--text-secondary)' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Branch Protection Rules</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Not configured. Configure via GitHub repository settings.</div>
            </div>
            <span className="badge neutral">External</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
            <FiGitBranch size={20} style={{ color: 'var(--text-secondary)' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Deployment Branch</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Default: {repo.default_branch || 'main'}. Change via repository configuration.</div>
            </div>
            <span className="badge success">{repo.default_branch || 'main'}</span>
          </div>
        </div>
        <EmptyState
          message="Settings management coming in a future update"
          description="Webhook configuration, branch protection rules, and integration management will be available here."
        />
      </div>
    </div>
  );
}
