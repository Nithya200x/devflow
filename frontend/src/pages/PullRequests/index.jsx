import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiGitPullRequest, FiUser, FiCalendar } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function PullRequests() {
  const { repoId } = useParams();
  const navigate = useNavigate();
  const [prs, setPrs] = useState([]);
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  const fetchData = useCallback(async () => {
    try {
      const [data, repoData] = await Promise.all([
        githubService.getRepoPulls(repoId, filter),
        githubService.getRepoDetails(repoId).catch(() => null)
      ]);
      setPrs(data);
      setRepo(repoData);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [repoId, filter]);

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
        { label: 'Pull Requests' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <div>
          <h1 className="page-title">Pull Requests</h1>
          <p className="page-subtitle">Review and manage pull requests.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['all', 'open', 'closed'].map(s => (
            <button key={s} className={`btn ${filter === s ? 'btn-primary' : ''}`}
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
              onClick={() => setFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <RepositoryTabs repoId={repoId} />

      <div style={{ marginTop: '1.5rem' }}>
        {prs.length === 0 ? <EmptyState message="No pull requests found" /> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {prs.map(pr => (
              <div className="glass-panel" key={pr.id} style={{ padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FiGitPullRequest size={16} style={{ color: pr.state === 'open' ? 'var(--success-color)' : pr.merged ? 'var(--accent-color)' : 'var(--text-secondary)' }} />
                    <h3 style={{ margin: 0, fontSize: '1rem', color: '#fff' }}>#{pr.number} {pr.title}</h3>
                  </div>
                  <span className={`badge ${pr.state === 'open' ? 'warning' : pr.merged ? 'success' : 'danger'}`}>
                    {pr.merged ? 'Merged' : pr.state}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <FiUser size={14} /> {pr.author}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <FiCalendar size={14} /> Created: {new Date(pr.created_at).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' })}
                  </span>
                  <span>{pr.head_branch} → {pr.base_branch}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
