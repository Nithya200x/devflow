import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiGitCommit, FiUser, FiCalendar, FiCopy } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function Commits() {
  const { repoId } = useParams();
  const navigate = useNavigate();
  const [commits, setCommits] = useState([]);
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [data, repoData] = await Promise.all([
        githubService.getRepoCommits(repoId),
        githubService.getRepoDetails(repoId).catch(() => null)
      ]);
      setCommits(data);
      setRepo(repoData);
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

  return (
    <div>
      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'GitHub', path: '/github' },
        { label: 'Repositories', path: '/github/repos' },
        { label: repo?.name || 'Repository', path: `/github/repos/${repoId}` },
        { label: 'Commits' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <h1 className="page-title">Commits</h1>
        <p className="page-subtitle">Recent commit history</p>
      </div>

      <RepositoryTabs repoId={repoId} />

      <div style={{ marginTop: '1.5rem' }}>
        {commits.length === 0 ? <EmptyState message="No commits found" /> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {commits.map(c => (
              <div className="glass-panel" key={c.sha} style={{ padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FiGitCommit size={16} style={{ color: 'var(--accent-color)' }} />
                    <code style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{c.sha}</code>
                    <button className="btn" style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem', cursor: 'pointer' }}
                      onClick={() => navigator.clipboard.writeText(c.sha)}>
                      <FiCopy size={12} />
                    </button>
                  </div>
                </div>
                <p style={{ fontWeight: 600, color: '#fff', marginBottom: '0.5rem' }}>{c.message}</p>
                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <FiUser size={14} /> {c.author_name}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <FiCalendar size={14} /> {new Date(c.date).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
