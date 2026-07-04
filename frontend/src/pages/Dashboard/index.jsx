import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiBox, FiServer, FiAlertTriangle, FiCpu, FiGithub, FiActivity,
  FiGitBranch, FiBarChart2, FiShield, FiTerminal, FiLayers, FiDollarSign
} from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import * as clusterService from '../../services/clusterService';
import * as githubService from '../../services/githubService';
import * as projectService from '../../services/projectService';
import * as orchestrationService from '../../services/orchestrationService';

const HEALTH_SERVICES = [
  { key: 'github', label: 'GitHub', icon: FiGithub },
  { key: 'docker', label: 'Docker', icon: FiBox },
  { key: 'jenkins', label: 'Jenkins', icon: FiTerminal },
  { key: 'kubernetes', label: 'Kubernetes', icon: FiServer },
  { key: 'prometheus', label: 'Prometheus', icon: FiBarChart2 },
  { key: 'grafana', label: 'Grafana', icon: FiActivity },
  { key: 'groq', label: 'Groq AI', icon: FiCpu },
];

function HealthStatus({ name, icon: Icon, status }) {
  const dotClass = status === 'online' || status === 'healthy' || status === 'running' || status === 'active' || status === 'streaming' || status === 'connected'
    ? 'online' : status === 'degraded' || status === 'warning' ? 'warning' : 'offline';
  const label = typeof status === 'string' ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
  return (
    <div className="health-item">
      <div className={`health-dot ${dotClass}`} />
      <Icon size={14} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
      <span className="health-label">{name}</span>
      <span className={`health-status ${dotClass}`}>{label}</span>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [clusters, setClusters] = useState([]);
  const [projects, setProjects] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [ghStatus, setGhStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [now] = useState(new Date());

  const hour = now.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  const fetchAll = useCallback(async () => {
    try {
      const [cData, pData, incData, gh, analysisData] = await Promise.all([
        clusterService.getClusters().catch(() => []),
        projectService.getProjects().catch(() => []),
        orchestrationService.getIncidents().catch(() => []),
        githubService.getGitHubDashboard().catch(() => null),
        orchestrationService.listDbAnalyses().catch(() => ({ analyses: [] })),
      ]);
      setClusters(Array.isArray(cData) ? cData : []);
      setProjects(Array.isArray(pData) ? pData : []);
      setIncidents(Array.isArray(incData) ? incData : []);
      setGhStatus(gh);
      setAnalyses(analysisData?.analyses || []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchAll} />;

  const totalPods = clusters.reduce((sum, c) => sum + (c.pod_count || 0), 0);
  const openIncidents = incidents.filter(i => i.status === 'open' || i.status === 'investigating').length;
  const connectedRepos = ghStatus?.connected_repos || projects.length;
  const aiFixes = analyses.length;

  const systemHealth = {
    github: ghStatus?.connected ? 'online' : 'offline',
    docker: totalPods > 0 ? 'healthy' : 'degraded',
    jenkins: 'running',
    kubernetes: clusters.length > 0 ? 'healthy' : 'degraded',
    prometheus: 'streaming',
    grafana: 'connected',
    groq: aiFixes > 0 ? 'active' : 'online',
  };

  const recentIncidents = incidents.slice(0, 5);
  const recentAnalyses = analyses.slice(0, 3);

  return (
    <div>
      {/* Welcome */}
      <div className="page-header">
        <div>
          <h1 className="page-title">{greeting}, Admin</h1>
          <p className="page-subtitle">DevFlow Command Center · Platform Status Overview</p>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stat-grid stagger-children">
        <div className="glass-panel stat-card card-hover" onClick={() => navigate('/github/repos')}>
          <div className="stat-icon-wrap blue"><FiGitBranch size={22} /></div>
          <div className="stat-body">
            <h3>Active Projects</h3>
            <p>{connectedRepos}</p>
            {connectedRepos > 0 && <div className="stat-trend up"><FiActivity size={12} /> Operational</div>}
          </div>
        </div>
        <div className="glass-panel stat-card card-hover" onClick={() => navigate('/monitoring')}>
          <div className="stat-icon-wrap green"><FiServer size={22} /></div>
          <div className="stat-body">
            <h3>Healthy Services</h3>
            <p>{Object.values(systemHealth).filter(s => s !== 'offline' && s !== 'degraded').length}/7</p>
            <div className="stat-trend up"><FiActivity size={12} /> All systems nominal</div>
          </div>
        </div>
        <div className="glass-panel stat-card card-hover" onClick={() => navigate('/orchestration/incidents')}>
          <div className="stat-icon-wrap red"><FiAlertTriangle size={22} /></div>
          <div className="stat-body">
            <h3>Active Incidents</h3>
            <p>{openIncidents}</p>
            {openIncidents > 0 && <div className="stat-trend down"><FiActivity size={12} /> Needs attention</div>}
            {openIncidents === 0 && <div className="stat-trend up"><FiActivity size={12} /> All clear</div>}
          </div>
        </div>
        <div className="glass-panel stat-card card-hover" onClick={() => navigate('/orchestration/root-cause')}>
          <div className="stat-icon-wrap violet"><FiCpu size={22} /></div>
          <div className="stat-body">
            <h3>AI Fixes Generated</h3>
            <p>{aiFixes}</p>
            {aiFixes > 0 && <div className="stat-trend up"><FiActivity size={12} /> Groq LLM active</div>}
          </div>
        </div>
      </div>

      <div className="grid-2-cols" style={{ marginBottom: '1.25rem' }}>
        {/* System Health Matrix */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiShield /> System Health Matrix
          </h3>
          <div className="health-matrix">
            {HEALTH_SERVICES.map(svc => (
              <HealthStatus key={svc.key} name={svc.label} icon={svc.icon} status={systemHealth[svc.key]} />
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiActivity /> Recent Activity
          </h3>
          <div className="activity-feed">
            {ghStatus?.latest_commit && (
              <div className="activity-row">
                <div className="activity-dot blue"><FiGitBranch size={14} /></div>
                <div className="activity-desc">
                  <div className="activity-text">{ghStatus.latest_commit.message || 'Commit pushed'}</div>
                  <div className="activity-time">{ghStatus.latest_commit.repo || 'Repository'} · Just now</div>
                </div>
              </div>
            )}

            {recentAnalyses.map((a, i) => (
              <div key={i} className="activity-row">
                <div className="activity-dot violet"><FiCpu size={14} /></div>
                <div className="activity-desc">
                  <div className="activity-text">AI RCA generated · {a.root_cause || 'Analysis complete'}</div>
                  <div className="activity-time">
                    Incident {a.incident_id} · {a.analyzed_at ? new Date(a.analyzed_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : 'Recently'}
                  </div>
                </div>
              </div>
            ))}

            {recentIncidents.map((inc, i) => (
              <div key={i} className="activity-row">
                <div className={`activity-dot ${inc.severity === 'critical' || inc.severity === 'high' ? 'red' : inc.severity === 'medium' ? 'amber' : 'green'}`}>
                  <FiAlertTriangle size={14} />
                </div>
                <div className="activity-desc">
                  <div className="activity-text">{inc.summary?.slice(0, 80) || `Incident ${inc.incident_id}`}</div>
                  <div className="activity-time">
                    <span className={`badge ${inc.severity === 'critical' || inc.severity === 'high' ? 'danger' : inc.severity === 'medium' ? 'warning' : 'success'}`} style={{ fontSize: '0.6rem', padding: '0.1rem 0.4rem' }}>
                      {inc.severity}
                    </span>
                    {' '}· {inc.created_at ? new Date(inc.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : 'Recently'}
                  </div>
                </div>
              </div>
            ))}

            {!ghStatus?.latest_commit && recentAnalyses.length === 0 && recentIncidents.length === 0 && (
              <div className="empty-state" style={{ padding: '1.5rem' }}>
                <h3>No recent activity</h3>
                <p>Activity will appear here as events are processed</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Connected Projects */}
      {projects.length > 0 && (
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <FiBox /> Connected Projects
            </h3>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/github/repos')}>
              View All
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {projects.slice(0, 6).map(p => (
              <div key={p.id} className="card-hover"
                onClick={() => navigate(`/repositories/${p.id}`)}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 1rem', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.name}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{p.full_name}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {p.language && <span className="badge neutral" style={{ fontSize: '0.6rem' }}>{p.language}</span>}
                  <FiLayers size={14} style={{ color: 'var(--accent-blue)' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!ghStatus?.connected && (
        <div className="glass-panel" style={{ marginTop: '1.25rem', textAlign: 'center', padding: '2.5rem', borderColor: 'rgba(59, 130, 246, 0.15)' }}>
          <FiGithub size={32} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Connect Your GitHub Account</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem', maxWidth: '400px', margin: '0 auto 1rem' }}>
            Connect your GitHub account to start managing repositories, enable CI/CD monitoring, and unlock AI-powered incident analysis.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/github')}>
            <FiGithub size={16} /> Connect GitHub
          </button>
        </div>
      )}
    </div>
  );
}
