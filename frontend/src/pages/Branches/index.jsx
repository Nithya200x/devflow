import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiGitBranch, FiShield, FiCopy } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function Branches() {
  const { repoId } = useParams();
  const navigate = useNavigate();
  const [branches, setBranches] = useState([]);
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [data, repoData] = await Promise.all([
        githubService.getRepoBranches(repoId),
        githubService.getRepoDetails(repoId).catch(() => null)
      ]);
      setBranches(data);
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
        { label: 'Branches' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <h1 className="page-title">Branches</h1>
        <p className="page-subtitle">Repository branches and protection status.</p>
      </div>

      <RepositoryTabs repoId={repoId} />

      <div style={{ marginTop: '1.5rem' }}>
        {branches.length === 0 ? <EmptyState message="No branches found" /> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {branches.map(b => (
              <div className="glass-panel" key={b.name} style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <FiGitBranch size={18} style={{ color: 'var(--accent-color)' }} />
                  <div>
                    <div style={{ fontWeight: 700, color: '#fff' }}>{b.name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <code style={{ fontSize: '0.75rem' }}>{b.last_commit_sha?.slice(0, 7)}</code>
                      <button className="btn" style={{ padding: '0.1rem 0.3rem', fontSize: '0.65rem' }}
                        onClick={() => navigator.clipboard.writeText(b.last_commit_sha)}>
                        <FiCopy size={10} />
                      </button>
                    </div>
                  </div>
                </div>
                {b.protected && (
                  <span className="badge success"><FiShield size={12} /> Protected</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
