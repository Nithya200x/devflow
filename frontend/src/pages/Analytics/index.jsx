import { useState, useEffect, useCallback } from 'react';
import { FiTrendingUp, FiBarChart2, FiPieChart, FiActivity, FiCpu, FiHardDrive, FiAlertTriangle } from 'react-icons/fi';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import * as analyticsService from '../../services/analyticsService';
import { StatCard } from '../../components/Cards/StatCard';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(7);

  const fetchData = useCallback(async () => {
    try {
      const result = await analyticsService.getAnalyticsDashboard(days);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchData} />;
  if (!data) return null;

  const healthData = data.healthBreakdown ? Object.entries(data.healthBreakdown).map(([name, connected]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: connected ? 1 : 0,
    status: connected ? 'Healthy' : 'Unhealthy',
  })) : [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">Historical deployment and infrastructure analytics.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[7, 14, 30].map(d => (
            <button
              key={d}
              className={`btn ${days === d ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => { setDays(d); setLoading(true); }}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
            >{d}d</button>
          ))}
        </div>
      </div>

      <div className="grid-cards stagger-children" style={{ marginBottom: '2rem' }}>
        <StatCard label="Success Rate" value={`${data.deploymentSuccessRate}%`} icon={FiTrendingUp} color="#22c55e" />
        <StatCard label="Total Deployments" value={data.totalDeployments} icon={FiBarChart2} color="#3b82f6" />
        <StatCard label="Avg Duration" value={`${data.avgDeploymentDuration}s`} icon={FiActivity} color="#f59e0b" />
        <StatCard label="Infra Health" value={`${data.infrastructureHealthScore}%`} icon={FiPieChart} color={data.infrastructureHealthScore > 50 ? '#22c55e' : '#ef4444'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiBarChart2 /> Deployments Per Day
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.deploymentsPerDay}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <Tooltip contentStyle={{ background: 'var(--glass-bg)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiAlertTriangle /> Incident Trends
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.incidentTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <Tooltip contentStyle={{ background: 'var(--glass-bg)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Area type="monotone" dataKey="count" stroke="#ef4444" fill="#ef444420" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiCpu /> CPU Trend
          </h3>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#3b82f6' }}>{data.cpuTrend}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>req/s (5m rate)</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiHardDrive /> Memory
          </h3>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f59e0b' }}>{data.memTrend} MB</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>resident memory</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiAlertTriangle /> Error Rate
          </h3>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: data.errorRateTrend > 0 ? '#ef4444' : '#22c55e' }}>{(data.errorRateTrend * 100).toFixed(2)}%</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>5xx rate (5m)</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiActivity /> Infrastructure Health
          </h3>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: data.infrastructureHealthScore > 50 ? '#22c55e' : '#ef4444' }}>{data.infrastructureHealthScore}%</div>
          <div style={{ marginTop: '0.75rem' }}>
            {healthData.map(h => (
              <div key={h.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', fontSize: '0.8rem' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: h.status === 'Healthy' ? '#22c55e' : '#ef4444' }} />
                <span style={{ flex: 1, color: 'var(--text-secondary)' }}>{h.name}</span>
                <span className={`badge ${h.status === 'Healthy' ? 'success' : 'danger'}`} style={{ fontSize: '0.65rem' }}>{h.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Top Failed Deployments</h3>
          {data.topFailedDeployments.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No failed deployments</p>
          ) : (
            <table style={{ width: '100%', fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', color: 'var(--text-secondary)', paddingBottom: '0.5rem' }}>Repository</th>
                  <th style={{ textAlign: 'right', color: 'var(--text-secondary)', paddingBottom: '0.5rem' }}>Count</th>
                </tr>
              </thead>
              <tbody>
                {data.topFailedDeployments.map((d, i) => (
                  <tr key={i}>
                    <td style={{ padding: '0.25rem 0', fontWeight: 600 }}>{d.repository}</td>
                    <td style={{ textAlign: 'right', color: '#ef4444' }}>{d.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Top Active Repositories</h3>
          {data.topActiveRepositories.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No deployments yet</p>
          ) : (
            <table style={{ width: '100%', fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', color: 'var(--text-secondary)', paddingBottom: '0.5rem' }}>Repository</th>
                  <th style={{ textAlign: 'right', color: 'var(--text-secondary)', paddingBottom: '0.5rem' }}>Deployments</th>
                </tr>
              </thead>
              <tbody>
                {data.topActiveRepositories.map((d, i) => (
                  <tr key={i}>
                    <td style={{ padding: '0.25rem 0', fontWeight: 600 }}>{d.repository}</td>
                    <td style={{ textAlign: 'right', color: '#3b82f6' }}>{d.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
