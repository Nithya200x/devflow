import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiBox, FiServer, FiAlertTriangle, FiCpu, FiGithub, FiActivity,
  FiGitBranch, FiBarChart2, FiShield, FiLayers
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { HealthStatus } from '../../components/Common/StatusBadge';
import * as githubService from '../../services/githubService';
import * as projectService from '../../services/projectService';
import * as kubernetesService from '../../services/kubernetesService';
import * as dockerService from '../../services/dockerService';
import * as prometheusService from '../../services/prometheusService';
import * as grafanaService from '../../services/grafanaService';
import * as alertmanagerService from '../../services/alertmanagerService';
import * as diagnosticsService from '../../services/diagnosticsService';
import * as orchestrationService from '../../services/orchestrationService';
import { listHealthScores } from '../../services/repositoryHealthService';
import HealthScore from '../../components/Common/HealthScore';

const HEALTH_SERVICES = [
  { key: 'github', label: 'GitHub', icon: FiGithub },
  { key: 'docker', label: 'Docker', icon: FiBox },
  { key: 'kubernetes', label: 'Kubernetes', icon: FiServer },
  { key: 'prometheus', label: 'Prometheus', icon: FiBarChart2 },
  { key: 'grafana', label: 'Grafana', icon: FiActivity },
  { key: 'alertmanager', label: 'Alertmanager', icon: FiAlertTriangle },
  { key: 'groq', label: 'Groq AI', icon: FiCpu },
];



export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [ghStatus, setGhStatus] = useState(null);
  const [serviceHealth, setServiceHealth] = useState({});
  const [healthScores, setHealthScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [now] = useState(new Date());

  const hour = now.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const username = user?.name || user?.username || 'User';

  const fetchAll = useCallback(async () => {
    try {
      const [
        pData, incData, gh, analysisData,
        ghHealth, dockerHealth, k8sHealth,
        promHealth, grafanaHealth, amHealth, diagResult, hsData,
      ] = await Promise.all([
        projectService.getProjects().catch(() => []),
        orchestrationService.getIncidents().catch(() => []),
        githubService.getGitHubDashboard().catch(() => null),
        orchestrationService.listDbAnalyses().catch(() => ({ analyses: [] })),
        githubService.getGitHubStatus().catch(() => null),
        dockerService.getDockerHealth().catch(() => null),
        kubernetesService.getKubernetesHealth().catch(() => null),
        prometheusService.getPrometheusHealth().catch(() => null),
        grafanaService.getGrafanaHealth().catch(() => null),
        alertmanagerService.getAlertmanagerHealth().catch(() => null),
        diagnosticsService.runDiagnostics().catch(() => null),
        listHealthScores().catch(() => ({ scores: [] })),
      ]);
      const aiResult = diagResult?.results?.find(r => r.key === 'ai');

      setProjects(Array.isArray(pData) ? pData : []);
      setIncidents(Array.isArray(incData) ? incData : []);
      setGhStatus(gh);
      setAnalyses(analysisData?.analyses || []);

      setHealthScores(Array.isArray(hsData?.scores) ? hsData.scores : []);

      setServiceHealth({
        github: ghHealth?.connected ? 'healthy' : 'not_configured',
        docker: dockerHealth?.status || 'not_configured',
        kubernetes: k8sHealth?.status || 'not_configured',
        prometheus: promHealth?.status || 'not_configured',
        grafana: grafanaHealth?.status || 'not_configured',
        alertmanager: amHealth?.status || 'not_configured',
        groq: aiResult?.status || 'not_configured',
      });

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

  const openIncidents = incidents.filter(i => i.status === 'open' || i.status === 'investigating').length;
  const connectedRepos = ghStatus?.connected_repos || projects.length;
  const aiFixes = analyses.length;

  const healthyCount = Object.values(serviceHealth).filter(s => ['healthy', 'connected', 'configured'].includes(s)).length;

  const recentIncidents = incidents.slice(0, 5);
  const recentAnalyses = analyses.slice(0, 3);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{greeting}, {username}</h1>
          <p className="page-subtitle">DevFlow Command Center · Platform Status Overview</p>
        </div>
      </div>

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
            <p>{healthyCount}/7</p>
            <div className="stat-trend up"><FiActivity size={12} /> Live health check</div>
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
        <div>
          <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
            <div className="card-header">
              <FiShield size={16} />
              <h3>System Health Matrix</h3>
            </div>
            <div className="health-matrix">
              {HEALTH_SERVICES.map(svc => (
                <HealthStatus key={svc.key} name={svc.label} icon={svc.icon} status={serviceHealth[svc.key] || 'not_configured'} />
              ))}
            </div>
          </div>

          {healthScores.length > 0 && (
            <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
              <div className="card-header">
                <FiShield size={16} />
                <h3>Repository Health Scores</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {healthScores.slice(0, 4).map(s => (
                  <div key={s.project_id} className="card-hover"
                    onClick={() => navigate(`/repositories/${s.project_id}`)}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
                    <HealthScore
                      score={s.score} trend={s.trend} color={s.color}
                      label={s.label} size="sm"
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="text-truncate" style={{ fontWeight: 600, fontSize: '0.85rem' }}>{s.project_name}</div>
                      <div className="text-truncate" style={{ color: 'var(--text-secondary)', fontSize: '0.72rem' }}>{s.full_name}</div>
                    </div>
                    <span className={`badge ${s.trend === 'improving' ? 'success' : s.trend === 'degrading' ? 'danger' : 'neutral'}`} style={{ fontSize: '0.6rem' }}>{s.trend}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/alerts')}>
            <div className="card-header" style={{ marginBottom: '0.75rem' }}>
              <FiAlertTriangle size={16} />
              <h3>Alert Summary</h3>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{incidents.length}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Incidents</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: openIncidents > 0 ? '#ef4444' : '#22c55e' }}>{openIncidents}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Active</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{connectedRepos}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Projects</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#a855f7' }}>{aiFixes}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>AI Fixes</div>
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel">
          <div className="card-header">
            <FiActivity size={16} />
            <h3>Recent Activity</h3>
          </div>
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

      {projects.length > 0 && (
        <div className="glass-panel">
          <div className="flex-between" style={{ marginBottom: '1rem' }}>
            <div className="card-header" style={{ margin: 0 }}>
              <FiBox size={16} />
              <h3>Connected Projects</h3>
            </div>
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
                  <div className="text-truncate" style={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.name}</div>
                  <div className="text-truncate" style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{p.full_name}</div>
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
        <div className="glass-panel" style={{ marginTop: '1.25rem', textAlign: 'center', padding: '2.5rem', border: '1px solid rgba(59, 130, 246, 0.15)' }}>
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
