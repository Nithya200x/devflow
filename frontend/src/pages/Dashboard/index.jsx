import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiServer, FiBox, FiAlertTriangle, FiActivity, FiGithub, FiGitCommit, FiGitPullRequest, FiBook, FiExternalLink } from 'react-icons/fi';
import { ResourceChart } from '../../components/Charts/ResourceChart';
import { StatCard } from '../../components/Cards/StatCard';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { usePolling } from '../../hooks/usePolling';
import * as clusterService from '../../services/clusterService';
import * as githubService from '../../services/githubService';

export default function Dashboard() {
  const navigate = useNavigate();
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ghData, setGhData] = useState(null);
  const [connectedRepos, setConnectedRepos] = useState([]);

  const chartData = [
    { name: '10:00', cpu: 45, mem: 60 },
    { name: '10:05', cpu: 55, mem: 65 },
    { name: '10:10', cpu: 40, mem: 60 },
    { name: '10:15', cpu: 80, mem: 75 },
    { name: '10:20', cpu: 65, mem: 70 },
    { name: '10:25', cpu: 50, mem: 65 },
  ];

  const fetchClusters = useCallback(async () => {
    try {
      const [cData, gh, repos] = await Promise.all([
        clusterService.getClusters(),
        githubService.getGitHubDashboard().catch(() => null),
        githubService.getConnectedRepos().catch(() => [])
      ]);
      setClusters(cData);
      setGhData(gh);
      setConnectedRepos(repos);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchClusters(); }, [fetchClusters]);
  usePolling(fetchClusters, 5000, !error);

  const totalPods = clusters.reduce((sum, c) => sum + (c.pod_count || 0), 0);
  const openIncidents = 1;

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchClusters} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Platform Overview</h1>
          <p className="page-subtitle">Real-time metrics and system health at a glance.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <StatCard icon={FiServer} label="Active Clusters" value={clusters.length} color="blue" />
        <StatCard icon={FiBox} label="Total Pods" value={totalPods} color="green" />
        <StatCard icon={FiAlertTriangle} label="Open Incidents" value={openIncidents} color="red" />
      </div>

      {ghData && ghData.connected && (
        <>
          <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
            <div className="glass-panel stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/github/repos')}>
              <div className="stat-icon blue"><FiGithub /></div>
              <div className="stat-content">
                <h3>Connected Repos</h3>
                <p>{ghData.connected_repos}</p>
              </div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-icon green"><FiGitCommit /></div>
              <div className="stat-content">
                <h3>Latest Commit</h3>
                <p style={{ fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {ghData.latest_commit ? `${ghData.latest_commit.repo}: ${ghData.latest_commit.message?.slice(0, 30)}...` : 'N/A'}
                </p>
              </div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-icon red"><FiGitPullRequest /></div>
              <div className="stat-content">
                <h3>Open PRs</h3>
                <p>{ghData.open_prs}</p>
              </div>
            </div>
          </div>

          {connectedRepos.length > 0 && (
            <div className="glass-panel" style={{ marginBottom: '2.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <FiBook size={16} /> Connected Repositories
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {connectedRepos.slice(0, 5).map(r => (
                  <div key={r.id} className="dashboard-repo-row" onClick={() => navigate(`/github/repos/${r.id}`)}
                    style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', transition: 'background 0.2s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}>
                    <div>
                      <div style={{ fontWeight: 600, color: '#fff' }}>{r.name}</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{r.owner}/{r.name}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      <span>{r.language}</span>
                      <span className={`badge ${r.visibility === 'private' ? 'neutral' : 'success'}`} style={{ fontSize: '0.65rem' }}>{r.visibility}</span>
                      <FiExternalLink size={14} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <div className="glass-panel" style={{ height: '450px' }}>
        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiActivity /> Cluster Resource Usage (Avg)
        </h3>
        <ResourceChart data={chartData} />
      </div>
    </div>
  );
}
