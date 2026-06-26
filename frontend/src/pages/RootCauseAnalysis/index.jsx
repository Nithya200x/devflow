import { useNavigate } from 'react-router-dom';
import { FiSearch, FiCpu, FiAlertTriangle, FiLayers } from 'react-icons/fi';
import { EmptyState } from '../../components/Common/EmptyState';

export default function RootCauseAnalysis() {
  const navigate = useNavigate();

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Root Cause Analysis</h1>
          <p className="page-subtitle">AI-powered root cause identification for orchestration incidents.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiSearch size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Incident Analysis</h3>
          </div>
          <EmptyState message="Coming in next phase — AI analysis will be available after LLM integration" />
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiCpu size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Pattern Detection</h3>
          </div>
          <EmptyState message="Coming in next phase — Recurring failure pattern identification" />
        </div>
      </div>

      <div className="glass-panel" style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <FiAlertTriangle size={20} style={{ color: 'var(--accent-color)' }} />
          <h3 style={{ margin: 0 }}>Recent Incidents for Analysis</h3>
        </div>
        <div style={{ cursor: 'pointer' }} onClick={() => navigate('/orchestration/incidents')}>
          <EmptyState message="Select an incident to analyze — All incidents" />
        </div>
      </div>

      <div className="glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <FiLayers size={20} style={{ color: 'var(--accent-color)' }} />
          <h3 style={{ margin: 0 }}>Suggested Fixes</h3>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          The AI analysis service will generate remediation suggestions based on incident context.
        </p>
        <EmptyState message="No suggested fixes yet — AI integration pending" />
      </div>
    </div>
  );
}
