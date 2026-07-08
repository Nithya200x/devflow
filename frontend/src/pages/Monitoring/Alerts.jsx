import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiArrowLeft, FiAlertTriangle, FiRefreshCw, FiClock, FiTag, FiServer,
  FiExternalLink, FiInfo, FiBarChart2, FiSlash, FiXCircle,
  FiCheckCircle, FiChevronDown, FiChevronRight,
} from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';
import * as alertmanagerService from '../../services/alertmanagerService';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
  none: '#6b7280',
};

function Section({ title, icon: Icon, children }) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {Icon && <Icon size={12} />} {title}
      </div>
      {children}
    </div>
  );
}

function AlertCard({ alert }) {
  const name = alert.alertname || alert.labels?.alertname || alert.name || 'Unknown';
  const severity = alert.severity || alert.labels?.severity || 'info';
  const status = alert.status || 'unknown';
  const namespace = alert.namespace || alert.labels?.namespace || '';
  const pod = alert.pod || alert.labels?.pod || '';
  const instance = alert.instance || '';
  const summary = alert.summary || alert.annotations?.summary || alert.message || '';
  const description = alert.description || alert.annotations?.description || '';
  const startsAt = alert.starts_at || alert.startsAt || '';
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="glass-panel" style={{ padding: expanded ? '1.25rem' : '0.85rem 1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <FiAlertTriangle size={16} style={{ color: status === 'firing' ? '#ef4444' : '#22c55e', marginTop: '0.15rem', flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600, fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
            <span className={`badge ${status === 'firing' ? 'danger' : 'success'}`} style={{ fontSize: '0.6rem' }}>{status}</span>
            <span className={`badge ${severity === 'critical' ? 'danger' : severity === 'warning' ? 'warning' : 'neutral'}`} style={{ fontSize: '0.6rem' }}>{severity}</span>
            <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              {expanded ? <FiChevronDown size={14} /> : <FiChevronRight size={14} />}
            </span>
          </div>
          {summary && (
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: expanded ? 'normal' : 'nowrap' }}>
              {summary}
            </p>
          )}
          {!expanded && (
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)', flexWrap: 'wrap', marginTop: '0.15rem' }}>
              {namespace && <span><FiTag size={11} /> {namespace}</span>}
              {pod && <span><FiServer size={11} /> {pod}</span>}
              {startsAt && <span><FiClock size={11} /> {formatTime(startsAt)}</span>}
            </div>
          )}
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.82rem' }}>
            <div>
              <Section title="Details" icon={FiInfo}>
                {description && <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{description}</p>}
                {instance && <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--text-muted)' }}>Instance:</span><span>{instance}</span></div>}
                {alert.job && <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--text-muted)' }}>Job:</span><span>{alert.job}</span></div>}
                {alert.fingerprint && <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--text-muted)' }}>Fingerprint:</span><span style={{ fontFamily: 'var(--mono-font)', fontSize: '0.75rem' }}>{alert.fingerprint.slice(0, 16)}...</span></div>}
              </Section>
            </div>
            <div>
              <Section title="Timeline" icon={FiClock}>
                {startsAt && <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--text-muted)' }}>Started:</span><span>{formatTime(startsAt)}</span></div>}
                {alert.ends_at && <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--text-muted)' }}>Ended:</span><span>{formatTime(alert.ends_at)}</span></div>}
                {alert.received_at && <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--text-muted)' }}>Received:</span><span>{formatTime(alert.received_at)}</span></div>}
              </Section>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
            {alert.runbook_url && (
              <a href={alert.runbook_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
                <FiExternalLink size={12} /> Runbook
              </a>
            )}
            {alert.generator_url && (
              <a href={alert.generator_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
                <FiBarChart2 size={12} /> Prometheus
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SilenceForm({ onCreated }) {
  const [alertname, setAlertname] = useState('');
  const [severity, setSeverity] = useState('');
  const [duration, setDuration] = useState('1h');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const matchers = [];
      if (alertname) matchers.push({ name: 'alertname', value: alertname, isRegex: false });
      if (severity) matchers.push({ name: 'severity', value: severity, isRegex: false });
      if (matchers.length === 0) {
        setError('Add at least one matcher (alert name or severity)');
        setSubmitting(false);
        return;
      }
      await alertmanagerService.createSilence({ matchers, duration, comment });
      setAlertname('');
      setSeverity('');
      setDuration('1h');
      setComment('');
      if (onCreated) onCreated();
    } catch (err) {
      setError(err.message || 'Failed to create silence');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <div className="input-group" style={{ margin: 0 }}>
          <label>Alert Name</label>
          <input type="text" placeholder="e.g. DevFlowHighCPU" value={alertname} onChange={e => setAlertname(e.target.value)} />
        </div>
        <div className="input-group" style={{ margin: 0 }}>
          <label>Severity</label>
          <select value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="">Any</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <div className="input-group" style={{ margin: 0 }}>
          <label>Duration</label>
          <select value={duration} onChange={e => setDuration(e.target.value)}>
            <option value="15m">15 minutes</option>
            <option value="30m">30 minutes</option>
            <option value="1h">1 hour</option>
            <option value="2h">2 hours</option>
            <option value="6h">6 hours</option>
            <option value="24h">24 hours</option>
            <option value="7d">7 days</option>
          </select>
        </div>
        <div className="input-group" style={{ margin: 0 }}>
          <label>Comment</label>
          <input type="text" placeholder="Why silence?" value={comment} onChange={e => setComment(e.target.value)} />
        </div>
      </div>
      {error && <p style={{ color: '#ef4444', fontSize: '0.82rem' }}>{error}</p>}
      <button className="btn btn-primary btn-sm" type="submit" disabled={submitting} style={{ alignSelf: 'flex-end' }}>
        <FiSlash size={14} /> {submitting ? 'Creating...' : 'Create Silence'}
      </button>
    </form>
  );
}

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return ts;
  return d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
}

export default function ActiveAlerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [silences, setSilences] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [tab, setTab] = useState('active');
  const [showSilenceForm, setShowSilenceForm] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [alertsData, silencesData, historyData, statsData] = await Promise.allSettled([
        alertmanagerService.getAlerts(),
        alertmanagerService.getSilences(),
        alertmanagerService.getAlertHistory({ limit: 50 }),
        alertmanagerService.getAlertStats(),
      ]);
      setAlerts(alertsData.status === 'fulfilled' ? (alertsData.value.alerts || []) : []);
      setSilences(silencesData.status === 'fulfilled' ? (silencesData.value.silences || []) : []);
      setHistory(historyData.status === 'fulfilled' ? (historyData.value.alerts || []) : []);
      setStats(statsData.status === 'fulfilled' ? statsData.value : null);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filteredAlerts = filter === 'all' ? alerts : alerts.filter(a => a.status === filter);
  const firingCount = alerts.filter(a => a.status === 'firing' || a.status === 'active').length;
  const resolvedCount = alerts.filter(a => a.status === 'resolved').length;

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Monitoring
          </button>
          <h1 className="page-title">Alertmanager</h1>
          <p className="page-subtitle">Real-time alerts, history, silences, and statistics.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowSilenceForm(!showSilenceForm)}>
            <FiSlash size={14} /> {showSilenceForm ? 'Hide Silence Form' : 'New Silence'}
          </button>
          <button className="btn" onClick={fetchData} disabled={loading}>
            <FiRefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid-cards" style={{ marginBottom: '1.5rem' }}>
          <div className="glass-panel" style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: firingCount > 0 ? '#ef4444' : '#22c55e' }}>{firingCount}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Active (Firing)</div>
          </div>
          <div className="glass-panel" style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats.total_alerts}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Received</div>
          </div>
          <div className="glass-panel" style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>{silences.length}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Silences</div>
          </div>
          {stats.by_severity && (
            <div className="glass-panel" style={{ padding: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>By Severity</div>
              <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.85rem' }}>
                {Object.entries(stats.by_severity).map(([sev, count]) => (
                  <div key={sev} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: SEVERITY_COLORS[sev] || '#6b7280' }} />
                    <span>{sev}: <strong>{count}</strong></span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {showSilenceForm && (
        <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiSlash size={14} /> Create Silence
          </h3>
          <SilenceForm onCreated={() => { setShowSilenceForm(false); fetchData(); }} />
        </div>
      )}

      <div className="tabs" style={{ marginBottom: '1.5rem' }}>
        {[
          { key: 'active', label: `Active (${alerts.length})` },
          { key: 'history', label: `History (${history.length})` },
          { key: 'silences', label: `Silences (${silences.length})` },
        ].map(t => (
          <button key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'active' && (
        <>
          <div className="tabs" style={{ marginBottom: '1rem', borderBottom: 'none', gap: '0.5rem' }}>
            {[
              { key: 'all', label: `All (${alerts.length})` },
              { key: 'firing', label: `Firing (${firingCount})` },
              { key: 'resolved', label: `Resolved (${resolvedCount})` },
            ].map(t => (
              <button key={t.key} className={`btn btn-ghost btn-sm ${filter === t.key ? 'btn-primary' : ''}`} onClick={() => setFilter(t.key)}>
                {t.label}
              </button>
            ))}
          </div>

          {filteredAlerts.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {filteredAlerts.map((alert, i) => (
                <AlertCard key={alert.fingerprint || i} alert={alert} />
              ))}
            </div>
          ) : (
            <EmptyState message={filter !== 'all' ? `No ${filter} alerts` : 'No alerts from Alertmanager. Is it connected?'} />
          )}
        </>
      )}

      {tab === 'history' && (
        <>
          {history.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {history.slice(0, 50).map((alert, i) => (
                <AlertCard key={alert.fingerprint || i} alert={alert} />
              ))}
            </div>
          ) : (
            <EmptyState message="No alert history yet. Alerts received via webhook will appear here." />
          )}
        </>
      )}

      {tab === 'silences' && (
        <>
          {silences.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {silences.map((s, i) => {
                const sid = s.id?.split('/')?.pop() || s.id || `silence-${i}`;
                const matchers = s.matchers || [];
                const endsAt = s.ends_at || s.endsAt || '';
                const isExpired = endsAt ? new Date(endsAt) < new Date() : false;
                return (
                  <div key={sid} className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem' }}>
                    <div style={{ color: isExpired ? 'var(--text-muted)' : '#f59e0b', flexShrink: 0 }}>
                      {isExpired ? <FiCheckCircle size={16} /> : <FiSlash size={16} />}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {matchers.map((m, mi) => (
                          <span key={mi} className="badge neutral" style={{ fontSize: '0.65rem' }}>{m.name}={m.value}</span>
                        ))}
                        <span className={`badge ${isExpired ? 'neutral' : 'warning'}`} style={{ fontSize: '0.6rem' }}>{isExpired ? 'Expired' : 'Active'}</span>
                      </div>
                      {s.comment && <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>{s.comment}</div>}
                      {endsAt && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>Expires: {formatTime(endsAt)}</div>}
                    </div>
                    {!isExpired && (
                      <button className="btn btn-ghost btn-sm" style={{ color: '#ef4444' }} onClick={async () => { await alertmanagerService.expireSilence(sid); fetchData(); }}>
                        <FiXCircle size={12} /> Expire
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState message="No silences configured. Create one to suppress unwanted alerts." />
          )}
        </>
      )}
    </div>
  );
}
