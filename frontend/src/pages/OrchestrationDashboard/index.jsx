import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiAlertTriangle, FiActivity, FiClock, FiTrendingUp, FiBarChart2, FiLayers, FiList } from 'react-icons/fi';
import { EmptyState } from '../../components/Common/EmptyState';
import { StatCard } from '../../components/Cards/StatCard';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import * as orchestrationService from '../../services/orchestrationService';

export default function OrchestrationDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const data = await orchestrationService.getOrchestrationDashboard();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchStats} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Issue Orchestration</h1>
          <p className="page-subtitle">Event-driven incident lifecycle and root cause analysis platform.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <StatCard icon={FiAlertTriangle} label="Active Incidents" value={stats?.active_incidents ?? 'No data'} color="red" />
        <StatCard icon={FiActivity} label="Critical Incidents" value={stats?.critical_incidents ?? 'No data'} color="red" />
        <StatCard icon={FiClock} label="Avg Resolution Time" value={stats?.avg_resolution_time_seconds ? `${Math.round(stats.avg_resolution_time_seconds)}s` : 'No data'} color="blue" />
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/orchestration/incidents')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiList size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Incident Trend</h3>
          </div>
          <EmptyState message="No data available" />
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiBarChart2 size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Top Failure Categories</h3>
          </div>
          <EmptyState message="No data available" />
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate('/orchestration/history')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiTrendingUp size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Event History</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            {stats?.event_buffer_size ?? 0} events in buffer
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.5rem' }}>
            Coming in next phase — Event stream visualization with real-time filtering.
          </p>
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
        </div>
      </div>
    </div>
  );
}
