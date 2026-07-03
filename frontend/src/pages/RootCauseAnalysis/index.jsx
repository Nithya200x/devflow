import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiCpu, FiAlertTriangle, FiLayers, FiRefreshCw, FiCheckCircle, FiXCircle, FiBarChart2, FiTag, FiTarget, FiTool, FiTrendingUp, FiShield, FiClock, FiUser, FiList, FiEye } from 'react-icons/fi';
import * as orchestrationService from '../../services/orchestrationService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

function ConfidenceMeter({ score }) {
  const pct = Math.round(score * 100);
  const color = score > 0.7 ? 'var(--success-color)' : score > 0.4 ? 'var(--warning-color)' : 'var(--danger-color)';
  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Confidence</span>
        <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{pct}%</span>
      </div>
      <div style={{ height: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '5px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: '5px', transition: 'width 0.8s ease' }} />
      </div>
    </div>
  );
}

function Section({ icon, title, children, className = '' }) {
  return (
    <div className={`glass-panel ${className}`} style={{ marginBottom: '1rem' }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', fontSize: '0.95rem' }}>
        {icon} {title}
      </h3>
      {children}
    </div>
  );
}

function IncidentAnalysisView({ incidentId, onBack }) {
  const [analysis, setAnalysis] = useState(null);
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      const [incData, analysisData] = await Promise.all([
        orchestrationService.getIncident(incidentId),
        orchestrationService.getAnalysis(incidentId),
      ]);
      setIncident(incData);
      setAnalysis(analysisData);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => { fetchAnalysis(); }, [fetchAnalysis]);

  const handleTrigger = async () => {
    try {
      setAnalyzing(true);
      await orchestrationService.triggerAnalysis(incidentId);
      setTimeout(() => { fetchAnalysis(); setAnalyzing(false); }, 3000);
    } catch (err) {
      setError(err);
      setAnalyzing(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchAnalysis} />;
  if (!incident) return <EmptyState message="Incident not found" />;

  const hasResult = analysis?.ai_analysis && analysis.status === 'completed';
  const meta = analysis?.ai_metadata || {};

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={onBack} style={{ marginBottom: '0.75rem' }}>
            Back to Analysis List
          </button>
          <h1 className="page-title">{incidentId}</h1>
          <p className="page-subtitle">{incident.summary}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className={`badge ${incident.severity === 'critical' ? 'danger' : incident.severity === 'high' ? 'warning' : 'neutral'}`}>{incident.severity}</span>
          {!hasResult && (
            <button className="btn" onClick={handleTrigger} disabled={analyzing}>
              <FiCpu size={16} /> {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
            </button>
          )}
          {hasResult && (
            <button className="btn btn-ghost" onClick={handleTrigger} disabled={analyzing}>
              <FiRefreshCw size={16} /> {analyzing ? 'Re-analyzing...' : 'Re-run'}
            </button>
          )}
        </div>
      </div>

      {analyzing && (
        <div className="glass-panel" style={{ marginBottom: '1.5rem', textAlign: 'center', padding: '2rem' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }} />
          <p style={{ color: 'var(--text-secondary)' }}>AI analysis in progress — results will appear shortly.</p>
        </div>
      )}

      {hasResult && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <Section icon={<FiTarget size={18} style={{ color: 'var(--accent-color)' }} />} title="Root Cause">
              <div style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent-color)' }}>{analysis.root_cause || 'Unknown'}</div>
              <ConfidenceMeter score={analysis.confidence_score} />
            </Section>

            <Section icon={<FiEye size={18} style={{ color: 'var(--accent-color)' }} />} title="Risk Assessment">
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>{analysis.risk_assessment || 'No risk assessment available.'}</div>
              {analysis.estimated_resolution_time && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', fontSize: '0.85rem' }}>
                  <FiClock size={14} style={{ color: 'var(--accent-color)' }} />
                  <span>Estimated resolution: <strong>{analysis.estimated_resolution_time}</strong></span>
                </div>
              )}
              {analysis.requires_human && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', color: 'var(--warning-color)', fontSize: '0.85rem' }}>
                  <FiUser size={14} /> Requires human intervention
                </div>
              )}
            </Section>
          </div>

          <Section icon={<FiList size={18} style={{ color: 'var(--accent-color)' }} />} title="Analysis Summary">
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.7', whiteSpace: 'pre-wrap' }}>{analysis.ai_analysis}</div>
          </Section>

          {analysis.affected_components?.length > 0 && (
            <Section icon={<FiLayers size={18} style={{ color: 'var(--accent-color)' }} />} title="Affected Components">
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {analysis.affected_components.map((comp, idx) => (
                  <span key={idx} className="badge neutral">{comp}</span>
                ))}
              </div>
            </Section>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            {analysis.suggested_fixes?.length > 0 && (
              <Section icon={<FiTool size={18} style={{ color: 'var(--accent-color)' }} />} title="Recommended Fixes">
                <ul style={{ paddingLeft: '1.25rem', margin: 0, lineHeight: '1.8' }}>
                  {analysis.suggested_fixes.map((fix, idx) => (
                    <li key={idx} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{fix}</li>
                  ))}
                </ul>
              </Section>
            )}

            {analysis.preventive_actions?.length > 0 && (
              <Section icon={<FiShield size={18} style={{ color: 'var(--accent-color)' }} />} title="Preventive Actions">
                <ul style={{ paddingLeft: '1.25rem', margin: 0, lineHeight: '1.8' }}>
                  {analysis.preventive_actions.map((a, idx) => (
                    <li key={idx} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{a}</li>
                  ))}
                </ul>
              </Section>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            {analysis.possible_causes?.length > 0 && (
              <Section icon={<FiAlertTriangle size={18} style={{ color: 'var(--accent-color)' }} />} title="Possible Causes">
                <ul style={{ paddingLeft: '1.25rem', margin: 0, lineHeight: '1.8' }}>
                  {analysis.possible_causes.map((c, idx) => (
                    <li key={idx} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{c}</li>
                  ))}
                </ul>
              </Section>
            )}

            {analysis.similar_patterns?.length > 0 && (
              <Section icon={<FiTrendingUp size={18} style={{ color: 'var(--accent-color)' }} />} title="Similar Patterns">
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {analysis.similar_patterns.map((pat, idx) => (
                    <span key={idx} className="badge warning">{pat}</span>
                  ))}
                </div>
              </Section>
            )}
          </div>

          {(meta.provider || meta.analyzed_at) && (
            <Section icon={<FiCpu size={18} style={{ color: 'var(--accent-color)' }} />} title="Analysis Provider">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {meta.provider && <div>Provider: <strong>{meta.provider}</strong></div>}
                {meta.model && <div>Model: <strong>{meta.model}</strong></div>}
                {meta.analyzed_at && <div>Analyzed: <strong>{new Date(meta.analyzed_at).toLocaleString()}</strong></div>}
                {meta.prompt_version && <div>Prompt v: <strong>{meta.prompt_version}</strong></div>}
              </div>
            </Section>
          )}
        </>
      )}

      {!hasResult && !analyzing && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
          <FiCpu size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>No Analysis Yet</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Click "Run AI Analysis" to trigger root cause analysis for this incident.
          </p>
          <button className="btn" onClick={handleTrigger}>
            <FiCpu size={16} /> Run AI Analysis
          </button>
        </div>
      )}
    </div>
  );
}

function AnalysisCard({ analysis }) {
  const severityClass = analysis.severity === 'critical' ? 'danger' : analysis.severity === 'high' ? 'warning' : 'neutral';
  const pct = Math.round(analysis.confidence_score * 100);
  const confColor = analysis.confidence_score > 0.7 ? 'var(--success-color)' : analysis.confidence_score > 0.4 ? 'var(--warning-color)' : 'var(--danger-color)';

  return (
    <div
      className="glass-panel"
      style={{ cursor: 'pointer' }}
      onClick={() => window.location.href = `/orchestration/incidents/${analysis.incident_id}`}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{analysis.incident_id}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{analysis.summary}</div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
          <span className={`badge ${severityClass}`}>{analysis.severity}</span>
          <span className={`badge ${analysis.status === 'resolved' ? 'success' : 'warning'}`}>{analysis.status}</span>
        </div>
      </div>
      {analysis.root_cause && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <FiTarget size={14} style={{ color: 'var(--accent-color)' }} />
          <span style={{ fontSize: '0.85rem' }}>{analysis.root_cause}</span>
        </div>
      )}
      {analysis.confidence_score > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiBarChart2 size={14} style={{ color: 'var(--accent-color)' }} />
          <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: confColor, borderRadius: '3px', transition: 'width 0.5s ease' }} />
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', minWidth: '3rem', textAlign: 'right' }}>{pct}%</span>
        </div>
      )}
      {analysis.affected_components?.length > 0 && (
        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
          {analysis.affected_components.slice(0, 4).map((c, i) => (
            <span key={i} className="badge neutral" style={{ fontSize: '0.65rem' }}>{c}</span>
          ))}
        </div>
      )}
      {analysis.created_at && (
        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
          {new Date(analysis.created_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}

export default function RootCauseAnalysis() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [triggering, setTriggering] = useState(null);
  const [activeTab, setActiveTab] = useState('all');

  const fetchData = useCallback(async () => {
    try {
      const [analysesData, incidentsData] = await Promise.all([
        orchestrationService.listAnalyses(),
        orchestrationService.getIncidents(),
      ]);
      setAnalyses(analysesData.analyses || []);
      setIncidents(incidentsData || []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleQuickAnalyze = async (incidentId) => {
    try {
      setTriggering(incidentId);
      await orchestrationService.triggerAnalysis(incidentId);
      setTimeout(fetchData, 2000);
    } catch {
    } finally {
      setTriggering(null);
    }
  };

  if (selectedIncident) {
    return (
      <IncidentAnalysisView
        incidentId={selectedIncident}
        onBack={() => setSelectedIncident(null)}
      />
    );
  }

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;

  const analyzedIds = new Set(analyses.map(a => a.incident_id));
  const pendingIncidents = incidents.filter(i => !analyzedIds.has(i.incident_id));
  const criticalAnalyses = analyses.filter(a => a.severity === 'critical' || a.severity === 'high');
  const displayAnalyses = activeTab === 'critical' ? criticalAnalyses : analyses;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Root Cause Analysis</h1>
          <p className="page-subtitle">AI-powered root cause identification for orchestration incidents.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`btn ${activeTab === 'all' ? '' : 'btn-ghost'}`}
            onClick={() => setActiveTab('all')}
          >
            All ({analyses.length})
          </button>
          <button
            className={`btn ${activeTab === 'critical' ? '' : 'btn-ghost'}`}
            onClick={() => setActiveTab('critical')}
          >
            Critical/High ({criticalAnalyses.length})
          </button>
        </div>
      </div>

      {displayAnalyses.length > 0 && (
        <div className="glass-panel" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiSearch size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Completed Analyses ({displayAnalyses.length})</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {displayAnalyses.map(a => (
              <AnalysisCard key={a.incident_id} analysis={a} />
            ))}
          </div>
        </div>
      )}

      {analyses.length === 0 && pendingIncidents.length === 0 && (
        <EmptyState message="No incidents found. Trigger events from the Orchestration Dashboard to create incidents." />
      )}

      {pendingIncidents.length > 0 && (
        <div className="glass-panel" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiAlertTriangle size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Pending Incidents ({pendingIncidents.length})</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {pendingIncidents.slice(0, 20).map(i => (
              <div key={i.incident_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                <div style={{ cursor: 'pointer' }} onClick={() => setSelectedIncident(i.incident_id)}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{i.incident_id}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{i.summary}</div>
                </div>
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                  onClick={() => handleQuickAnalyze(i.incident_id)}
                  disabled={triggering === i.incident_id}
                >
                  {triggering === i.incident_id ? '...' : <FiCpu size={14} />}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {analyses.filter(a => a.suggested_fixes?.length > 0).length > 0 && (
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <FiTool size={20} style={{ color: 'var(--accent-color)' }} />
            <h3 style={{ margin: 0 }}>Suggested Fixes</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {analyses.slice(0, 5).filter(a => a.suggested_fixes?.length > 0).map(a => (
              <div key={a.incident_id} style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem', cursor: 'pointer' }} onClick={() => setSelectedIncident(a.incident_id)}>
                  {a.incident_id}
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {(a.suggested_fixes || []).slice(0, 3).map((f, idx) => (
                    <li key={idx}>{f}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}