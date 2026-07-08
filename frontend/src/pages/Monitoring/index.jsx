import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiActivity, FiBarChart2, FiPieChart, FiAlertTriangle, FiLayers, FiCpu, FiHardDrive, FiChevronRight } from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { StatusBadge, getStatusColor } from '../../components/Common/StatusBadge';
import * as prometheusService from '../../services/prometheusService';
import * as grafanaService from '../../services/grafanaService';
import * as alertmanagerService from '../../services/alertmanagerService';
import * as orchestrationService from '../../services/orchestrationService';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
};

export default function MonitoringDashboard() {
  const navigate = useNavigate();
  const [promHealth, setPromHealth] = useState(null);
  const [grafanaHealth, setGrafanaHealth] = useState(null);
  const [amHealth, setAmHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [ph, gh, ah, alertsData, statsData, incData] = await Promise.allSettled([
        prometheusService.getPrometheusHealth(),
        grafanaService.getGrafanaHealth(),
        alertmanagerService.getAlertmanagerHealth(),
        alertmanagerService.getAlerts(),
        alertmanagerService.getAlertStats(),
        orchestrationService.getIncidents().catch(() => []),
      ]);
      setPromHealth(ph.status === 'fulfilled' ? ph.value : { status: 'connection_failed', connected: false, error: 'Failed to connect' });
      setGrafanaHealth(gh.status === 'fulfilled' ? gh.value : { status: 'connection_failed', connected: false, error: 'Failed to connect' });
      setAmHealth(ah.status === 'fulfilled' ? ah.value : { status: 'connection_failed', connected: false, error: 'Failed to connect' });
      setAlerts(alertsData.status === 'fulfilled' ? (alertsData.value.alerts || []) : []);
      setStats(statsData.status === 'fulfilled' ? statsData.value : null);
      setIncidents(Array.isArray(incData.value) ? incData.value : []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;

  const firingAlerts = alerts.filter(a => a.alertstate === 'firing' || a.status === 'firing');

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Observability</h1>
          <p className="page-subtitle">Prometheus metrics, Grafana dashboards, and Alertmanager alerts.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/metrics')}>
          <div className="card-header">
            <FiBarChart2 size={20} style={{ color: getStatusColor(promHealth?.status) }} />
            <h3>Prometheus</h3>
            <StatusBadge status={promHealth?.status || 'not_configured'} className="card-badge" />
          </div>
          {['healthy', 'connected', 'configured'].includes(promHealth?.status) ? (
            <div className="grid-2-cols" style={{ gap: '0.75rem' }}>
              <div><span className="deploy-info-label">Version</span><span className="deploy-info-value text-truncate">{promHealth.version || 'N/A'}</span></div>
              <div><span className="deploy-info-label">Latency</span><span className="deploy-info-value">{promHealth.latency_ms ? `${promHealth.latency_ms}ms` : 'N/A'}</span></div>
            </div>
          ) : (
            <p className="text-secondary" style={{ fontSize: '0.85rem' }}>{promHealth?.error || 'Set PROMETHEUS_URL to connect'}</p>
          )}
        </div>

        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/dashboards')}>
          <div className="card-header">
            <FiPieChart size={20} style={{ color: getStatusColor(grafanaHealth?.status) }} />
            <h3>Grafana</h3>
            <StatusBadge status={grafanaHealth?.status || 'not_configured'} className="card-badge" />
          </div>
          {['healthy', 'connected', 'configured'].includes(grafanaHealth?.status) ? (
            <div className="grid-2-cols" style={{ gap: '0.75rem' }}>
              <div><span className="deploy-info-label">Version</span><span className="deploy-info-value text-truncate">{grafanaHealth.version || 'N/A'}</span></div>
              <div><span className="deploy-info-label">Latency</span><span className="deploy-info-value">{grafanaHealth.latency_ms ? `${grafanaHealth.latency_ms}ms` : 'N/A'}</span></div>
            </div>
          ) : (
            <p className="text-secondary" style={{ fontSize: '0.85rem' }}>{grafanaHealth?.error || 'Set GRAFANA_URL to connect'}</p>
          )}
        </div>

        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/alerts')}>
          <div className="card-header">
            <FiAlertTriangle size={20} style={{ color: firingAlerts.length > 0 ? '#ef4444' : getStatusColor(amHealth?.status) }} />
            <h3>Alertmanager</h3>
            <StatusBadge status={amHealth?.status || 'not_configured'} className="card-badge" />
          </div>
          {['healthy', 'connected', 'configured'].includes(amHealth?.status) ? (
            <div>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
                <span style={{ color: '#ef4444', fontWeight: 600 }}>{firingAlerts.length} firing</span>
                <span style={{ color: 'var(--text-secondary)' }}>{stats?.total_alerts || alerts.length} total</span>
                <span style={{ color: 'var(--text-secondary)' }}>{incidents.length} incidents</span>
              </div>
              {stats?.by_severity && (
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.75rem' }}>
                  {Object.entries(stats.by_severity).map(([sev, count]) => (
                    <span key={sev} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: SEVERITY_COLORS[sev] || '#6b7280' }} />
                      {sev}:{count}
                    </span>
                  ))}
                </div>
              )}
              {stats?.top_alerts && stats.top_alerts.length > 0 && (
                <div style={{ maxHeight: '3.5rem', overflow: 'hidden', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  {stats.top_alerts.slice(0, 3).map((a, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', margin: '0.1rem 0' }}>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>{a.name}</span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>{a.count}x</span>
                    </div>
                  ))}
                </div>
              )}
              {!stats && firingAlerts.length > 0 && (
                <div style={{ maxHeight: '3.5rem', overflow: 'hidden' }}>
                  {firingAlerts.slice(0, 3).map((a, i) => (
                    <p key={i} style={{ fontSize: '0.8rem', margin: '0.1rem 0', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.alertname || a.labels?.alertname || 'Unknown'}
                    </p>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{amHealth?.error || 'Set ALERTMANAGER_URL to connect'}</p>
          )}
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/metrics?type=cpu')}>
          <div className="card-header" style={{ marginBottom: '0.5rem' }}>
            <FiCpu size={18} style={{ color: 'var(--accent-color)' }} />
            <h3>CPU Metrics</h3>
          </div>
          <p className="text-secondary" style={{ fontSize: '0.8rem' }}>Cluster and pod CPU usage, rates, and limits</p>
        </div>
        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/metrics?type=memory')}>
          <div className="card-header" style={{ marginBottom: '0.5rem' }}>
            <FiActivity size={18} style={{ color: 'var(--accent-color)' }} />
            <h3>Memory Metrics</h3>
          </div>
          <p className="text-secondary" style={{ fontSize: '0.8rem' }}>Working set, usage percent, and limits</p>
        </div>
        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/metrics?type=disk')}>
          <div className="card-header" style={{ marginBottom: '0.5rem' }}>
            <FiHardDrive size={18} style={{ color: 'var(--accent-color)' }} />
            <h3>Disk Metrics</h3>
          </div>
          <p className="text-secondary" style={{ fontSize: '0.8rem' }}>Read/write rates, usage, and limits</p>
        </div>
        <div className="glass-panel card-hover" onClick={() => navigate('/monitoring/metrics?type=network')}>
          <div className="card-header" style={{ marginBottom: '0.5rem' }}>
            <FiLayers size={18} style={{ color: 'var(--accent-color)' }} />
            <h3>Network Metrics</h3>
          </div>
          <p className="text-secondary" style={{ fontSize: '0.8rem' }}>RX/TX bytes, packet rates, and latency</p>
        </div>
      </div>

      {incidents.filter(i => i.source === 'alertmanager' || (i.timeline || []).some(t => t.source === 'alertmanager')).length > 0 && (
        <div className="glass-panel" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <FiAlertTriangle size={14} />
            <h3>Alert Incidents</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {incidents.filter(i => i.source === 'alertmanager' || (i.timeline || []).some(t => t.source === 'alertmanager')).slice(0, 5).map((inc) => (
              <div key={inc.id || inc.incident_id}
                className="card-hover"
                onClick={() => navigate('/orchestration/incidents')}
                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}
              >
                <FiAlertTriangle size={14} style={{ color: inc.severity === 'critical' ? '#ef4444' : inc.severity === 'warning' ? '#f59e0b' : '#3b82f6', flexShrink: 0 }} />
                <span className="text-truncate" style={{ flex: 1, fontSize: '0.85rem' }}>{inc.summary || inc.title}</span>
                <span className={`badge ${inc.severity === 'critical' ? 'danger' : inc.severity === 'warning' ? 'warning' : 'neutral'}`} style={{ fontSize: '0.6rem', flexShrink: 0 }}>{inc.severity}</span>
                <span className={`badge ${inc.status === 'open' ? 'warning' : 'success'}`} style={{ fontSize: '0.6rem', flexShrink: 0 }}>{inc.status}</span>
                <FiChevronRight size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
              </div>
            ))}
          </div>
        </div>
      )}

      
    </div>
  );
}
