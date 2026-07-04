import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiGithub, FiStar, FiGitBranch, FiCode, FiCpu, FiExternalLink, FiPlus, FiCheckCircle, FiX } from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

function SetupOverlay({ name, status, errorMsg }) {
  return (
    <div className="setup-overlay">
      <div className="setup-card">
        {status === 'connecting' && (
          <>
            <div className="setup-icon">
              <div className="animate-spin" style={{ width: 28, height: 28, border: '3px solid rgba(139,92,246,0.2)', borderTopColor: 'var(--accent-violet)', borderRadius: '50%' }} />
            </div>
            <h2>Connecting {name}</h2>
            <p>Setting up your DevFlow managed project</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="setup-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
              <FiCheckCircle size={28} />
            </div>
            <h2>Connected {name}</h2>
            <p>Redirecting to dashboard...</p>
          </>
        )}
        {status === 'failed' && (
          <>
            <div className="setup-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' }}>
              <FiX size={28} />
            </div>
            <h2>Connection Failed</h2>
            <p>{errorMsg || 'An error occurred while connecting the repository'}</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function Repositories() {
  const navigate = useNavigate();
  const [connected, setConnected] = useState([]);
  const [available, setAvailable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [connecting, setConnecting] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadData = useCallback(async (cancelled) => {
    try {
      setLoading(true);
      const [c, a] = await Promise.all([
        githubService.getConnectedRepos().catch(() => []),
        githubService.getGitHubRepos().catch(() => []),
      ]);
      if (cancelled?.()) return;
      setConnected(Array.isArray(c) ? c : []);
      setAvailable(Array.isArray(a) ? a : []);
      setError(null);
    } catch (err) {
      if (!cancelled?.()) setError(err);
    } finally {
      if (!cancelled?.()) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData(() => cancelled);
    return () => { cancelled = true; };
  }, [loadData, refreshKey]);

  const handleConnect = async (owner, name) => {
    const repoName = `${owner}/${name}`;
    setConnecting({ name: repoName, status: 'connecting' });
    try {
      const result = await githubService.connectRepo(owner, name);
      if (result?.project_id) {
        setConnecting({ name: repoName, status: 'success' });
        setTimeout(() => {
          setConnecting(null);
          navigate(`/repositories/${result.project_id}`);
        }, 1000);
      } else {
        setConnecting(null);
        setRefreshKey(k => k + 1);
      }
    } catch (err) {
      setConnecting({ name: repoName, status: 'failed', errorMsg: err.message || 'Failed to connect repository' });
    }
  };

  const handleDisconnect = async (repoId) => {
    try {
      await githubService.disconnectRepo(repoId);
      setRefreshKey(k => k + 1);
    } catch (err) {
      setError(err);
    }
  };

  const connectedIds = new Set(connected.map(r => r.repo_id));
  const filtered = available.filter(r =>
    r.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    r.name?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      {connecting && <SetupOverlay name={connecting.name} status={connecting.status} errorMsg={connecting.errorMsg} />}

      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'Repositories' },
      ]} />

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <div>
          <h1 className="page-title">Repositories</h1>
          <p className="page-subtitle">Connect repositories to enable monitoring, CI/CD, and AI analysis.</p>
        </div>
      </div>

      {error && <NetworkError error={error} onRetry={() => setRefreshKey(k => k + 1)} />}

      {connected.length > 0 && (
        <div style={{ marginBottom: '2.5rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiCpu size={16} style={{ color: 'var(--accent-violet)' }} />
            DevFlow Managed Projects ({connected.length})
          </h3>
          <div className="grid-cards">
            {connected.map(r => (
              <div key={r.id} className="glass-panel card-hover"
                onClick={() => r.project_id ? navigate(`/repositories/${r.project_id}`) : null}
                style={{ cursor: r.project_id ? 'pointer' : 'default' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ margin: 0, fontSize: '1rem', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.name}</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                      {r.full_name || `${r.github_owner || r.owner}/${r.name}`}
                    </p>
                  </div>
                  <span className="badge connected"><FiCpu size={10} /> Managed</span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', flex: 1, marginBottom: '1rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {r.description || 'Connected project with full monitoring enabled'}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {r.language && <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiCode size={14} /> {r.language}</span>}
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiStar size={14} /> {r.stars || 0}</span>
                  </div>
                  <button className="btn btn-danger btn-sm" onClick={e => { e.stopPropagation(); handleDisconnect(r.id); }}>
                    Disconnect
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {connected.length === 0 && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '2.5rem', marginBottom: '2.5rem', borderColor: 'rgba(139, 92, 246, 0.08)' }}>
          <FiCpu size={36} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>No Connected Repositories</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '360px', margin: '0 auto 1rem' }}>
            Connect a GitHub repository to enable CI/CD monitoring, Kubernetes tracking, incident detection, and AI root cause analysis.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/github')}>
            <FiGithub size={16} /> Connect GitHub Account
          </button>
        </div>
      )}

      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', margin: 0 }}>
            GitHub Repositories ({filtered.length})
          </h3>
          <button className="btn btn-ghost btn-sm" onClick={() => setRefreshKey(k => k + 1)}>
            Refresh
          </button>
        </div>
        <div className="input-group" style={{ maxWidth: '400px', margin: 0 }}>
          <div style={{ position: 'relative' }}>
            <FiSearch style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search repositories..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: '2.75rem' }}
            />
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="No repositories found" icon={FiGithub} />
      ) : (
        <div className="grid-cards">
          {filtered.map(r => {
            const isConnected = connectedIds.has(r.id);
            return (
              <div key={r.id} className={`glass-panel card-hover${isConnected ? ' repo-card-connected' : ''}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ margin: 0, fontSize: '1rem', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.name}
                      {isConnected && <span className="badge connected" style={{ marginLeft: '0.5rem', fontSize: '0.6rem' }}><FiCpu size={10} /> Managed</span>}
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                      {r.owner || r.full_name?.split('/')[0]}
                    </p>
                  </div>
                  <span className={`badge ${r.visibility === 'private' || r.private ? 'neutral' : 'success'}`}>
                    {r.visibility === 'private' || r.private ? 'Private' : 'Public'}
                  </span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {r.description || 'No description'}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {r.language && <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiCode size={14} /> {r.language}</span>}
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiStar size={14} /> {r.stars || 0}</span>
                    {r.forks !== undefined && <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiGitBranch size={14} /> {r.forks}</span>}
                  </div>
                  <div style={{ display: 'flex', gap: '0.4rem' }} onClick={e => e.stopPropagation()}>
                    <button className="btn btn-ghost btn-sm"
                      onClick={() => window.open(r.html_url, '_blank', 'noopener,noreferrer')}>
                      <FiExternalLink size={12} />
                    </button>
                    {isConnected ? (
                      <button className="btn btn-primary btn-sm" onClick={() => {
                    const match = connected.find(c => c.repo_id === r.id);
                    if (match?.project_id) navigate(`/repositories/${match.project_id}`);
                  }}>
                        <FiCpu size={12} /> Open
                      </button>
                    ) : (
                      <button className="btn btn-primary btn-sm"
                        onClick={() => handleConnect(r.owner || r.full_name?.split('/')[0], r.name)}
                        disabled={connecting !== null}>
                        {connecting?.name === `${r.owner || r.full_name?.split('/')[0]}/${r.name}` && connecting?.status === 'connecting' ? (
                          <><span className="animate-spin" style={{ display: 'inline-block', width: 12, height: 12, border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#fff', borderRadius: '50%' }} /> Syncing</>
                        ) : (
                          <><FiPlus size={12} /> Connect</>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}