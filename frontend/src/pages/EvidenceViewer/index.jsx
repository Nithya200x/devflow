import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiFileText, FiExternalLink, FiClock } from 'react-icons/fi';
import * as orchestrationService from '../../services/orchestrationService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function EvidenceViewer() {
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

  const evidence = incident.evidence || [];
  const bySource = {};
  evidence.forEach(ev => {
    if (!bySource[ev.source]) bySource[ev.source] = [];
    bySource[ev.source].push(ev);
  });

  const formatDuration = (seconds) => {
    if (!seconds && seconds !== 0) return '-';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate(`/orchestration/incidents/${incidentId}`)} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Incident
          </button>
          <h1 className="page-title">Evidence Viewer</h1>
          <p className="page-subtitle">Collected evidence for incident {incidentId}.</p>
        </div>
      </div>

      {evidence.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem', marginTop: '1rem' }}>
          <FiFileText size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3>No Evidence Collected</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>This incident has no evidence attached.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
          {Object.entries(bySource).map(([source, items]) => (
            <div key={source} className="glass-panel">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <FiFileText size={20} style={{ color: 'var(--accent-color)' }} />
                <h3 style={{ margin: 0 }}>{source.charAt(0).toUpperCase() + source.slice(1)} Evidence</h3>
                <span className="badge neutral">{items.length} item{items.length > 1 ? 's' : ''}</span>
              </div>

              {items.map((ev, idx) => (
                <div key={idx} style={{
                  marginBottom: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.02)',
                  borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <FiClock size={12} style={{ marginRight: '0.3rem' }} />
                      {ev.collected_at ? new Date(ev.collected_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '—'}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{ev.evidence_id}</span>
                  </div>

                  <pre style={{
                    fontSize: '0.75rem', color: 'var(--text-secondary)',
                    maxHeight: '300px', overflow: 'auto',
                    background: '#1a1a2e', padding: '0.75rem', borderRadius: '4px',
                    whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                  }}>
                    {JSON.stringify(ev.data, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
