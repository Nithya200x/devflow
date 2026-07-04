import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiGithub, FiLink, FiTrash2, FiStar, FiGitBranch, FiExternalLink, FiInfo, FiCheckCircle, FiArrowRight } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { RepositoryCard } from '../../components/Repository/RepositoryCard';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';

export default function Github() {
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [status, setStatus] = useState(null);
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [repoLoading, setRepoLoading] = useState(false);
  const [error, setError] = useState(null);
  const [connectError, setConnectError] = useState('');
  const [connected, setConnected] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await githubService.getGitHubStatus();
      setStatus(data);
      setConnected(data.connected);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleConnect = async (e) => {
    e.preventDefault();
    if (!token.trim()) {
      setConnectError('Please enter a GitHub Personal Access Token');
      return;
    }
    setConnectError('');
    setLoading(true);
    try {
      const data = await githubService.connectGitHub(token);
      setConnected(true);
      setStatus({ connected: true, github_username: data.github_username });
      setToken('');
      setError(null);
    } catch (err) {
      setConnectError(err.response?.data?.msg || 'Failed to connect to GitHub');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    try {
      await githubService.disconnectGitHub();
      setConnected(false);
      setStatus({ connected: false, github_username: '' });
      setRepos([]);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRepos = async () => {
    setRepoLoading(true);
    try {
      const data = await githubService.getGitHubRepos();
      setRepos(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setRepoLoading(false);
    }
  };

  useEffect(() => {
    if (connected) fetchRepos();
  }, [connected]);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'GitHub' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <div>
          <h1 className="page-title">GitHub Integration</h1>
          <p className="page-subtitle">Connect your GitHub account to enable repository management and CI/CD triggers.</p>
        </div>
      </div>

      {error && <NetworkError error={error} onRetry={fetchStatus} />}

      <div className="glass-panel" style={{ marginBottom: '2.5rem' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <FiGithub /> {connected ? 'Connected Account' : 'Connect Your GitHub Account'}
        </h3>

        {connected ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="user-avatar" style={{ width: '48px', height: '48px', fontSize: '1.25rem', background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' }}>
                <FiGithub size={24} />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#fff' }}>{status?.github_username}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  <FiCheckCircle size={12} style={{ color: 'var(--success-color)', marginRight: '4px' }} />
                  Connected
                </div>
              </div>
            </div>
            <button className="btn btn-danger" onClick={handleDisconnect}>
              <FiTrash2 size={16} /> Disconnect GitHub
            </button>
          </div>
        ) : (
          <form onSubmit={handleConnect}>
            <div className="input-group">
              <label>GitHub Personal Access Token</label>
              <input
                type="password"
                value={token}
                onChange={e => setToken(e.target.value)}
                placeholder="ghp_..."
                required
              />
              <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <FiInfo size={14} />
                Token needs <strong>repo</strong> and <strong>read:user</strong> scopes.
                <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-color)', marginLeft: '0.25rem' }}>
                  Create one here <FiExternalLink size={12} style={{ display: 'inline' }} />
                </a>
              </div>
            </div>
            {connectError && <div className="badge danger" style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>{connectError}</div>}
            <button type="submit" className="btn btn-primary">
              <FiLink size={16} /> Connect
            </button>
          </form>
        )}
      </div>

      {connected && (
        <div>
          <div className="page-header" style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Repositories</h2>
            <button className="btn" onClick={fetchRepos} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
              Refresh
            </button>
          </div>

          {repoLoading ? (
            <LoadingSpinner />
          ) : repos.length === 0 ? (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
              <FiGithub size={40} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
              <p style={{ color: 'var(--text-secondary)' }}>No repositories found or failed to load.</p>
              <button className="btn btn-primary" onClick={fetchRepos} style={{ marginTop: '1rem' }}>Retry</button>
            </div>
          ) : (
            <div className="grid-cards">
              {repos.map((repo) => {
                const cardRepo = {
                  ...repo,
                  owner: repo.owner || repo.full_name?.split('/')[0],
                  visibility: repo.private ? 'private' : 'public',
                  stars: repo.stars,
                  forks: repo.forks
                };
                return (
                  <RepositoryCard
                    key={repo.id}
                    repository={cardRepo}
                    connected={false}
                    disableNavigation
                  />
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
