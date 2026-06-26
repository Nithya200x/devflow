import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiClock, FiTag, FiUser, FiCode, FiServer, FiCheckCircle, FiLayers } from 'react-icons/fi';
import * as orchestrationService from '../../services/orchestrationService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function IncidentDetails() {
  const { incidentId } = useParams();
  const navigate = useNavigate();
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchIncident = useCallback(async () => {
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

  useEffect(() => { fetchIncident(); }, [fetchIncident]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchIncident} />;
  if (!incident) return <EmptyState message="Incident not found" />;

  const severityClass = incident.severity === 'critical' ? 'danger' : incident.severity === 'high' ? 'warning' : 'neutral';

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/orchestration/incidents')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Incidents
          </button>
          <h1 className="page-title">{incident.incident_id}</h1>
          <p className="page-subtitle">{incident.summary}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <span className={`badge ${severityClass}`}>{incident.severity}</span>
          <span className={`badge ${incident.status === 'resolved' ? 'success' : incident.status === 'open' ? 'warning' : 'neutral'}`}>{incident.status}</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass-panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FiServer /> Context</h3>
          <div className="deploy-info-grid">
            {incident.repository && <div className="deploy-info-item">
              <span className="deploy-info-label">Repository</span>
              <span className="deploy-info-value"><code>{incident.repository}</code></span>
            </div>}
            {incident.environment && <div className="deploy-info-item">
              <span className="deploy-info-label">Environment</span>
              <span className="deploy-info-value">{incident.environment}</span>
            </div>}
            {incident.branch && <div className="deploy-info-item">
              <span className="deploy-info-label">Branch</span>
              <span className="deploy-info-value"><code>{incident.branch}</code></span>
            </div>}
            {incident.commit_sha && <div className="deploy-info-item">
              <span className="deploy-info-label">Commit</span>
              <span className="deploy-info-value"><code>{incident.commit_sha?.slice(0, 8)}</code></span>
            </div>}
            {incident.build_number && <div className="deploy-info-item">
              <span className="deploy-info-label">Build</span>
              <span className="deploy-info-value">{incident.build_number}</span>
            </div>}
            {incident.deployment_id && <div className="deploy-info-item">
              <span className="deploy-info-label">Deployment</span>
              <span className="deploy-info-value">{incident.deployment_id}</span>
            </div>}
          </div>
        </div>

        <div className="glass-panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FiTag /> Details</h3>
          <div className="deploy-info-grid">
            <div className="deploy-info-item">
              <span className="deploy-info-label">Category</span>
              <span className="deploy-info-value">{incident.category || 'Uncategorized'}</span>
            </div>
            <div className="deploy-info-item">
              <span className="deploy-info-label">Assigned To</span>
              <span className="deploy-info-value">{incident.assigned_to || 'Unassigned'}</span>
            </div>
            <div className="deploy-info-item">
              <span className="deploy-info-label">Created</span>
              <span className="deploy-info-value">{incident.created_at ? new Date(incident.created_at).toLocaleString() : 'N/A'}</span>
            </div>
            <div className="deploy-info-item">
              <span className="deploy-info-label">Resolved</span>
              <span className="deploy-info-value">{incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {incident.description && (
        <div className="glass-panel" style={{ marginBottom: '2rem' }}>
          <h3>Description</h3>
          <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>{incident.description}</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate(`/orchestration/evidence/${incident.incident_id}`)}>
          <h3>Evidence ({incident.evidence?.length || 0})</h3>
          <EmptyState message="No evidence collected — Coming in next phase" />
        </div>
        <div className="glass-panel" style={{ cursor: 'pointer' }} onClick={() => navigate(`/orchestration/timeline/${incident.incident_id}`)}>
          <h3>Timeline ({incident.timeline?.length || 0})</h3>
          <EmptyState message="No timeline entries — Coming in next phase" />
        </div>
      </div>

      {incident.status !== 'resolved' && (
        <button className="btn btn-success" onClick={async () => {
          await orchestrationService.resolveIncident(incident.incident_id);
          fetchIncident();
        }}>
          <FiCheckCircle size={16} /> Resolve Incident
        </button>
      )}
    </div>
  );
}
