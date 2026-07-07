import { useState, useEffect, useCallback } from 'react';
import {
  FiCheckCircle, FiChevronDown, FiChevronRight,
  FiActivity, FiClock, FiAlertTriangle, FiCpu,
  FiCopy, FiBarChart2, FiShield, FiAlertOctagon,
} from 'react-icons/fi';
import * as incidentService from '../../services/incidentService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

const SOURCE_META = {
  prometheus_high_error_rate: { icon: FiAlertTriangle, label: 'High Error Rate', color: 'red' },
  prometheus_high_latency: { icon: FiClock, label: 'High Latency', color: 'violet' },
  prometheus_service_down: { icon: FiActivity, label: 'Service Down', color: 'danger' },
};

function formatSource(source) {
  if (SOURCE_META[source]) return SOURCE_META[source].label;
  return source.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function SourceIcon({ source }) {
  const meta = SOURCE_META[source];
  if (!meta) return null;
  const Icon = meta.icon;
  return <Icon size={14} style={{ color: `var(--${meta.color === 'danger' ? 'danger' : meta.color}-color)` }} />;
}

function formatTimestamp(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
}

function EventIcon({ eventType }) {
  const icons = {
    prometheus_alert: { icon: FiAlertTriangle, color: 'var(--warning-color)' },
    incident_created: { icon: FiActivity, color: 'var(--info-color)' },
    incident_resolved: { icon: FiCheckCircle, color: 'var(--success-color)' },
    auto_resolved: { icon: FiCheckCircle, color: 'var(--success-color)' },
    ai_analysis_completed: { icon: FiCpu, color: 'var(--violet-color)' },
    ai_analysis_reused: { icon: FiCpu, color: 'var(--violet-color)' },
    ai_analysis_failed: { icon: FiCpu, color: 'var(--danger-color)' },
    ai_analysis_error: { icon: FiCpu, color: 'var(--danger-color)' },
    ai_analysis_rate_limited: { icon: FiClock, color: 'var(--warning-color)' },
  };
  const meta = icons[eventType];
  if (!meta) return <div style={{ width: 12, height: 12, borderRadius: '50%', background: 'var(--text-secondary)', flexShrink: 0 }} />;
  const Icon = meta.icon;
  return <Icon size={12} style={{ color: meta.color, flexShrink: 0 }} />;
}

function Timeline({ events }) {
  if (!events || events.length === 0) return null;
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        <FiClock size={11} style={{ marginRight: '0.3rem', display: 'inline' }} />
        Timeline
      </div>
      <div style={{ position: 'relative', paddingLeft: '1.25rem' }}>
        <div style={{ position: 'absolute', left: 5, top: 4, bottom: 4, width: 1, background: 'rgba(255,255,255,0.1)' }} />
        {events.map((evt, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.4rem', fontSize: '0.8rem' }}>
            <EventIcon eventType={evt.event_type} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', marginRight: '0.4rem' }}>
                {formatTimestamp(evt.timestamp)}
              </span>
              <span style={{ color: 'var(--text-primary)' }}>{evt.description}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await incidentService.getIncidents();
      setIncidents(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const resolveIncident = async (id) => {
    try {
      await incidentService.resolveIncident(id);
      await fetchIncidents();
    } catch (err) {
      setError(err);
    }
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchIncidents} />;
  if (!incidents.length) return <EmptyState message="No incidents found" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Incidents</h1>
          <p className="page-subtitle">Track and resolve platform alerts.</p>
        </div>
      </div>
      {incidents.map((row) => {
        const isOpen = expandedId === row.id;
        return (
          <div key={row.id} className="glass-panel card-hover" style={{ marginBottom: '0.75rem', padding: 0 }}>
            <div
              onClick={() => toggleExpand(row.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.75rem 1rem', cursor: 'pointer',
              }}
            >
              <div style={{ color: 'var(--text-secondary)', flexShrink: 0 }}>
                {isOpen ? <FiChevronDown size={16} /> : <FiChevronRight size={16} />}
              </div>
              <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                  #{row.id}
                </span>
                <strong style={{ flex: 1, minWidth: 140 }}>{row.title}</strong>
                {row.source && (
                  <span className="repo-meta-item" style={{ fontSize: '0.75rem', gap: '0.3rem' }}>
                    <SourceIcon source={row.source} />
                    {formatSource(row.source)}
                  </span>
                )}
                <span className={`badge ${row.severity}`} style={{ fontSize: '0.7rem' }}>{row.severity}</span>
                <span className={`badge ${row.status === 'open' ? 'warning' : 'success'}`} style={{ fontSize: '0.7rem' }}>{row.status}</span>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', flexShrink: 0, whiteSpace: 'nowrap' }}>
                {formatTimestamp(row.created_at)}
              </div>
              {row.status !== 'resolved' && (
                <button
                  className="btn btn-success"
                  style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', flexShrink: 0 }}
                  onClick={(e) => { e.stopPropagation(); resolveIncident(row.id); }}
                >
                  <FiCheckCircle size={12} /> Resolve
                </button>
              )}
            </div>
            {isOpen && (
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '1rem 1rem 1rem 2.75rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    {row.description && (
                      <div style={{ marginBottom: '0.75rem' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Description</div>
                        <div style={{ fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>{row.description}</div>
                      </div>
                    )}
                    {row.resolution_reason && (
                      <div style={{ marginBottom: '0.75rem' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                          <FiCheckCircle size={11} style={{ marginRight: '0.3rem', display: 'inline' }} />
                          Resolution
                        </div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--success-color)' }}>{row.resolution_reason}</div>
                      </div>
                    )}
                    <Timeline events={row.timeline} />
                  </div>

                  <div>
                    {row.ai_summary && (
                      <div className="glass-panel" style={{ padding: '0.75rem', background: 'rgba(168,85,247,0.05)' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <FiCpu size={14} style={{ color: '#a855f7' }} />
                          AI Recommendation
                        </div>

                        <div style={{ marginBottom: '0.5rem' }}>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Root Cause</div>
                          <div style={{ fontSize: '0.82rem', fontWeight: 500 }}>{row.root_cause || row.ai_summary}</div>
                        </div>

                        {row.confidence_score !== undefined && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Confidence Score</div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                              <FiBarChart2 size={12} style={{ color: row.confidence_score > 0.7 ? '#22c55e' : row.confidence_score > 0.4 ? '#f59e0b' : '#ef4444' }} />
                              <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>
                                {Math.round((row.confidence_score || 0) * 100)}%
                              </span>
                            </div>
                          </div>
                        )}

                        {row.estimated_resolution_time && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Estimated Resolution Time</div>
                            <div style={{ fontSize: '0.82rem' }}>{row.estimated_resolution_time}</div>
                          </div>
                        )}

                        {row.risk_assessment && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Risk Assessment</div>
                            <div style={{ fontSize: '0.82rem' }}>{row.risk_assessment}</div>
                          </div>
                        )}

                        {row.affected_components && row.affected_components.length > 0 && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Affected Components</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.2rem' }}>
                              {row.affected_components.map((c, i) => (
                                <span key={i} className="badge danger" style={{ fontSize: '0.65rem' }}>{c}</span>
                              ))}
                            </div>
                          </div>
                        )}

                        {row.suggested_fixes && row.suggested_fixes.length > 0 && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                              <FiCheckCircle size={11} style={{ marginRight: '0.3rem', display: 'inline' }} />
                              Recommended Fixes
                            </div>
                            {row.suggested_fixes.map((fix, i) => (
                              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem', background: 'rgba(255,255,255,0.03)', padding: '0.3rem 0.5rem', borderRadius: '4px' }}>
                                <span style={{ flex: 1, fontSize: '0.8rem' }}>{fix}</span>
                                <button
                                  className="btn btn-ghost btn-sm"
                                  style={{ padding: '0.2rem', minWidth: 'auto' }}
                                  onClick={() => navigator.clipboard.writeText(fix)}
                                  title="Copy command"
                                >
                                  <FiCopy size={12} />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}

                        {row.possible_causes && row.possible_causes.length > 0 && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                              <FiAlertOctagon size={11} style={{ marginRight: '0.3rem', display: 'inline' }} />
                              Possible Causes
                            </div>
                            <ul style={{ margin: 0, paddingLeft: '1rem', fontSize: '0.8rem' }}>
                              {row.possible_causes.map((c, i) => (
                                <li key={i} style={{ marginBottom: '0.15rem' }}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {row.preventive_actions && row.preventive_actions.length > 0 && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                              <FiShield size={11} style={{ marginRight: '0.3rem', display: 'inline' }} />
                              Preventive Actions
                            </div>
                            <ul style={{ margin: 0, paddingLeft: '1rem', fontSize: '0.8rem' }}>
                              {row.preventive_actions.map((a, i) => (
                                <li key={i} style={{ marginBottom: '0.15rem' }}>{a}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    {!row.ai_summary && (
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        AI analysis pending...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
