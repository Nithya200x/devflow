import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  FiLayers, FiInfo, FiCheck, FiX, FiClock, FiLoader,
  FiExternalLink, FiRefreshCw
} from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import * as jenkinsService from '../../services/jenkinsService';
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
  const [jenkinsError, setJenkinsError] = useState(null);
  const [jenkinsHealth, setJenkinsHealth] = useState(null);

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

  const fetchBuilds = useCallback(async () => {
    try {
      const healthRes = await jenkinsService.getJenkinsHealth();
      setJenkinsHealth(healthRes.data);
      if (healthRes.data?.connected) {
        const buildsRes = await jenkinsService.getBuildHistory(20);
        setBuilds(buildsRes.data || []);
        setJenkinsError(null);
      }
    } catch (err) {
      setJenkinsError(err.response?.data?.msg || 'Jenkins not available');
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { if (!loading && repo) fetchBuilds(); }, [loading, repo, fetchBuilds]);

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

      {!jenkinsHealth?.connected ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginTop: '2rem' }}>
          <FiLayers size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.75rem' }}>Jenkins Not Connected</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
            {jenkinsError || 'Jenkins server is not configured. Set JENKINS_URL, JENKINS_USERNAME, and JENKINS_API_TOKEN to enable deployments.'}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            <FiInfo size={14} />
            <span>Deployments are managed via Jenkins CI/CD pipeline.</span>
          </div>
        </div>
      ) : builds.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginTop: '2rem' }}>
          <FiLayers size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.75rem' }}>No Builds Yet</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
            No builds have been triggered yet. Use the Deploy button on the repository detail page to start a build.
          </p>
        </div>
      ) : (
        <div className="glass-panel" style={{ marginTop: '2rem', overflow: 'hidden' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiLayers size={18} /> Build History
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="deployments-table">
              <thead>
                <tr>
                  <th>Build #</th>
                  <th>Status</th>
                  <th>Result</th>
                  <th>Duration</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {builds.map((b) => (
                  <tr key={b.build_number}>
                    <td><strong>#{b.build_number}</strong></td>
                    <td>
                      <span className={`badge ${STATUS_BADGE[b.status] || 'neutral'}`}>
                        {STATUS_ICONS[b.status] || null} {b.status}
                      </span>
                    </td>
                    <td>{b.result || '-'}</td>
                    <td>{formatDuration(b.duration_seconds)}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {b.timestamp ? new Date(b.timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '-'}
                    </td>
                    <td>
                      {b.url && (
                        <a href={b.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                          <FiExternalLink size={14} /> Open
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
