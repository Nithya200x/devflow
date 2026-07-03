import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiAlertTriangle, FiRefreshCw, FiClock, FiTag, FiServer, FiEye, FiExternalLink } from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';
import * as alertmanagerService from '../../services/alertmanagerService';

export default function ActiveAlerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [silences, setSilences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [alertsData, silencesData] = await Promise.all([
        alertmanagerService.getAlerts(),
        alertmanagerService.getSilences(),
      ]);
      setAlerts(Array.isArray(alertsData?.alerts) ? alertsData.alerts : []);
      setSilences(Array.isArray(silencesData?.silences) ? silencesData.silences : []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = filter === 'all' ? alerts : alerts.filter(a => a.status === filter);

  const firingCount = alerts.filter(a => a.status === 'firing' || a.status === 'active').length;
  const resolvedCount = alerts.filter(a => a.status === 'resolved').length;

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Monitoring
          </button>
          <h1 className="page-title">Active Alerts</h1>
          <p className="page-subtitle">Real-time alert status from Alertmanager.</p>
        </div>
        <button className="btn" onClick={fetchData} disabled={loading}>
          <FiRefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      <div className="grid-cards" style={{ marginBottom: '1.5rem' }}>
        <div className="glass-panel" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: firingCount > 0 ? 'var(--danger-color)' : 'var(--success-color)' }}>{firingCount}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Firing</div>
        </div>
        <div className="glass-panel" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>{resolvedCount}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Resolved</div>
        </div>
        <div className="glass-panel" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>{silences.length}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Silences</div>
        </div>
      </div>

      <div className="tabs" style={{ marginBottom: '1.5rem' }}>
        {[
          { key: 'all', label: `All (${alerts.length})` },
          { key: 'firing', label: `Firing (${firingCount})` },
          { key: 'resolved', label: `Resolved (${resolvedCount})` },
        ].map(t => (
          <button key={t.key} className={`tab ${filter === t.key ? 'active' : ''}`} onClick={() => setFilter(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner /> : error ? <NetworkError error={error} onRetry={fetchData} /> : (
        filtered.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {filtered.map((alert, i) => {
              const name = alert.alertname || alert.labels?.alertname || alert.name || 'Unknown';
              const severity = alert.severity || alert.labels?.severity || 'info';
              const status = alert.status || 'unknown';
              const namespace = alert.namespace || alert.labels?.namespace || '';
              const pod = alert.pod || alert.labels?.pod || '';
              const instance = alert.instance || '';
              const summary = alert.summary || alert.annotations?.summary || alert.message || '';
              const startsAt = alert.starts_at || alert.startsAt || '';

              return (
                <div key={alert.fingerprint || i} className="glass-panel">
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                    <FiAlertTriangle size={18} style={{ color: status === 'firing' ? 'var(--danger-color)' : 'var(--success-color)', marginTop: '0.15rem' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 600 }}>{name}</span>
                        <span className={`badge ${status === 'firing' ? 'danger' : 'success'}`}>{status}</span>
                        {severity && <span className={`badge ${severity === 'critical' ? 'danger' : severity === 'warning' ? 'warning' : 'neutral'}`}>{severity}</span>}
                      </div>
                      {summary && <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{summary}</p>}
                      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                        {namespace && <span><FiTag size={12} /> {namespace}</span>}
                        {pod && <span><FiServer size={12} /> {pod}</span>}
                        {instance && <span><FiEye size={12} /> {instance}</span>}
                        {startsAt && <span><FiClock size={12} /> {new Date(startsAt).toLocaleString()}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState message={filter !== 'all' ? `No ${filter} alerts` : 'No alerts from Alertmanager. Is it connected?'} />
        )
      )}
    </div>
  );
}
