import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiClock } from 'react-icons/fi';
import { EmptyState } from '../../components/Common/EmptyState';

const PLACEHOLDER_TIMELINE = [
  { time: '—', event: 'Deployment Started', source: 'kubernetes' },
  { time: '—', event: 'Build Started', source: 'jenkins' },
  { time: '—', event: 'Build Completed', source: 'jenkins' },
  { time: '—', event: 'Deployment Started', source: 'kubernetes' },
  { time: '—', event: 'Pod CrashLoopBackOff', source: 'kubernetes' },
  { time: '—', event: 'Incident Created', source: 'system' },
];

export default function TimelineViewer() {
  const { incidentId } = useParams();
  const navigate = useNavigate();

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

      <div className="glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <FiClock size={20} style={{ color: 'var(--accent-color)' }} />
          <h3 style={{ margin: 0 }}>Incident Timeline</h3>
        </div>

        <div style={{ position: 'relative', paddingLeft: '2rem', borderLeft: '2px solid rgba(255,255,255,0.1)' }}>
          {PLACEHOLDER_TIMELINE.map((entry, i) => (
            <div key={i} style={{ marginBottom: '1.5rem', position: 'relative' }}>
              <div style={{
                position: 'absolute', left: '-2.4rem', top: '0.25rem',
                width: '12px', height: '12px', borderRadius: '50%',
                background: 'var(--accent-gradient)', border: '2px solid var(--bg-color)'
              }} />
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                {entry.time}
              </div>
              <div style={{ fontWeight: 600, color: '#fff' }}>{entry.event}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                <span className="badge neutral" style={{ fontSize: '0.6rem' }}>{entry.source}</span>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textAlign: 'center' }}>
            Real-time timeline events will appear here once integrations are connected. Data above is a preview of the expected format.
          </p>
        </div>
      </div>
    </div>
  );
}
