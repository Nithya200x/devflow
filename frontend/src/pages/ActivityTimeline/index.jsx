import { useState, useEffect, useCallback } from 'react';
import { FiClock, FiGitBranch, FiBox, FiLayers, FiBarChart2, FiAlertTriangle, FiCheckCircle, FiXCircle, FiActivity, FiCpu, FiServer } from 'react-icons/fi';
import * as orchestrationService from '../../services/orchestrationService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

const EVENT_ICONS = {
  REPOSITORY_CONNECTED: FiGitBranch,
  DEPLOYMENT_REQUESTED: FiBox,
  BUILD_STARTED: FiActivity,
  BUILD_SUCCEEDED: FiCheckCircle,
  BUILD_FAILED: FiXCircle,
  DEPLOYMENT_STARTED: FiLayers,
  DEPLOYMENT_SUCCEEDED: FiCheckCircle,
  DEPLOYMENT_FAILED: FiXCircle,
  CONTAINER_CRASHED: FiAlertTriangle,
  CONTAINER_UNHEALTHY: FiAlertTriangle,
  CRASH_LOOP_BACK_OFF: FiAlertTriangle,
  HIGH_CPU_DETECTED: FiCpu,
  HIGH_MEMORY_DETECTED: FiServer,
  HEALTH_CHECK_FAILED: FiXCircle,
  INCIDENT_CREATED: FiAlertTriangle,
  INCIDENT_RESOLVED: FiCheckCircle,
  NODE_NOT_READY: FiAlertTriangle,
  POD_RESTARTED: FiActivity,
};

const EVENT_COLORS = {
  REPOSITORY_CONNECTED: '#22c55e',
  DEPLOYMENT_REQUESTED: '#3b82f6',
  BUILD_STARTED: '#f59e0b',
  BUILD_SUCCEEDED: '#22c55e',
  BUILD_FAILED: '#ef4444',
  DEPLOYMENT_STARTED: '#3b82f6',
  DEPLOYMENT_SUCCEEDED: '#22c55e',
  DEPLOYMENT_FAILED: '#ef4444',
  CONTAINER_CRASHED: '#ef4444',
  CONTAINER_UNHEALTHY: '#f97316',
  CRASH_LOOP_BACK_OFF: '#ef4444',
  HIGH_CPU_DETECTED: '#f59e0b',
  HIGH_MEMORY_DETECTED: '#f59e0b',
  HEALTH_CHECK_FAILED: '#ef4444',
  INCIDENT_CREATED: '#ec4899',
  INCIDENT_RESOLVED: '#22c55e',
  NODE_NOT_READY: '#ef4444',
  POD_RESTARTED: '#f59e0b',
};

function formatEventName(name) {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
}

export default function ActivityTimeline() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  const fetchEvents = useCallback(async () => {
    try {
      const data = await orchestrationService.getEventHistory();
      setEvents(Array.isArray(data) ? data : data.events || []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 15000);
    return () => clearInterval(interval);
  }, [fetchEvents]);

  const filtered = filter === 'all' ? events : events.filter(e => e.event_type === filter);

  const eventTypes = [...new Set(events.map(e => e.event_type))];

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchEvents} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Activity Timeline</h1>
          <p className="page-subtitle">Infrastructure events in chronological order.</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('all')}
          style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
        >All</button>
        {eventTypes.slice(0, 8).map(type => (
          <button
            key={type}
            className={`btn ${filter === type ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter(type)}
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
          >{formatEventName(type)}</button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={FiClock}
          message="No events yet"
          description="Infrastructure events will appear here as they occur."
        />
      ) : (
        <div style={{ position: 'relative' }}>
          <div style={{
            position: 'absolute', left: 15, top: 0, bottom: 0, width: 2,
            background: 'linear-gradient(to bottom, var(--accent-blue), var(--accent-purple))',
            opacity: 0.3, borderRadius: 1,
          }} />
          {filtered.slice().reverse().map((event, i) => {
            const Icon = EVENT_ICONS[event.event_type] || FiActivity;
            const color = EVENT_COLORS[event.event_type] || 'var(--text-secondary)';
            return (
              <div key={event.id || i} style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', position: 'relative' }}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%', background: `${color}20`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, color, zIndex: 1,
                }}>
                  <Icon size={14} />
                </div>
                <div className="glass-panel" style={{ flex: 1, padding: '0.75rem 1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{formatEventName(event.event_type)}</span>
                    <span className="badge neutral" style={{ fontSize: '0.7rem' }}>{event.source}</span>
                  </div>
                  {event.metadata && Object.keys(event.metadata).length > 0 && (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', margin: '0.25rem 0' }}>
                      {event.metadata.project_id && `Project: ${event.metadata.project_id}`}
                      {event.metadata.pod_name && ` · Pod: ${event.metadata.pod_name}`}
                      {event.metadata.namespace && ` · Namespace: ${event.metadata.namespace}`}
                      {event.metadata.severity && (
                        <span className={`badge ${
                          event.metadata.severity === 'critical' ? 'danger' :
                          event.metadata.severity === 'warning' ? 'pending' : 'info'
                        }`} style={{ marginLeft: '0.5rem', fontSize: '0.7rem' }}>
                          {event.metadata.severity}
                        </span>
                      )}
                    </p>
                  )}
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                    {event.timestamp ? new Date(event.timestamp).toLocaleString() : ''}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
