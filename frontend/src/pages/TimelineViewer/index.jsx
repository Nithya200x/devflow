import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiClock, FiInfo, FiCheckCircle, FiAlertCircle, FiAlertTriangle } from 'react-icons/fi';
import * as orchestrationService from '../../services/orchestrationService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

const EVENT_ICONS = {
  'build_failed': FiAlertCircle,
  'build_started': FiInfo,
  'severity_assigned': FiAlertTriangle,
  'evidence_collected': FiInfo,
  'incident_created': FiAlertCircle,
  'incident_resolved': FiCheckCircle,
};

const EVENT_COLORS = {
  'build_failed': 'var(--danger-color)',
  'build_started': 'var(--accent-color)',
  'severity_assigned': 'var(--warning-color)',
  'evidence_collected': 'var(--accent-color)',
  'incident_created': 'var(--danger-color)',
  'incident_resolved': 'var(--success-color)',
};

export default function TimelineViewer() {
  const { incidentId } = useParams();
  const navigate = useNavigate();
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const data = await orchestrationService.getIncident(incidentId);
      setIncident(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;
  if (!incident) return <EmptyState message="Incident not found" />;

  const timeline = incident.timeline || [];
  const sortedTimeline = [...timeline].sort(
    (a, b) => new Date(a.timestamp || 0) - new Date(b.timestamp || 0)
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate(`/orchestration/incidents/${incidentId}`)} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Incident
          </button>
          <h1 className="page-title">Timeline Viewer</h1>
          <p className="page-subtitle">Event timeline for incident {incidentId}.</p>
        </div>
      </div>

      {timeline.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginTop: '1rem' }}>
          <FiClock size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3>No Timeline Entries</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>This incident has no timeline data.</p>
        </div>
      ) : (
        <div className="glass-panel" style={{ marginTop: '1rem', padding: '2rem' }}>
          <div style={{ position: 'relative' }}>
            {/* Vertical line */}
            <div style={{
              position: 'absolute', left: '20px', top: '0', bottom: '0',
              width: '2px', background: 'rgba(255,255,255,0.1)',
            }} />

            {sortedTimeline.map((entry, idx) => {
              const Icon = EVENT_ICONS[entry.event_type] || FiInfo;
              const color = EVENT_COLORS[entry.event_type] || 'var(--text-secondary)';

              return (
                <div key={idx} style={{
                  display: 'flex', gap: '1rem', marginBottom: '1.5rem',
                  position: 'relative', paddingLeft: '0',
                }}>
                  {/* Icon circle */}
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%',
                    background: 'rgba(255,255,255,0.05)',
                    border: `2px solid ${color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, zIndex: 1,
                  }}>
                    <Icon size={18} style={{ color }} />
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, paddingTop: '0.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h4 style={{ margin: 0, fontSize: '0.95rem' }}>{entry.description}</h4>
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                          <span className="badge neutral" style={{ fontSize: '0.6rem' }}>
                            {entry.source}
                          </span>
                          <span className="badge neutral" style={{ fontSize: '0.6rem', opacity: 0.7 }}>
                            {entry.event_type}
                          </span>
                        </div>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                        {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '—'}
                      </div>
                    </div>

                    {entry.details && (
                      <p style={{
                        fontSize: '0.8rem', color: 'var(--text-secondary)',
                        marginTop: '0.5rem', padding: '0.5rem',
                        background: 'rgba(255,255,255,0.02)', borderRadius: '4px',
                      }}>{entry.details}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
