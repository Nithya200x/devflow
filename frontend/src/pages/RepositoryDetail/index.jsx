import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiStar, FiGitBranch, FiExternalLink, FiCode, FiEye, FiAlertCircle,
  FiCopy, FiRefreshCw, FiLink, FiTrash2, FiSend, FiBookOpen,
  FiUser, FiCalendar, FiGitCommit, FiGitPullRequest, FiClock,
  FiTag, FiDatabase, FiShield, FiInfo
} from 'react-icons/fi';
import * as githubService from '../../services/githubService';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';
import { RepositoryTabs } from '../../components/Repository/RepositoryTabs';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function RepositoryDetail() {
  const { repoId } = useParams();
  const navigate = useNavigate();
  const [repo, setRepo] = useState(null);
  const [commits, setCommits] = useState([]);
  const [branches, setBranches] = useState([]);
  const [pulls, setPulls] = useState([]);
  const [contributors, setContributors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showDeployInfo, setShowDeployInfo] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [repoData, commitsData, branchesData, pullsData, contributorsData] = await Promise.all([
        githubService.getRepoDetails(repoId),
        githubService.getRepoCommits(repoId).catch(() => []),
        githubService.getRepoBranches(repoId).catch(() => []),
        githubService.getRepoPulls(repoId, 'all').catch(() => []),
        githubService.getRepoContributors(repoId).catch(() => []),
      ]);
      setRepo(repoData);
      setCommits(Array.isArray(commitsData) ? commitsData.slice(0, 5) : []);
      setBranches(Array.isArray(branchesData) ? branchesData : []);
      setPulls(Array.isArray(pullsData) ? pullsData.slice(0, 5) : []);
      setContributors(Array.isArray(contributorsData) ? contributorsData : []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCopyCloneUrl = () => {
    if (repo?.clone_url) {
      navigator.clipboard.writeText(repo.clone_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDeployClick = () => {
    setShowDeployInfo(true);
    setTimeout(() => setShowDeployInfo(false), 5000);
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;
  if (!repo) {
    return (
      <div>
        <Breadcrumbs items={[
          { label: 'Dashboard', path: '/' },
          { label: 'GitHub', path: '/github' },
          { label: 'Repositories', path: '/github/repos' },
          { label: 'Repository' },
        ]} />
        <EmptyState message="Repository not found" icon={FiAlertCircle} />
      </div>
    );
  }

  const topics = repo.topics_list || [];
  const languages = repo.languages || {};
  const latestCommit = commits.length > 0 ? commits[0] : null;
  const repoSize = repo.size ? (repo.size / 1024).toFixed(2) : null;

  const statItems = [
    { label: 'Repository Size', value: repoSize ? `${repoSize} MB` : 'N/A', icon: FiDatabase },
    { label: 'Stars', value: repo.stars || 0, icon: FiStar },
    { label: 'Forks', value: repo.forks || 0, icon: FiGitBranch },
    { label: 'Watchers', value: repo.watchers_count || 0, icon: FiEye },
    { label: 'Open Issues', value: repo.open_issues_count || 0, icon: FiAlertCircle },
    { label: 'Primary Language', value: repo.language || 'N/A', icon: FiCode },
    { label: 'License', value: repo.license || 'N/A', icon: FiShield },
    { label: 'Contributors', value: contributors.length || 'N/A', icon: FiUser },
  ];

  return (
    <div>
      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'GitHub', path: '/github' },
        { label: 'Repositories', path: '/github/repos' },
        { label: repo.name },
      ]} />

      {/* Repository Header */}
      <div className="glass-panel repo-header" style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
        <div className="repo-header-top">
          <div className="repo-header-info">
            <div className="repo-header-title-row">
              <h1 className="repo-name">{repo.name}</h1>
              <span className={`badge ${repo.visibility === 'private' ? 'neutral' : 'success'}`}>
                {repo.visibility}
              </span>
            </div>
            <p className="repo-owner">{repo.owner}/{repo.name}</p>
          </div>
          <div className="repo-header-meta">
            {repo.default_branch && (
              <div className="repo-meta-item">
                <FiGitBranch size={14} />
                <span>{repo.default_branch}</span>
              </div>
            )}
            {repo.language && (
              <div className="repo-meta-item">
                <FiCode size={14} />
                <span>{repo.language}</span>
              </div>
            )}
          </div>
        </div>

        {repo.description && (
          <p className="repo-description">{repo.description}</p>
        )}

        {topics.length > 0 && (
          <div className="repo-topics">
            {topics.map(t => <span key={t} className="badge neutral">{t}</span>)}
          </div>
        )}

        <div className="repo-url-row">
          <div className="repo-url-display">
            <FiLink size={14} />
            <span>{repo.html_url}</span>
          </div>
          {repo.clone_url && (
            <div className="repo-url-display">
              <FiCopy size={14} />
              <span>{repo.clone_url}</span>
            </div>
          )}
        </div>

        <div className="repo-dates">
          <span>Created: {repo.github_created_at ? new Date(repo.github_created_at).toLocaleDateString() : 'N/A'}</span>
          <span>Updated: {repo.github_updated_at ? new Date(repo.github_updated_at).toLocaleDateString() : 'N/A'}</span>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions" style={{ marginBottom: '1.5rem' }}>
        <button className="btn btn-primary" onClick={() => window.open(repo.html_url, '_blank', 'noopener,noreferrer')}>
          <FiExternalLink size={16} /> Open in GitHub
        </button>
        <button className="btn" onClick={handleCopyCloneUrl}>
          <FiCopy size={16} /> {copied ? 'Copied!' : 'Copy Clone URL'}
        </button>
        <button className="btn" onClick={fetchData}>
          <FiRefreshCw size={16} /> Refresh
        </button>
        <button className="btn btn-success" onClick={() => navigate(`/github/repos/${repoId}/commits`)}>
          <FiGitCommit size={16} /> View Commits
        </button>
        <button className="btn btn-success" onClick={() => navigate(`/github/repos/${repoId}/branches`)}>
          <FiGitBranch size={16} /> View Branches
        </button>
        <button className="btn btn-success" onClick={() => navigate(`/github/repos/${repoId}/pulls`)}>
          <FiGitPullRequest size={16} /> View Pull Requests
        </button>
        <button className="btn btn-danger" onClick={handleDeployClick}>
          <FiSend size={16} /> Deploy
        </button>
      </div>

      {showDeployInfo && (
        <div className="glass-panel deploy-notice" style={{ marginBottom: '1.5rem', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
          <FiInfo size={20} style={{ color: 'var(--warning-color)' }} />
          <div>
            <strong>Jenkins integration will be available in the next implementation phase.</strong>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              Repository ID: {repo.id} | Repository: {repo.name} | Branch: {repo.default_branch} | Latest Commit: {latestCommit?.sha?.slice(0, 7) || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <RepositoryTabs repoId={repoId} />

      {/* Main Content Grid */}
      <div className="repo-detail-grid" style={{ marginTop: '2rem' }}>
        {/* Left Column */}
        <div className="repo-detail-main">
          {/* Deployment Information */}
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <FiSend size={18} /> Deployment Information
            </h3>
            <div className="deploy-info-grid">
              <div className="deploy-info-item">
                <span className="deploy-info-label">Selected Branch</span>
                <span className="deploy-info-value">{repo.default_branch || 'N/A'}</span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Latest Commit</span>
                <span className="deploy-info-value">{latestCommit?.message?.slice(0, 50) || 'No commits yet'}</span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Latest Commit SHA</span>
                <span className="deploy-info-value">
                  {latestCommit ? (
                    <code>{latestCommit.sha?.slice(0, 7)}</code>
                  ) : 'N/A'}
                </span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Latest Commit Author</span>
                <span className="deploy-info-value">{latestCommit?.author_name || 'N/A'}</span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Latest Commit Date</span>
                <span className="deploy-info-value">
                  {latestCommit?.date ? new Date(latestCommit.date).toLocaleString() : 'N/A'}
                </span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Repository Status</span>
                <span className="deploy-info-value">
                  <span className="badge success">Connected</span>
                </span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Last Deployment</span>
                <span className="deploy-info-value" style={{ color: 'var(--text-secondary)' }}>No deployments yet</span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Deployment Environment</span>
                <span className="deploy-info-value" style={{ color: 'var(--text-secondary)' }}>Not configured</span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Current Deployment Status</span>
                <span className="deploy-info-value" style={{ color: 'var(--text-secondary)' }}>No deployments yet</span>
              </div>
            </div>

            <button className="btn btn-primary" onClick={handleDeployClick} style={{ marginTop: '1.25rem', width: '100%', padding: '1rem' }}>
              <FiSend size={18} /> Deploy Now
            </button>
          </div>

          {/* Repository Statistics */}
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <FiDatabase size={18} /> Repository Statistics
            </h3>
            <div className="repo-stats-grid">
              {statItems.map(item => (
                <div key={item.label} className="repo-stat-item">
                  <item.icon size={16} style={{ color: 'var(--accent-color)' }} />
                  <div className="repo-stat-content">
                    <span className="repo-stat-label">{item.label}</span>
                    <span className="repo-stat-value">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Languages Breakdown */}
          {Object.keys(languages).length > 0 && (
            <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <FiCode size={18} /> Languages
              </h3>
              <div className="lang-bars">
                {Object.entries(languages).map(([lang, bytes]) => {
                  const total = Object.values(languages).reduce((a, b) => a + b, 0);
                  const pct = ((bytes / total) * 100).toFixed(1);
                  return (
                    <div key={lang} className="lang-bar-item">
                      <div className="lang-bar-header">
                        <span>{lang}</span>
                        <span>{pct}%</span>
                      </div>
                      <div className="lang-bar-track">
                        <div className="lang-bar-fill" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Latest Release */}
          {repo.latest_release_tag && (
            <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <FiTag size={18} /> Latest Release
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <FiTag size={16} style={{ color: 'var(--accent-color)' }} />
                <a href={repo.latest_release_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-color)', fontWeight: 700 }}>
                  {repo.latest_release_tag}
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Recent Activity */}
        <div className="repo-detail-sidebar">
          {/* Recent Commits */}
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FiGitCommit size={16} /> Recent Commits
              </h3>
              <button className="btn btn-ghost" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                onClick={() => navigate(`/github/repos/${repoId}/commits`)}>
                View All
              </button>
            </div>
            {commits.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No commits found</p>
            ) : (
              <div className="activity-list">
                {commits.slice(0, 5).map(c => (
                  <div key={c.sha} className="activity-item">
                    <div className="activity-icon"><FiGitCommit size={14} /></div>
                    <div className="activity-content">
                      <p className="activity-text">{c.message?.slice(0, 60)}</p>
                      <p className="activity-meta">
                        <FiUser size={12} /> {c.author_name}
                        <FiClock size={12} style={{ marginLeft: '0.5rem' }} />
                        {c.date ? new Date(c.date).toLocaleDateString() : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Pull Requests */}
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FiGitPullRequest size={16} /> Recent Pull Requests
              </h3>
              <button className="btn btn-ghost" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                onClick={() => navigate(`/github/repos/${repoId}/pulls`)}>
                View All
              </button>
            </div>
            {pulls.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No pull requests found</p>
            ) : (
              <div className="activity-list">
                {pulls.slice(0, 5).map(pr => (
                  <div key={pr.id} className="activity-item">
                    <div className="activity-icon">
                      <FiGitPullRequest size={14} style={{
                        color: pr.state === 'open' ? 'var(--success-color)' : pr.merged ? 'var(--accent-color)' : 'var(--text-secondary)'
                      }} />
                    </div>
                    <div className="activity-content">
                      <p className="activity-text">#{pr.number} {pr.title?.slice(0, 50)}</p>
                      <p className="activity-meta">
                        <FiUser size={12} /> {pr.author}
                        <span className={`badge ${pr.state === 'open' ? 'warning' : pr.merged ? 'success' : 'danger'}`} style={{ marginLeft: '0.5rem', padding: '0.1rem 0.4rem', fontSize: '0.65rem' }}>
                          {pr.merged ? 'Merged' : pr.state}
                        </span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Branches Summary */}
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FiGitBranch size={16} /> Branches
              </h3>
              <button className="btn btn-ghost" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                onClick={() => navigate(`/github/repos/${repoId}/branches`)}>
                View All
              </button>
            </div>
            {branches.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No branches found</p>
            ) : (
              <div className="activity-list">
                {branches.slice(0, 5).map(b => (
                  <div key={b.name} className="activity-item">
                    <div className="activity-icon"><FiGitBranch size={14} /></div>
                    <div className="activity-content">
                      <p className="activity-text">{b.name}</p>
                      <p className="activity-meta">
                        {b.last_commit_sha && <code>{b.last_commit_sha.slice(0, 7)}</code>}
                        {b.protected && (
                          <span className="badge success" style={{ marginLeft: '0.5rem', padding: '0.1rem 0.4rem', fontSize: '0.65rem' }}>
                            Protected
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Latest Release */}
          {repo.latest_release_tag && (
            <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FiTag size={16} /> Latest Release
                </h3>
              </div>
              <div className="activity-item">
                <div className="activity-icon"><FiTag size={14} style={{ color: 'var(--accent-color)' }} /></div>
                <div className="activity-content">
                  <a href={repo.latest_release_url} target="_blank" rel="noopener noreferrer" className="activity-text" style={{ color: 'var(--accent-color)' }}>
                    {repo.latest_release_tag}
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
