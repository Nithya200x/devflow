import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiGitBranch, FiStar, FiCode, FiExternalLink, FiCpu, FiServer,
  FiBox, FiActivity, FiAlertTriangle, FiCheckCircle, FiX, FiArrowUp,
  FiTerminal, FiBarChart2, FiClock, FiUser,
  FiRefreshCw, FiGithub, FiGlobe, FiPlus
} from 'react-icons/fi';
import * as projectService from '../../services/projectService';
import { getMetricsSummary } from '../../services/metricsService';
import { NetworkError } from '../../components/Common/NetworkError';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { Breadcrumbs } from '../../components/Repository/Breadcrumbs';

function ScoreRing({ value, label, sublabel, color = '#8b5cf6' }) {
  const r = 42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  return (
    <div className="score-ring" style={{ width: 140, height: 140 }}>
      <svg width="140" height="140" viewBox="0 0 100 100">
        <circle className="score-bg" cx="50" cy="50" r={r} />
        <circle className="score-fill" cx="50" cy="50" r={r}
          stroke={color}
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="score-label">
        <div className="score-value" style={{ color }}>{value}%</div>
        <div className="score-text">{sublabel || label}</div>
      </div>
    </div>
  );
}

function timeAgo(iso) {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

const STATUS_MAP = {
  connected: 'success',
  ready: 'active',
  not_configured: 'pending',
  unavailable: 'error',
};

function serviceData(o, key) {
  const d = o[key] || {};
  return {
    status: STATUS_MAP[d.service_status] || 'pending',
    configured: d.configured || false,
    lastChecked: d.last_checked || null,
    errorMessage: d.error_message || null,
    raw: d,
  };
}

function DevFlowTimeline({ overview }) {
  const services = [
    { key: 'github', icon: FiGithub, label: 'GitHub Connection' },
    { key: 'jenkins', icon: FiTerminal, label: 'Jenkins Pipeline' },
    { key: 'docker', icon: FiBox, label: 'Docker Container Scan' },
    { key: 'kubernetes', icon: FiServer, label: 'Kubernetes Analysis' },
    { key: 'prometheus', icon: FiBarChart2, label: 'Prometheus Metrics' },
    { key: 'grafana', icon: FiActivity, label: 'Grafana Dashboard' },
    { key: 'ai', icon: FiCpu, label: 'AI Root Cause Engine' },
  ];
  return (
    <div className="devflow-timeline">
      {services.map((svc) => {
        const Icon = svc.icon;
        const isAI = svc.key === 'ai';
        let status, configured, lastChecked, errorMessage;
        if (isAI) {
          const ai = overview.ai_analysis || {};
          status = ai.latest?.root_cause ? 'success' : 'active';
          configured = true;
          lastChecked = ai.latest?.analyzed_at || null;
          errorMessage = null;
        } else {
          const sd = serviceData(overview, svc.key);
          status = sd.status;
          configured = sd.configured;
          lastChecked = sd.lastChecked;
          errorMessage = sd.errorMessage;
        }

        const isNotConfigured = status === 'pending' && !configured;
        const isError = status === 'error';
        const isConnected = status === 'success';
        const isReady = status === 'active';

        let message;
        if (isAI) {
          message = errorMessage || (isConnected ? 'AI analysis complete' : 'Groq AI active');
        } else if (isNotConfigured) {
          message = 'Credentials not configured';
        } else if (isError) {
          message = errorMessage || 'Connection failed';
        } else if (isConnected) {
          if (svc.key === 'prometheus' && overview.prometheus?.has_kubernetes_metrics === false) {
            message = lastChecked ? `Connected - waiting for metrics (${timeAgo(lastChecked)})` : 'Connected - waiting for metrics';
          } else {
            message = lastChecked ? `Last checked: ${timeAgo(lastChecked)}` : 'Connected';
          }
        } else {
          message = 'Waiting...';
        }

        return (
          <div key={svc.key} className={`timeline-collector ${status}`}>
            <div className="collector-line">
              <div className={`collector-dot ${status}`}>
                <Icon size={14} />
              </div>
              <div className="collector-content">
                <div className="collector-header">
                  <span className="collector-status-icon">
                    {isConnected && <FiCheckCircle size={14} style={{ color: 'var(--success-color)' }} />}
                    {isError && <FiX size={14} style={{ color: 'var(--danger-color)' }} />}
                    {isReady && <FiActivity size={14} style={{ color: 'var(--accent-cyan)' }} />}
                    {isNotConfigured && <FiClock size={14} style={{ color: 'var(--text-muted)' }} />}
                  </span>
                  <span className="collector-label">{svc.label}</span>
                  <span className={`collector-badge ${status}`}>
                    {isConnected ? 'Connected' : isError ? 'Error' : isReady ? 'Ready' : 'Not Configured'}
                  </span>
                </div>
                <div className="collector-message">{message}</div>
                {isNotConfigured && (
                  <button className="btn btn-sm btn-ghost collector-connect-btn" style={{ marginTop: '0.35rem' }}>
                    <FiPlus size={12} style={{ marginRight: '0.25rem' }} /> Connect Service
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RepoStatCard({ icon: Icon, label, value, color = 'blue', trend }) {
  return (
    <div className="glass-panel card-hover stat-card" style={{ gap: '1rem' }}>
      <div className={`stat-icon-wrap ${color}`}><Icon size={22} /></div>
      <div className="stat-body">
        <h3>{label}</h3>
        <p>{value}</p>
        {trend !== undefined && (
          <div className={`stat-trend ${trend >= 0 ? 'up' : 'down'}`}>
            <FiArrowUp size={12} style={{ transform: trend >= 0 ? 'none' : 'rotate(180deg)' }} />
            {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  );
}

function OverviewTab({ overview }) {
  const p = overview.project || {};
  const gh = overview.github || {};
  return (
    <div className="page-enter">
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <RepoStatCard icon={FiStar} label="Stars" value={gh.stars || p.stars || 0} color="amber" />
        <RepoStatCard icon={FiGitBranch} label="Branches" value={gh.branch_count ?? 0} color="blue" />
        <RepoStatCard icon={FiCode} label="Language" value={p.language || gh.language || 'N/A'} color="cyan" />
        <RepoStatCard icon={FiAlertTriangle} label="Open PRs" value={gh.open_prs ?? 0} color="violet" />
      </div>

      {(gh.latest_commit || gh.latest_commit_date) && (
        <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', fontSize: '0.95rem' }}>
            <FiActivity /> Latest Activity
          </h3>
          <div className="activity-feed">
            <div className="activity-row">
              <div className="activity-dot green"><FiCheckCircle size={14} /></div>
              <div className="activity-desc">
                <div className="activity-text">{gh.latest_commit || 'Repository connected'}</div>
                <div className="activity-time">
                  {gh.latest_commit_author && <><FiUser size={11} /> {gh.latest_commit_author} · </>}
                  {gh.latest_commit_date && new Date(gh.latest_commit_date).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                  {gh.latest_commit_sha && <> · <code>{gh.latest_commit_sha}</code></>}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!gh.latest_commit && gh.connected && !gh.error && (
        <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
          <div className="empty-state" style={{ padding: '1rem' }}>
            <FiGithub size={24} />
            <h3>Repository connected</h3>
            <p>Fetching latest activity...</p>
          </div>
        </div>
      )}

      {gh.error && !gh.latest_commit && (
        <div className="glass-panel" style={{ marginBottom: '1.25rem', borderColor: 'rgba(239, 68, 68, 0.1)' }}>
          <div className="repo-meta-item" style={{ justifyContent: 'center', padding: '0.75rem' }}>
            <FiAlertTriangle size={14} style={{ color: 'var(--warning-color)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>GitHub sync pending — {gh.error}</span>
          </div>
        </div>
      )}

      <div className="grid-2-cols">
        <div className="glass-panel">
          <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiGlobe /> DevFlow Timeline
          </h3>
          <DevFlowTimeline overview={overview} />
        </div>

        <div className="glass-panel">
          <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiCpu /> Deployment Info
          </h3>
          {overview.jenkins?.job_name || overview.docker?.container_name || overview.kubernetes?.namespace ? (
            <div className="deploy-info-grid">
              <div className="deploy-info-item">
                <span className="deploy-info-label">Default Branch</span>
                <span className="deploy-info-value">{p.default_branch || 'N/A'}</span>
              </div>
              <div className="deploy-info-item">
                <span className="deploy-info-label">Visibility</span>
                <span className="deploy-info-value"><span className={`badge ${p.visibility === 'private' ? 'neutral' : 'success'}`}>{p.visibility || 'public'}</span></span>
              </div>
              {overview.jenkins?.job_name && (
                <div className="deploy-info-item">
                  <span className="deploy-info-label">Jenkins Job</span>
                  <span className="deploy-info-value">{overview.jenkins.job_name}</span>
                </div>
              )}
              {overview.docker?.container_name && (
                <div className="deploy-info-item">
                  <span className="deploy-info-label">Docker Container</span>
                  <span className="deploy-info-value">{overview.docker.container_name}</span>
                </div>
              )}
              {overview.kubernetes?.namespace && (
                <div className="deploy-info-item">
                  <span className="deploy-info-label">K8s Namespace</span>
                  <span className="deploy-info-value">{overview.kubernetes.namespace}</span>
                </div>
              )}
              {overview.kubernetes?.deployment && (
                <div className="deploy-info-item">
                  <span className="deploy-info-label">K8s Deployment</span>
                  <span className="deploy-info-value">{overview.kubernetes.deployment}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '1rem' }}>
              <FiCpu size={24} />
              <h3>No deployment detected yet</h3>
              <p>Connect CI/CD and infrastructure services to view deployment info</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PipelineTab({ overview }) {
  const builds = overview.jenkins?.build_history || [];
  const github = overview.github || {};
  return (
    <div className="page-enter">
      <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
        <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiGitBranch /> GitHub
        </h3>
        {github.connected && !github.error ? (
          <>
            <div className="repo-meta-item" style={{ marginBottom: '0.5rem' }}>
              <FiCheckCircle size={14} style={{ color: 'var(--success-color)' }} />
              <span>Repository connected · {github.latest_commit ? 'Latest commit synced' : 'Awaiting data'}</span>
            </div>
            {github.latest_commit && (
              <div className="repo-meta-item">
                <FiActivity size={14} style={{ color: 'var(--accent-cyan)' }} />
                <span>{github.latest_commit}</span>
              </div>
            )}
          </>
        ) : github.error ? (
          <div className="repo-meta-item">
            <FiAlertTriangle size={14} style={{ color: 'var(--warning-color)' }} />
            <span>GitHub sync: {github.error}</span>
          </div>
        ) : (
          <div className="repo-meta-item">
            <FiClock size={14} style={{ color: 'var(--text-muted)' }} />
            <span>GitHub connection pending</span>
          </div>
        )}
      </div>

      <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
        <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiTerminal /> Jenkins Pipeline
        </h3>
        {!overview.jenkins?.connected ? (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiTerminal size={24} />
            <h3>No Jenkins pipeline detected</h3>
            <p>Waiting for pipeline configuration</p>
          </div>
        ) : builds.length === 0 ? (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiTerminal size={24} />
            <h3>Pipeline configured</h3>
            <p>No builds yet — awaiting first deployment</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr><th>Build</th><th>Status</th><th>Duration</th><th>Timestamp</th></tr>
              </thead>
              <tbody>
                {builds.slice(0, 10).map((b, i) => (
                  <tr key={b.number || i}>
                    <td style={{ fontWeight: 600 }}>#{b.number}</td>
                    <td>
                      <span className={`badge ${b.result === 'SUCCESS' ? 'success' : b.result === 'FAILURE' ? 'danger' : 'warning'}`}>
                        {b.result || 'PENDING'}
                      </span>
                    </td>
                    <td>{b.duration ? `${(b.duration / 1000).toFixed(1)}s` : '-'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      <FiClock size={12} style={{ marginRight: '0.3rem', display: 'inline' }} />
                      {b.timestamp ? new Date(b.timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="glass-panel">
        <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiBox /> Docker
        </h3>
        {!overview.docker?.connected ? (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiBox size={24} />
            <h3>No Docker containers found</h3>
            <p>Waiting for container configuration</p>
          </div>
        ) : overview.docker?.container_name ? (
          <div className="repo-meta-item">
            <FiCheckCircle size={14} style={{ color: 'var(--success-color)' }} />
            <span>Container <strong>{overview.docker.container_name}</strong> {overview.docker.running ? 'running' : 'stopped'}</span>
            {overview.docker.image && <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>({overview.docker.image})</span>}
          </div>
        ) : (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiBox size={24} />
            <h3>No container configured</h3>
            <p>Connect Docker to enable container monitoring</p>
          </div>
        )}
      </div>
    </div>
  );
}

function InfrastructureTab({ overview }) {
  const k8s = overview.kubernetes || {};
  const pods = k8s.pods || [];
  return (
    <div className="page-enter">
      <div className="glass-panel">
        <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiServer /> Kubernetes
        </h3>
        {!overview.kubernetes?.connected || !overview.kubernetes?.deployment ? (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiServer size={24} />
            <h3>No Kubernetes deployment linked</h3>
            <p>Waiting for deployment configuration</p>
          </div>
        ) : k8s.namespace ? (
          <>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              <div><span className="deploy-info-label">Namespace</span><div className="deploy-info-value">{k8s.namespace}</div></div>
              <div><span className="deploy-info-label">Deployment</span><div className="deploy-info-value">{k8s.deployment || 'N/A'}</div></div>
              <div><span className="deploy-info-label">Pods</span><div className="deploy-info-value">{pods.length}</div></div>
            </div>
            {pods.length > 0 && (
              <div className="table-container">
                <table>
                  <thead><tr><th>Pod</th><th>Status</th><th>IP</th><th>Node</th></tr></thead>
                  <tbody>
                    {pods.slice(0, 10).map((pod, i) => (
                      <tr key={pod.name || i}>
                        <td style={{ fontWeight: 600, fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{pod.name}</td>
                        <td>
                          <span className={`badge ${pod.status === 'Running' ? 'success' : 'danger'}`}>
                            {pod.status}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--mono-font)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{pod.ip || '-'}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{pod.node || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {pods.length === 0 && (
              <div className="repo-meta-item" style={{ justifyContent: 'center', padding: '0.5rem' }}>
                <FiClock size={14} style={{ color: 'var(--text-muted)' }} />
                <span style={{ color: 'var(--text-secondary)' }}>Deployment configured, awaiting pods</span>
              </div>
            )}
          </>
        ) : (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiServer size={24} />
            <h3>Kubernetes not configured</h3>
            <p>Connect Kubernetes to enable infrastructure monitoring</p>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricsTab({ overview }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getMetricsSummary();
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSummary(); }, [fetchSummary]);

  const prom = overview.prometheus || {};
  const isConfigured = prom.configured;

  if (!isConfigured) {
    return (
      <div className="glass-panel">
        <div className="empty-state" style={{ padding: '1.5rem' }}>
          <FiBarChart2 size={24} />
          <h3>No metrics available</h3>
          <p>Prometheus not configured</p>
        </div>
      </div>
    );
  }

  if (loading) return <LoadingSpinner text="Loading metrics..." />;
  if (error) return <NetworkError error={error} onRetry={fetchSummary} />;

  const s = data || {};
  const status = s.status || 'no_data';
  const requests = s.requests || 0;
  const errors = s.errors || 0;
  const errorRate = s.errorRate || 0;
  const avgLatency = s.avgLatency || 0;
  const activeRequests = s.activeRequests || 0;

  const latencyMs = avgLatency > 0 ? (avgLatency * 1000).toFixed(1) : null;
  const displayLatency = latencyMs ? `${latencyMs}ms` : '—';

  let statusLabel, statusClass;
  if (status === 'healthy') {
    statusLabel = 'Active';
    statusClass = 'success';
  } else if (status === 'connected') {
    statusLabel = 'No Data';
    statusClass = 'warning';
  } else if (status === 'not_configured') {
    statusLabel = 'Not Configured';
    statusClass = 'neutral';
  } else {
    statusLabel = 'Disconnected';
    statusClass = 'danger';
  }

  return (
    <div className="page-enter">
      <div className="glass-panel" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 style={{ fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiBarChart2 /> Application Metrics
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className={`badge ${statusClass}`}>{statusLabel}</span>
            <button className="btn btn-ghost btn-sm" onClick={fetchSummary} title="Refresh">
              <FiRefreshCw size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <RepoStatCard icon={FiActivity} label="Total Requests" value={requests.toLocaleString()} color="blue" />
        <RepoStatCard icon={FiAlertTriangle} label="Error Rate" value={`${errorRate}%`} color={errorRate > 5 ? 'red' : 'green'} />
        <RepoStatCard icon={FiClock} label="Avg Latency" value={displayLatency} color="violet" />
        <RepoStatCard icon={FiCpu} label="Active Requests" value={activeRequests} color="cyan" />
      </div>

      {status === 'healthy' && (
        <div className="repo-meta-item" style={{ marginTop: '0.75rem' }}>
          <FiCheckCircle size={14} style={{ color: 'var(--success-color)' }} />
          <span>Alloy scraping active · metrics flowing</span>
        </div>
      )}
    </div>
  );
}

function IncidentsTab({ overview }) {
  const incidentData = overview.incidents || {};
  const incidents = incidentData.items || [];
  return (
    <div className="page-enter">
      <div className="glass-panel">
        <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiAlertTriangle /> Repository Incidents
        </h3>
        {incidents.length === 0 ? (
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiCheckCircle size={24} style={{ color: 'var(--success-color)' }} />
            <h3>No incidents detected</h3>
            <p>Monitoring active · All services operating normally</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead><tr><th>ID</th><th>Severity</th><th>Summary</th><th>Status</th><th>Root Cause</th></tr></thead>
              <tbody>
                {incidents.slice(0, 20).map((inc, i) => (
                  <tr key={inc.incident_id || i}>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{inc.incident_id}</td>
                    <td><span className={`badge ${inc.severity === 'critical' || inc.severity === 'high' ? 'danger' : inc.severity === 'medium' ? 'warning' : 'success'}`}>{inc.severity}</span></td>
                    <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inc.summary}</td>
                    <td><span className={`badge ${inc.status === 'open' ? 'warning' : 'success'}`}>{inc.status}</span></td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{inc.root_cause || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function AiRcaTab({ overview }) {
  const meta = overview.ai_analysis?.latest || {};

  if (!meta?.root_cause) {
    return (
      <div className="page-enter">
        <div className="glass-panel">
          <div className="empty-state" style={{ padding: '1.5rem' }}>
            <FiCpu size={24} />
            <h3>AI Analysis Ready</h3>
            <p>Groq AI engine active · Incidents will be analyzed automatically</p>
          </div>
        </div>
      </div>
    );
  }

  const confidence = meta.confidence_score || meta.confidence || 0;
  const pct = Math.round(confidence * 100);

  return (
    <div className="page-enter">
      <div className="glass-panel" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <ScoreRing value={pct} label="Confidence" sublabel="Confidence" color={pct > 70 ? '#10b981' : pct > 40 ? '#f59e0b' : '#ef4444'} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.25rem' }}>{meta.root_cause}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              {meta.summary || ''}
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <span className="badge connected">Provider: {meta.provider || 'Groq'}</span>
              <span className="badge success">Model: {meta.model || 'llama-3.3-70b-versatile'}</span>
              {meta.severity && <span className={`badge ${meta.severity === 'critical' || meta.severity === 'high' ? 'danger' : meta.severity === 'medium' ? 'warning' : 'success'}`}>{meta.severity}</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {meta.affected_components?.length > 0 && (
          <div className="glass-panel">
            <h3 style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>Affected Components</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {meta.affected_components.map((c, i) => (
                <span key={i} className="badge neutral">{c}</span>
              ))}
            </div>
          </div>
        )}
        {meta.suggested_fixes?.length > 0 && (
          <div className="glass-panel">
            <h3 style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>Suggested Fixes</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {meta.suggested_fixes.map((f, i) => (
                <li key={i} style={{ padding: '0.3rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
        {meta.preventive_actions?.length > 0 && (
          <div className="glass-panel">
            <h3 style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>Preventive Actions</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {meta.preventive_actions.map((a, i) => (
                <li key={i} style={{ padding: '0.3rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
        {meta.risk_assessment && (
          <div className="glass-panel">
            <h3 style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>Risk Assessment</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{meta.risk_assessment}</p>
          </div>
        )}
      </div>

      {meta.estimated_resolution_time && (
        <div className="glass-panel" style={{ marginTop: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FiClock size={20} style={{ color: 'var(--warning-color)' }} />
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Estimated Resolution Time</div>
              <div style={{ fontSize: '1rem', fontWeight: 700 }}>{meta.estimated_resolution_time}</div>
            </div>
          </div>
        </div>
      )}

      {meta.requires_human && (
        <div className="glass-panel" style={{ marginTop: '1rem', borderColor: 'rgba(245, 158, 11, 0.15)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FiAlertTriangle size={20} style={{ color: 'var(--warning-color)' }} />
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>This incident requires human review</span>
          </div>
        </div>
      )}
    </div>
  );
}

function calcHealthScore(overview) {
  let score = 0;
  const gh = overview.github || {};
  if (gh.connected && !gh.error) score += 40;
  const jenkins = overview.jenkins || {};
  if (jenkins.connected && jenkins.healthy) score += 15;
  const docker = overview.docker || {};
  if (docker.connected && docker.running) score += 15;
  const k8s = overview.kubernetes || {};
  if (k8s.connected && k8s.deployment) score += 15;
  if (k8s.total_pods > 0 && k8s.ready_pods === k8s.total_pods) score += 5;
  const prom = overview.prometheus || {};
  if (prom.healthy) score += 5;
  const graf = overview.grafana || {};
  if (graf.dashboard_uid) score += 5;
  const health = overview.health || {};
  if (health.status !== 'critical') score += 0;
  if (health.status === 'warning') score -= 10;
  return Math.min(100, score);
}

function calcHealthColor(score) {
  if (score >= 60) return '#10b981';
  if (score >= 30) return '#f59e0b';
  return '#ef4444';
}

const TABS = [
  { key: 'overview', label: 'Overview', icon: FiActivity },
  { key: 'pipeline', label: 'Pipeline', icon: FiTerminal },
  { key: 'infrastructure', label: 'Infrastructure', icon: FiServer },
  { key: 'metrics', label: 'Metrics', icon: FiBarChart2 },
  { key: 'incidents', label: 'Incidents', icon: FiAlertTriangle },
  { key: 'ai-rca', label: 'AI Root Cause', icon: FiCpu },
];

const LOADING_MESSAGES = [
  'Connecting repository...',
  'Initializing DevFlow collectors...',
  'Fetching repository intelligence...',
  'Preparing dashboard...',
];

function LoadingState({ phase }) {
  const activeIdx = Math.min(phase || 0, LOADING_MESSAGES.length - 1);
  return (
    <div className="page-enter">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '2rem', marginBottom: '1.5rem' }}>
        {[0,1,2,3].map(i => (
          <div key={i} className="skeleton skeleton-text" style={{ width: 80 + i * 20 }} />
        ))}
      </div>
      <div className="skeleton skeleton-card" style={{ height: 180, marginBottom: '1.25rem' }} />
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1.5rem' }}>
        {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ width: 100, height: 36, borderRadius: 'var(--radius-sm)' }} />)}
      </div>
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {[1,2,3,4].map(i => <div key={i} className="skeleton skeleton-card" style={{ height: 100 }} />)}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginTop: '2rem', padding: '1rem' }}>
        <div className="animate-spin" style={{ width: 18, height: 18, border: '2px solid rgba(139,92,246,0.2)', borderTopColor: 'var(--accent-violet)', borderRadius: '50%' }} />
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{LOADING_MESSAGES[activeIdx]}</span>
      </div>
    </div>
  );
}

export default function RepositoryCommandCenter() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [lastRefresh, setLastRefresh] = useState(null);
  const pollingRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const data = await projectService.getProjectOverview(id);
      setOverview(data);
      setError(null);
      setLastRefresh(new Date());
    } catch (err) {
      if (!overview) setError(err);
    }
  }, [id]);

  const fetchWithLoading = useCallback(async () => {
    try {
      setLoading(true);
      await fetchData();
    } finally {
      setLoading(false);
    }
  }, [fetchData]);

  useEffect(() => { fetchWithLoading(); }, [fetchWithLoading]);

  useEffect(() => {
    pollingRef.current = setInterval(() => {
      fetchData();
    }, 30000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [fetchData]);

  if (loading) return <LoadingState phase={0} />;
  if (error) return <NetworkError error={error} onRetry={fetchWithLoading} />;
  if (!overview || !overview.project) {
    return (
      <div className="page-enter">
        <Breadcrumbs items={[
          { label: 'Dashboard', path: '/' },
          { label: 'Repositories', path: '/github/repos' },
          { label: 'Project' },
        ]} />
        <div className="empty-state" style={{ padding: '3rem' }}>
          <FiServer size={40} />
          <h3>Project not found</h3>
          <p style={{ marginTop: '0.5rem' }}>This project may have been disconnected or does not exist.</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/github/repos')}>
            Back to Repositories
          </button>
        </div>
      </div>
    );
  }

  const p = overview.project;
  const gh = overview.github || {};
  const healthScore = calcHealthScore(overview);
  const healthColor = calcHealthColor(healthScore);

  return (
    <div className="page-enter">
      <Breadcrumbs items={[
        { label: 'Dashboard', path: '/' },
        { label: 'Repositories', path: '/github/repos' },
        { label: p.name },
      ]} />

      <div className="glass-panel repo-header-panel" style={{ marginTop: '0.75rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="repo-header-title-row">
              <h1 className="repo-name">{p.name}</h1>
              <span className={`badge ${p.visibility === 'private' ? 'neutral' : 'success'}`}>{p.visibility || 'public'}</span>
              <span className={`badge ${gh.connected && !gh.error ? 'connected' : 'neutral'}`}>
                {gh.connected && !gh.error ? 'Managed' : 'Disconnected'}
              </span>
            </div>
            <div className="repo-owner">{p.full_name || `${p.owner || '?'}/${p.name}`}</div>
            <div className="repo-header-meta" style={{ marginTop: '0.75rem' }}>
              {p.default_branch && (
                <div className="repo-meta-item"><FiGitBranch size={14} /> {p.default_branch}</div>
              )}
              {p.language && (
                <div className="repo-meta-item"><FiCode size={14} /> {p.language}</div>
              )}
              {gh.stars !== undefined && (
                <div className="repo-meta-item"><FiStar size={14} /> {gh.stars}</div>
              )}
              {p.html_url && (
                <a href={p.html_url} target="_blank" rel="noopener noreferrer" className="repo-meta-item" style={{ color: 'var(--accent-cyan)', textDecoration: 'none' }}>
                  <FiExternalLink size={14} /> GitHub
                </a>
              )}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <ScoreRing value={healthScore} label="DevFlow Score" sublabel="Operational" color={healthColor} />
          </div>
        </div>

        {p.description && (
          <p className="repo-description" style={{ marginTop: '1rem' }}>{p.description}</p>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem' }}>
          <div className="repo-dates">
            {gh.latest_commit_date && <span><FiClock size={12} style={{ marginRight: '0.3rem', display: 'inline' }} /> Latest commit: {new Date(gh.latest_commit_date).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</span>}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {lastRefresh && <span><FiRefreshCw size={11} style={{ marginRight: '0.2rem', display: 'inline' }} /> Updated {new Date(lastRefresh).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })}</span>}
            <button className="btn btn-ghost btn-sm" onClick={fetchData} title="Refresh now" style={{ padding: '0.25rem' }}>
              <FiRefreshCw size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <tab.icon />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {activeTab === 'overview' && <OverviewTab overview={overview} />}
      {activeTab === 'pipeline' && <PipelineTab overview={overview} />}
      {activeTab === 'infrastructure' && <InfrastructureTab overview={overview} />}
      {activeTab === 'metrics' && <MetricsTab overview={overview} />}
      {activeTab === 'incidents' && <IncidentsTab overview={overview} />}
      {activeTab === 'ai-rca' && <AiRcaTab overview={overview} />}
    </div>
  );
}