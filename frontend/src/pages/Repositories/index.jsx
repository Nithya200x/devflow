import { useState, useEffect, useCallback } from 'react';
import { FiSearch } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { RepositoryCard } from '../../components/Repository/RepositoryCard';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function Repositories() {
  const [connected, setConnected] = useState([]);
  const [available, setAvailable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [c, a] = await Promise.all([
        githubService.getConnectedRepos(),
        githubService.getGitHubRepos()
      ]);
      setConnected(c);
      setAvailable(a);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleConnect = async (owner, name) => {
    try {
      await githubService.connectRepo(owner, name);
      await fetchData();
    } catch (err) {
      setError(err);
    }
  };

  const handleDisconnect = async (repoId) => {
    try {
      await githubService.disconnectRepo(repoId);
      await fetchData();
    } catch (err) {
      setError(err);
    }
  };

  const connectedIds = new Set(connected.map(r => r.repo_id));
  const filtered = available.filter(r =>
    r.full_name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'GitHub', path: '/github' },
        { label: 'Repositories' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <div>
          <h1 className="page-title">Repositories</h1>
          <p className="page-subtitle">Connect and manage GitHub repositories.</p>
        </div>
      </div>

      {error && <NetworkError error={error} onRetry={fetchData} />}

      {connected.length > 0 && (
        <>
          <h3 style={{ marginBottom: '1rem' }}>Connected Repositories ({connected.length})</h3>
          <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
            {connected.map(r => (
              <RepositoryCard
                key={r.id}
                repository={r}
                connected={true}
                onDisconnect={handleDisconnect}
              />
            ))}
          </div>
        </>
      )}

      {connected.length === 0 && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginBottom: '2.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>No Repository Connected</p>
          <button className="btn btn-primary" onClick={() => navigate('/github')}>
            Browse GitHub Repositories
          </button>
        </div>
      )}

      <h3 style={{ marginBottom: '1rem' }}>Available Repositories</h3>
      <div className="input-group" style={{ maxWidth: '400px', marginBottom: '1.5rem' }}>
        <div style={{ position: 'relative' }}>
          <FiSearch style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="Search repositories..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: '2.5rem' }}
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="No repositories found" />
      ) : (
        <div className="grid-cards">
          {filtered.map(r => (
            <RepositoryCard
              key={r.id}
              repository={r}
              connected={connectedIds.has(r.id)}
              onConnect={handleConnect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
