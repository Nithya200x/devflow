import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiActivity, FiBarChart2, FiPieChart, FiAlertTriangle, FiServer, FiLayers, FiCpu, FiHardDrive } from 'react-icons/fi';
import { StatCard } from '../../components/Cards/StatCard';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import * as prometheusService from '../../services/prometheusService';
import * as grafanaService from '../../services/grafanaService';
import * as alertmanagerService from '../../services/alertmanagerService';

export default function MonitoringDashboard() {
  const navigate = useNavigate();
  const [promHealth, setPromHealth] = useState(null);
  const [grafanaHealth, setGrafanaHealth] = useState(null);
  const [amHealth, setAmHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [ph, gh, ah, alertsData] = await Promise.allSettled([
        prometheusService.getPrometheusHealth(),
        grafanaService.getGrafanaHealth(),
        alertmanagerService.getAlertmanagerHealth(),
        alertmanagerService.getAlerts(),
      ]);
      setPromHealth(ph.status === 'fulfilled' ? ph.value : { connected: false, error: 'Failed to connect' });
      setGrafanaHealth(gh.status === 'fulfilled' ? gh.value : { connected: false, error: 'Failed to connect' });
      setAmHealth(ah.status === 'fulfilled' ? ah.value : { connected: false, error: 'Failed to connect' });
      setAlerts(alertsData.status === 'fulfilled' ? (alertsData.value.alerts || []) : []);
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
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/metrics')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiBarChart2 size={20} style={{ color: promHealth?.connected ? 'var(--success-color)' : 'var(--text-secondary)' }} />
            <h3 style={{ margin: 0 }}>Prometheus</h3>
            <span className={`badge ${promHealth?.connected ? 'success' : 'danger'}`} style={{ marginLeft: 'auto' }}>
              {promHealth?.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {promHealth?.connected ? (
            <div className="grid-2-cols" style={{ gap: '0.75rem' }}>
              <div><span className="deploy-info-label">Version</span><span className="deploy-info-value">{promHealth.version || 'N/A'}</span></div>
              <div><span className="deploy-info-label">Latency</span><span className="deploy-info-value">{promHealth.latency_ms ? `${promHealth.latency_ms}ms` : 'N/A'}</span></div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{promHealth?.error || 'Set PROMETHEUS_URL to connect'}</p>
          )}
        </div>

        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/dashboards')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiPieChart size={20} style={{ color: grafanaHealth?.connected ? 'var(--success-color)' : 'var(--text-secondary)' }} />
            <h3 style={{ margin: 0 }}>Grafana</h3>
            <span className={`badge ${grafanaHealth?.connected ? 'success' : 'danger'}`} style={{ marginLeft: 'auto' }}>
              {grafanaHealth?.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {grafanaHealth?.connected ? (
            <div className="grid-2-cols" style={{ gap: '0.75rem' }}>
              <div><span className="deploy-info-label">Version</span><span className="deploy-info-value">{grafanaHealth.version || 'N/A'}</span></div>
              <div><span className="deploy-info-label">Latency</span><span className="deploy-info-value">{grafanaHealth.latency_ms ? `${grafanaHealth.latency_ms}ms` : 'N/A'}</span></div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{grafanaHealth?.error || 'Set GRAFANA_URL to connect'}</p>
          )}
        </div>

        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/alerts')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiAlertTriangle size={20} style={{ color: firingAlerts.length > 0 ? 'var(--danger-color)' : 'var(--success-color)' }} />
            <h3 style={{ margin: 0 }}>Alertmanager</h3>
            <span className={`badge ${amHealth?.connected ? 'success' : 'danger'}`} style={{ marginLeft: 'auto' }}>
              {amHealth?.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {amHealth?.connected ? (
            <div>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
                <span style={{ color: 'var(--danger-color)', fontWeight: 600 }}>{firingAlerts.length} firing</span>
                <span style={{ color: 'var(--text-secondary)' }}>{alerts.length} total</span>
              </div>
              {firingAlerts.length > 0 && (
                <div style={{ maxHeight: '4rem', overflow: 'hidden' }}>
                  {firingAlerts.slice(0, 3).map((a, i) => (
                    <p key={i} style={{ fontSize: '0.8rem', margin: '0.15rem 0', color: 'var(--text-secondary)' }}>
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
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/metrics?type=cpu')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <FiCpu size={18} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0, fontSize: '0.95rem' }}>CPU Metrics</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Cluster and pod CPU usage, rates, and limits</p>
        </div>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/metrics?type=memory')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <FiActivity size={18} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Memory Metrics</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Working set, usage percent, and limits</p>
        </div>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/metrics?type=disk')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <FiHardDrive size={18} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Disk Metrics</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Read/write rates, usage, and limits</p>
        </div>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/monitoring/metrics?type=network')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <FiLayers size={18} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Network Metrics</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>RX/TX bytes, packet rates, and latency</p>
        </div>
      </div>

      
    </div>
  );
}
