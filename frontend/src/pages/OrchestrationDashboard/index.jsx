import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiAlertTriangle, FiActivity, FiClock, FiTrendingUp, FiBarChart2, FiLayers, FiEye } from 'react-icons/fi';
import { EmptyState } from '../../components/Common/EmptyState';
import { StatCard } from '../../components/Cards/StatCard';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import * as orchestrationService from '../../services/orchestrationService';

export default function OrchestrationDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [statsData, incidentsData] = await Promise.all([
        orchestrationService.getOrchestrationDashboard(),
        orchestrationService.getIncidents({ status: 'open' }),
      ]);
      setStats(statsData);
      setIncidents(Array.isArray(incidentsData) ? incidentsData : []);
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

  const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
  const categoryCounts = {};
  incidents.forEach(inc => {
    severityCounts[inc.severity] = (severityCounts[inc.severity] || 0) + 1;
    if (inc.category) categoryCounts[inc.category] = (categoryCounts[inc.category] || 0) + 1;
  });
  const sortedCategories = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const latestIncident = incidents.length > 0 ? incidents[0] : null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Issue Orchestration</h1>
          <p className="page-subtitle">Event-driven incident lifecycle and root cause analysis platform.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <StatCard icon={FiAlertTriangle} label="Active Incidents" value={stats?.active_incidents ?? 0} color="red" />
        <StatCard icon={FiActivity} label="Critical Incidents" value={stats?.critical_incidents ?? 0} color="red" />
        <StatCard icon={FiClock} label="Avg Resolution Time" value={stats?.avg_resolution_time_seconds ? `${Math.round(stats.avg_resolution_time_seconds)}s` : 'N/A'} color="blue" />
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiBarChart2 size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Severity Distribution</h3>
          </div>
          {Object.keys(severityCounts).some(k => severityCounts[k] > 0) ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {Object.entries(severityCounts).map(([sev, count]) => (
                <div key={sev} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className={`badge ${sev === 'critical' ? 'danger' : sev === 'high' ? 'warning' : sev === 'medium' ? 'neutral' : 'success'}`}
                    style={{ minWidth: '5rem', textAlign: 'center' }}>{sev}</span>
                  <div style={{ flex: 1, height: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${incidents.length > 0 ? (count / incidents.length) * 100 : 0}%`,
                      height: '100%',
                      background: sev === 'critical' ? 'var(--danger-color)' : sev === 'high' ? 'var(--warning-color)' : sev === 'medium' ? 'var(--accent-color)' : 'var(--success-color)',
                      borderRadius: '4px',
                      transition: 'width 0.3s',
                    }} />
                  </div>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', minWidth: '2rem', textAlign: 'right' }}>{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No active incidents" />
          )}
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiLayers size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Top Failure Categories</h3>
          </div>
          {sortedCategories.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {sortedCategories.map(([cat, count]) => (
                <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0.6rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                  <span className="badge neutral">{cat}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{count} incident{count !== 1 ? 's' : ''}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No data available" />
          )}
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/orchestration/incidents')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiTrendingUp size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Latest Incident</h3>
          </div>
          {latestIncident ? (
            <div onClick={() => navigate(`/orchestration/incidents/${latestIncident.incident_id}`)} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span className={`badge ${latestIncident.severity === 'critical' ? 'danger' : latestIncident.severity === 'high' ? 'warning' : 'neutral'}`}>
                  {latestIncident.severity}
                </span>
                <span className={`badge ${latestIncident.status === 'open' ? 'warning' : 'success'}`}>{latestIncident.status}</span>
              </div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{latestIncident.summary}</p>
              {latestIncident.repository && <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{latestIncident.repository}{latestIncident.build_number ? ` · build #${latestIncident.build_number}` : ''}</p>}
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                {latestIncident.created_at ? new Date(latestIncident.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
              </p>
            </div>
          ) : (
            <EmptyState message="No incidents yet" />
          )}
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiLayers size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Registered Collectors</h3>
          </div>
          {stats?.registered_collectors?.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {stats.registered_collectors.map(c => (
                <span key={c} className="badge neutral">{c}</span>
              ))}
            </div>
          ) : (
            <EmptyState message="No collectors registered" />
          )}
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.75rem' }}>
            {stats?.event_buffer_size ?? 0} events in buffer
          </p>
        </div>
      </div>
    </div>
  );
}
