import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiSearch, FiFileText } from 'react-icons/fi';
import { EmptyState } from '../../components/Common/EmptyState';

export default function EvidenceViewer() {
  const { incidentId } = useParams();
  const navigate = useNavigate();

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

      <div className="glass-panel" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <FiSearch size={20} style={{ color: 'var(--accent-color)' }} />
          <h3 style={{ margin: 0 }}>Evidence Sources</h3>
        </div>
        <div className="grid-cards" style={{ marginBottom: '1rem' }}>
          {['GitHub', 'Jenkins', 'Docker', 'Kubernetes', 'Prometheus', 'Grafana'].map(source => (
            <div key={source} className="glass-panel" style={{ padding: '1.25rem', cursor: 'pointer', opacity: 0.6 }}
              onMouseEnter={e => e.currentTarget.style.opacity = '1'}
              onMouseLeave={e => e.currentTarget.style.opacity = '0.6'}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <FiFileText size={16} style={{ color: 'var(--accent-color)' }} />
                <strong>{source}</strong>
              </div>
              <EmptyState message="Not implemented — Coming in next phase" />
            </div>
          ))}
        </div>
      </div>

      <div className="glass-panel">
        <h3>Aggregated Evidence</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Cross-referenced evidence from all collectors will appear here once integrations are active.
        </p>
        <EmptyState message="No evidence data available" />
      </div>
    </div>
  );
}
