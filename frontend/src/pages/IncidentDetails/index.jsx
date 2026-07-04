import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiArrowLeft, FiClock, FiTag, FiUser, FiCode, FiServer, FiCheckCircle,
  FiLayers, FiFileText, FiExternalLink, FiGitBranch, FiGitCommit, FiCalendar, FiCpu
} from 'react-icons/fi';
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

  const jenkinsEvidence = incident.evidence?.find(e => e.source === 'jenkins');
  const jenkinsData = jenkinsEvidence?.data || {};
  const buildInfo = jenkinsData?.metadata || {};
  const consoleLogs = Array.isArray(jenkinsData?.logs) ? jenkinsData.logs : [];
  const buildUrl = buildInfo?.build_url || '';
  const buildNumber = incident.build_number || buildInfo?.build_number || '';

  const formatDuration = (seconds) => {
    if (!seconds && seconds !== 0) return '-';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

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
            {buildNumber && <div className="deploy-info-item">
              <span className="deploy-info-label">Build</span>
              <span className="deploy-info-value">#{buildNumber}</span>
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
              <span className="deploy-info-value">{incident.created_at ? new Date(incident.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : 'N/A'}</span>
            </div>
            <div className="deploy-info-item">
              <span className="deploy-info-label">Resolved</span>
              <span className="deploy-info-value">{incident.resolved_at ? new Date(incident.resolved_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {incident.description && (
        <div className="glass-panel" style={{ marginBottom: '2rem' }}>
          <h3>Description</h3>
          <pre style={{ color: 'var(--text-secondary)', lineHeight: '1.6', whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{incident.description}</pre>
        </div>
      )}

      {incident.ai_analysis && (
        <div className="glass-panel" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <FiCpu size={18} /> AI Root Cause Analysis
            </h3>
            <button className="btn btn-ghost" style={{ fontSize: '0.8rem' }} onClick={() => navigate('/orchestration/root-cause')}>
              View All Analyses
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-color)' }}>{incident.root_cause || 'Unknown'}</span>
            {incident.confidence_score > 0 && (
              <span className="badge neutral">{Math.round(incident.confidence_score * 100)}% confidence</span>
            )}
            <span className="badge warning">{incident.affected_components?.length || 0} components affected</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '0.5rem' }}>{incident.ai_analysis}</div>
          {incident.suggested_fixes?.length > 0 && (
            <details>
              <summary style={{ cursor: 'pointer', color: 'var(--accent-color)', fontSize: '0.85rem' }}>Suggested Fixes ({incident.suggested_fixes.length})</summary>
              <ul style={{ paddingLeft: '1.25rem', marginTop: '0.5rem', lineHeight: '1.8' }}>
                {incident.suggested_fixes.map((f, i) => (
                  <li key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{f}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Evidence Panel */}
        <div className="glass-panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FiFileText size={18} /> Evidence ({incident.evidence?.length || 0})
          </h3>
          {incident.evidence && incident.evidence.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {incident.evidence.map((ev, idx) => (
                <div key={idx} style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span className="badge neutral">{ev.source}</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                      {ev.collected_at ? new Date(ev.collected_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
                    </span>
                  </div>
                  {ev.source === 'jenkins' && (
                    <div>
                      {ev.data?.metadata?.build_url && (
                        <a href={ev.data.metadata.build_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', marginBottom: '0.4rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                          <FiExternalLink size={12} /> Open Build
                        </a>
                      )}
                      {ev.data?.metadata?.build_status && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          Status: <span className={`badge ${ev.data.metadata.build_status === 'failed' ? 'danger' : ev.data.metadata.build_status === 'success' ? 'success' : 'warning'}`} style={{ fontSize: '0.65rem' }}>{ev.data.metadata.build_status}</span>
                        </p>
                      )}
                      {ev.data?.metadata?.build_result && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Result: {ev.data.metadata.build_result}</p>
                      )}
                      {ev.data?.metadata?.duration_seconds !== undefined && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Duration: {formatDuration(ev.data.metadata.duration_seconds)}</p>
                      )}
                      {consoleLogs.length > 0 && (
                        <details style={{ marginTop: '0.5rem' }}>
                          <summary style={{ cursor: 'pointer', color: 'var(--accent-color)', fontSize: '0.8rem' }}>
                            Console Output ({consoleLogs[0]?.length || 0} chars)
                          </summary>
                          <pre style={{
                            marginTop: '0.5rem', padding: '0.5rem', fontSize: '0.7rem',
                            maxHeight: '200px', overflow: 'auto', background: '#1a1a2e',
                            borderRadius: '4px', color: '#ccc', whiteSpace: 'pre-wrap', wordBreak: 'break-all'
                          }}>{consoleLogs[0] || 'No console output'}</pre>
                        </details>
                      )}
                    </div>
                  )}
                  {ev.source !== 'jenkins' && (
                    <pre style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0, maxHeight: '120px', overflow: 'auto' }}>
                      {JSON.stringify(ev.data, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ cursor: 'pointer' }} onClick={() => navigate(`/orchestration/evidence/${incident.incident_id}`)}>
              <EmptyState message="No evidence collected" />
            </div>
          )}
        </div>

        {/* Timeline Panel */}
        <div className="glass-panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FiClock size={18} /> Timeline ({incident.timeline?.length || 0})
          </h3>
          {incident.timeline && incident.timeline.length > 0 ? (
            <div style={{ position: 'relative', paddingLeft: '1.5rem', borderLeft: '2px solid rgba(255,255,255,0.1)' }}>
              {incident.timeline.map((entry, idx) => (
                <div key={idx} style={{ marginBottom: '1rem', position: 'relative' }}>
                  <div style={{
                    position: 'absolute', left: '-1.65rem', top: '0.25rem',
                    width: '10px', height: '10px', borderRadius: '50%',
                    background: entry.event_type === 'incident_created' ? 'var(--danger-color)'
                      : entry.event_type === 'incident_resolved' ? 'var(--success-color)'
                      : 'var(--accent-gradient)',
                    border: '2px solid var(--bg-color)',
                  }} />
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.15rem' }}>
                    {entry.timestamp ? new Date(entry.timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{entry.description}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                    <span className="badge neutral" style={{ fontSize: '0.6rem' }}>{entry.source}</span>
                    <span style={{ marginLeft: '0.5rem' }}>{entry.event_type}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ cursor: 'pointer' }} onClick={() => navigate(`/orchestration/timeline/${incident.incident_id}`)}>
              <EmptyState message="No timeline entries" />
            </div>
          )}
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
