import { useState, useCallback } from 'react';
import { FiActivity, FiCheckCircle, FiXCircle, FiRefreshCw, FiServer, FiDatabase, FiGitBranch, FiBox, FiLayers, FiBarChart2, FiPieChart, FiAlertTriangle, FiCpu } from 'react-icons/fi';
import * as diagnosticsService from '../../services/diagnosticsService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';

const ICON_MAP = {
  backend: FiServer,
  database: FiDatabase,
  github: FiGitBranch,
  docker: FiBox,
  kubernetes: FiLayers,
  prometheus: FiBarChart2,
  grafana: FiPieChart,
  alertmanager: FiAlertTriangle,
  ai: FiCpu,
};

export default function Diagnostics() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runChecks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await diagnosticsService.runDiagnostics();
      setResults(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">System Diagnostics</h1>
          <p className="page-subtitle">Automated health checks for all infrastructure services.</p>
        </div>
        <button className="btn btn-primary" onClick={runChecks} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiRefreshCw size={16} className={loading ? 'spin' : ''} />
          {loading ? 'Running...' : 'Run Diagnostics'}
        </button>
      </div>

      {loading && <LoadingSpinner text="Running diagnostics..." />}
      {error && <NetworkError error={error} onRetry={runChecks} />}

      {!results && !loading && !error && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem' }}>
          <FiActivity size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3>Ready to Diagnose</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Click "Run Diagnostics" to check the health of all services.</p>
        </div>
      )}

      {results && (
        <>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {results.summary.all_healthy
              ? 'All services are healthy.'
              : `${results.summary.unhealthy} of ${results.summary.total} service(s) have issues. See Dashboard > System Health Matrix for the overview.`}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {results.results.map((check, i) => {
              const Icon = ICON_MAP[check.key] || FiActivity;
              return (
                <div key={i} className="glass-panel" style={{
                  padding: '1rem', borderLeft: `3px solid ${check.status === 'healthy' ? 'var(--success-color)' : 'var(--danger-color)'}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: `${check.status === 'healthy' ? '#22c55e' : '#ef4444'}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {check.status === 'healthy' ? <FiCheckCircle size={18} style={{ color: '#22c55e' }} /> : <FiXCircle size={18} style={{ color: '#ef4444' }} />}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{check.name}</span>
                        <span className={`badge ${check.status === 'healthy' ? 'success' : 'danger'}`} style={{ fontSize: '0.7rem' }}>{check.status}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.25rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {check.version && check.version !== 'N/A' && <span>Version: {check.version}</span>}
                        <span>Latency: {check.latency_ms}ms</span>
                        <span>Last checked: {new Date(check.last_checked).toLocaleTimeString()}</span>
                      </div>
                      {check.error && (
                        <div style={{ fontSize: '0.8rem', color: '#ef4444', marginTop: '0.25rem' }}>{check.error}</div>
                      )}
                      {check.recommended_fix && check.status !== 'healthy' && (
                        <div style={{ fontSize: '0.8rem', color: '#f59e0b', marginTop: '0.25rem' }}>
                          Fix: {check.recommended_fix}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
