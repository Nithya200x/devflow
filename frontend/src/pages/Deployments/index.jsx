import { useState, useCallback, useRef } from 'react';
import {
  FiPlay, FiCheckCircle, FiXCircle, FiActivity, FiRotateCcw,
  FiClock, FiGitCommit, FiBox, FiServer, FiRefreshCw,
  FiTerminal, FiArrowUp, FiLoader, FiFileText, FiSearch, FiDownload,
} from 'react-icons/fi';
import * as deploymentService from '../../services/deploymentService';
import * as kubernetesService from '../../services/kubernetesService';
import * as projectService from '../../services/projectService';
import { DataTable } from '../../components/Tables/DataTable';
import { StatCard } from '../../components/Cards/StatCard';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';
import { usePolling } from '../../hooks/usePolling';

export default function DeploymentCenter() {
  const [deployments, setDeployments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [clusterDeployments, setClusterDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [showDeployForm, setShowDeployForm] = useState(false);

  const [selectedProject, setSelectedProject] = useState('');
  const [deployBranch, setDeployBranch] = useState('main');
  const [deployCommit, setDeployCommit] = useState('');
  const [deployEnv, setDeployEnv] = useState('dev');
  const [logViewDeployment, setLogViewDeployment] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logLoading, setLogLoading] = useState(false);
  const [logSearch, setLogSearch] = useState('');
  const logRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [deps, projs, k8sDeps] = await Promise.all([
        deploymentService.getDeployments(),
        projectService.getProjects().catch(() => []),
        kubernetesService.listDeployments({ namespace: 'devflow' }).catch(() => []),
      ]);
      setDeployments(deps);
      setProjects(projs);
      setClusterDeployments(k8sDeps.deployments || k8sDeps || []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetchAll, 15000);

  const runningDeploy = deployments.find(d =>
    ['queued', 'building', 'deploying'].includes(d.status)
  );

  const handleDeploy = async () => {
    if (!selectedProject) return;
    setActionLoading(true);
    try {
      await deploymentService.createDeployment({
        project_id: parseInt(selectedProject, 10),
        branch: deployBranch,
        commit_sha: deployCommit,
        environment: deployEnv,
      });
      setShowDeployForm(false);
      setDeployCommit('');
      await fetchAll();
    } catch (err) {
      setError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRollback = async (deployId) => {
    setActionLoading(true);
    try {
      await deploymentService.rollbackDeployment(deployId);
      await fetchAll();
    } catch (err) {
      setError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const fetchLogs = async (deploymentId) => {
    setLogLoading(true);
    setLogViewDeployment(deploymentId);
    setLogSearch('');
    try {
      const data = await deploymentService.getDeploymentLogs(deploymentId);
      setLogs(data.logs || []);
    } catch (err) {
      setLogs([]);
    } finally {
      setLogLoading(false);
    }
    setTimeout(() => logRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  const closeLogs = () => {
    setLogViewDeployment(null);
    setLogs([]);
    setLogSearch('');
  };

  const downloadLogs = () => {
    const text = logs.map(l => `[${l.stage}] ${l.message}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `deployment-${logViewDeployment}-logs.txt`;
    a.click(); URL.revokeObjectURL(url);
  };

  const statusIcon = (status) => {
    switch (status) {
      case 'success': return <FiCheckCircle size={14} />;
      case 'failed': return <FiXCircle size={14} />;
      case 'rolled_back': return <FiArrowUp size={14} />;
      case 'queued':
      case 'building':
      case 'deploying': return <FiLoader size={14} className="spin" />;
      default: return <FiClock size={14} />;
    }
  };

  const statusBadge = (status) => {
    const map = {
      'success': 'success',
      'failed': 'danger',
      'rolled_back': 'warning',
      'queued': 'neutral',
      'building': 'warning',
      'deploying': 'warning',
    };
    return (
      <span className={`badge ${map[status] || 'neutral'}`}>
        {statusIcon(status)}
        {status.replace('_', ' ')}
      </span>
    );
  };

  const formatTime = (ts) => {
    if (!ts) return '—';
    const d = new Date(ts);
    return d.toLocaleString();
  };

  const columns = [
    {
      key: 'deployment_id', label: 'ID',
      style: { color: 'var(--text-secondary)', fontFamily: 'var(--mono-font)', fontSize: '0.8rem' },
      render: (row) => `#${row.deployment_id}`,
    },
    {
      key: 'commit_sha', label: 'Commit',
      style: { fontFamily: 'var(--mono-font)', fontSize: '0.8rem' },
      render: (row) => row.commit_sha ? (
        <span title={row.commit_sha}>{row.commit_sha.substring(0, 7)}</span>
      ) : '—',
    },
    { key: 'branch', label: 'Branch', render: (row) => (
      <span className="badge neutral">{row.branch || '—'}</span>
    )},
    { key: 'environment', label: 'Env', render: (row) => (
      <span className="badge neutral">{row.environment}</span>
    )},
    { key: 'status', label: 'Status', render: (row) => statusBadge(row.status) },
    {
      key: 'started_at', label: 'Started',
      style: { color: 'var(--text-secondary)', fontSize: '0.8rem' },
      render: (row) => formatTime(row.started_at || row.created_at),
    },
    { key: 'triggered_by', label: 'Triggered By', style: { color: 'var(--text-secondary)' } },
    {
      key: 'actions', label: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => fetchLogs(row.id)}
          >
            <FiFileText size={14} /> Logs
          </button>
          {row.status === 'failed' && (
            <button
              className="btn btn-danger btn-sm"
              onClick={() => handleRollback(row.id)}
              disabled={actionLoading}
            >
              <FiRotateCcw size={14} /> Rollback
            </button>
          )}
          {row.status === 'success' && row.rollback_available && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => handleRollback(row.id)}
              disabled={actionLoading}
            >
              <FiRotateCcw size={14} /> Rollback
            </button>
          )}
        </div>
      ),
    },
  ];

  if (loading) return <LoadingSpinner text="Loading deployment center..." />;
  if (error && !deployments.length) return <NetworkError error={error} onRetry={fetchAll} />;

  const latestDeployment = deployments[0];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Deployment Center</h1>
          <p className="page-subtitle">
            Orchestrate CI/CD pipelines and manage application rollouts.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {runningDeploy && (
            <span style={{ color: 'var(--accent-cyan)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <FiLoader className="spin" size={14} />
              Deployment in progress...
            </span>
          )}
          <button className="btn btn-primary" onClick={() => setShowDeployForm(!showDeployForm)} disabled={actionLoading}>
            <FiPlay size={18} /> New Deployment
          </button>
          <button className="btn btn-ghost" onClick={fetchAll} disabled={loading}>
            <FiRefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {error && <NetworkError error={error} onRetry={fetchAll} />}

      {showDeployForm && (
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiTerminal size={18} /> New Deployment
          </h3>
          <div className="grid-2-cols" style={{ gap: '1rem', marginBottom: '1rem' }}>
            <div className="input-group">
              <label>Project</label>
              <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
                <option value="">Select project...</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.full_name}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label>Environment</label>
              <select value={deployEnv} onChange={e => setDeployEnv(e.target.value)}>
                <option value="dev">Development</option>
                <option value="staging">Staging</option>
                <option value="prod">Production</option>
              </select>
            </div>
            <div className="input-group">
              <label>Branch</label>
              <input type="text" value={deployBranch} onChange={e => setDeployBranch(e.target.value)} placeholder="main" />
            </div>
            <div className="input-group">
              <label>Commit SHA</label>
              <input type="text" value={deployCommit} onChange={e => setDeployCommit(e.target.value)} placeholder="Latest commit (leave empty for latest)" />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button className="btn btn-primary" onClick={handleDeploy} disabled={actionLoading || !selectedProject}>
              {actionLoading ? <><FiLoader className="spin" size={16} /> Deploying...</> : <><FiPlay size={16} /> Deploy</>}
            </button>
            <button className="btn btn-ghost" onClick={() => setShowDeployForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      {deployments.length > 0 && (
        <>
          <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
            <StatCard
              icon={FiGitCommit}
              label="Latest Commit"
              value={latestDeployment?.commit_sha ? latestDeployment.commit_sha.substring(0, 7) : '—'}
              color="blue"
            />
            <StatCard
              icon={FiBox}
              label="Environment"
              value={latestDeployment?.environment || '—'}
              color="violet"
            />
            <StatCard
              icon={FiActivity}
              label="Status"
              value={latestDeployment?.status || '—'}
              color={latestDeployment?.status === 'success' ? 'green' : latestDeployment?.status === 'failed' ? 'red' : 'blue'}
            />
            <StatCard
              icon={FiServer}
              label="K8s Deployments"
              value={Array.isArray(clusterDeployments) ? clusterDeployments.length : 0}
              color="cyan"
            />
          </div>

          {clusterDeployments.length > 0 && (
            <div className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem' }}>
              <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <FiServer size={14} style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} />
                Kubernetes Deployments
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                {(Array.isArray(clusterDeployments) ? clusterDeployments : []).map(dep => (
                  <div key={`${dep.namespace}-${dep.name}`} style={{
                    background: 'var(--bg-deep)', borderRadius: 'var(--radius-sm)',
                    padding: '0.75rem 1rem', minWidth: '200px', flex: '1 1 auto',
                  }}>
                    <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.9rem' }}>
                      {dep.name}
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {dep.namespace}
                    </div>
                    <div style={{ marginTop: '0.4rem', display: 'flex', gap: '0.75rem', fontSize: '0.8rem' }}>
                      <span style={{ color: 'var(--success-color)' }}>
                        {dep.ready_replicas}/{dep.replicas} ready
                      </span>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {dep.available_replicas || 0} available
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <div className="page-header" style={{ marginTop: '1rem' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Deployment History</h2>
      </div>

      {!deployments.length ? (
        <EmptyState
          message="No deployments found"
          description="Trigger your first deployment to see history here."
          action={{ label: 'New Deployment', onClick: () => setShowDeployForm(true) }}
        />
      ) : (
        <DataTable columns={columns} data={deployments} />
      )}

      {logViewDeployment && (
        <div ref={logRef} className="glass-panel" style={{ marginTop: '1rem', padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FiTerminal size={16} />
            <span style={{ fontWeight: 600, fontSize: '0.9rem', flex: 1 }}>
              Deployment Logs #{logViewDeployment}
            </span>
            <div style={{ position: 'relative' }}>
              <FiSearch size={14} style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
              <input
                type="text"
                value={logSearch}
                onChange={e => setLogSearch(e.target.value)}
                placeholder="Search logs..."
                style={{ paddingLeft: '1.75rem', height: 30, fontSize: '0.8rem', width: 200 }}
              />
            </div>
            <button className="btn btn-ghost btn-sm" onClick={downloadLogs} title="Download logs">
              <FiDownload size={14} />
            </button>
            <button className="btn btn-ghost btn-sm" onClick={closeLogs} title="Close">
              <FiXCircle size={14} />
            </button>
          </div>
          <div className="terminal-window" style={{ border: 'none', borderRadius: 0, boxShadow: 'none', maxHeight: '400px', overflow: 'auto' }}>
            {logLoading ? (
              <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Loading logs...</div>
            ) : logs.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No logs available for this deployment.</div>
            ) : (
              logs.filter(l => !logSearch || l.message.toLowerCase().includes(logSearch.toLowerCase()) || l.stage.toLowerCase().includes(logSearch.toLowerCase()))
                .map((log, i) => (
                  <div key={i} className={`terminal-line ${log.message.includes('error') || log.message.includes('failed') ? 'terminal-error' : log.message.includes('warn') ? 'terminal-warn' : 'terminal-info'}`}>
                    <span style={{ color: '#64748b', marginRight: '0.5rem' }}>[{log.stage}]</span>
                    {log.message}
                  </div>
                ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
