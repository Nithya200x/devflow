import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiArrowLeft, FiMonitor, FiExternalLink, FiRefreshCw,
  FiActivity, FiAlertTriangle, FiClock, FiCpu, FiCheckCircle
} from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { getMetricsSummary } from '../../services/metricsService';
import config from '../../config/config';

function StatCard({ icon: Icon, label, value, color = 'blue' }) {
  return (
    <div className="glass-panel card-hover stat-card" style={{ gap: '1rem' }}>
      <div className={`stat-icon-wrap ${color}`}><Icon size={22} /></div>
      <div className="stat-body">
        <h3>{label}</h3>
        <p>{value}</p>
      </div>
    </div>
  );
}

export default function MetricsDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const dashboardUrl = config.GRAFANA_DASHBOARD_URL;

  const fetchMetrics = useCallback(async () => {
    try {
      const result = await getMetricsSummary();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    intervalRef.current = setInterval(fetchMetrics, 30000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchMetrics]);

  const handleRefresh = () => {
    setLoading(true);
    fetchMetrics();
  };

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
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Monitoring
          </button>
          <h1 className="page-title">Live Dashboard</h1>
          <p className="page-subtitle">Real-time application metrics from Prometheus.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <span className={`badge ${statusClass}`} style={{ alignSelf: 'center' }}>
            {statusLabel}
          </span>
          <button className="btn" onClick={handleRefresh} disabled={loading}>
            <FiRefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
          </button>
          {dashboardUrl && (
            <a href={dashboardUrl} target="_blank" rel="noopener noreferrer" className="btn">
              <FiExternalLink size={16} /> Open in Grafana
            </a>
          )}
        </div>
      </div>

      {loading && !data ? (
        <LoadingSpinner text="Loading metrics..." />
      ) : error ? (
        <NetworkError error={error} onRetry={fetchMetrics} />
      ) : (
        <div className="page-enter">
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            <StatCard icon={FiActivity} label="Total Requests" value={requests.toLocaleString()} color="blue" />
            <StatCard icon={FiAlertTriangle} label="Error Rate" value={`${errorRate}%`} color={errorRate > 5 ? 'red' : 'green'} />
            <StatCard icon={FiClock} label="P95 Latency" value={displayLatency} color="violet" />
            <StatCard icon={FiCpu} label="Active Requests" value={activeRequests} color="cyan" />
          </div>

          {status === 'healthy' && (
            <div className="glass-panel" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem 1.25rem' }}>
              <FiCheckCircle size={18} style={{ color: 'var(--success-color)' }} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Metrics pipeline healthy</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.15rem' }}>
                  Alloy scraping active &middot; data flowing to Grafana Cloud
                </div>
              </div>
            </div>
          )}

          {status === 'no_data' && (
            <div className="glass-panel" style={{ marginTop: '1rem', textAlign: 'center', padding: '2rem' }}>
              <FiMonitor size={32} style={{ color: 'var(--text-secondary)', marginBottom: '0.75rem' }} />
              <h3 style={{ marginBottom: '0.5rem' }}>No Metrics Data</h3>
              <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto', fontSize: '0.85rem' }}>
                Prometheus is connected but no application metrics have been received yet. 
                Metrics appear after the first HTTP request is processed by the backend.
              </p>
            </div>
          )}

          {dashboardUrl && (
            <div className="glass-panel" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FiMonitor size={16} style={{ color: 'var(--accent-color)' }} />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Full observability dashboard available in Grafana Cloud
                </span>
              </div>
              <a href={dashboardUrl} target="_blank" rel="noopener noreferrer" className="btn btn-sm">
                <FiExternalLink size={14} /> Open in Grafana
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
