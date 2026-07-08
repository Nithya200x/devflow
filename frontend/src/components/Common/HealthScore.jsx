import { useState } from 'react';
import { FiArrowUp, FiArrowDown, FiMinus, FiInfo, FiRefreshCw } from 'react-icons/fi';

const WEIGHT_LABELS = {
  github: 'GitHub',
  cicd: 'CI/CD',
  deployment: 'Deployment',
  infrastructure: 'Infrastructure',
  monitoring: 'Monitoring',
  activity: 'Activity',
  incidents: 'Incidents',
};

function timeAgo(iso) {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

function TrendIcon({ trend }) {
  if (trend === 'improving') return <FiArrowUp size={14} style={{ color: 'var(--success-color)' }} />;
  if (trend === 'degrading') return <FiArrowDown size={14} style={{ color: 'var(--danger-color)' }} />;
  return <FiMinus size={14} style={{ color: 'var(--text-muted)' }} />;
}

export default function HealthScore({
  score = 0,
  trend = 'stable',
  color = '#6b7280',
  label = 'Unknown',
  breakdown,
  weights,
  calculatedAt,
  size = 'md',
  showBreakdown = true,
  onRefresh,
}) {
  const [expanded, setExpanded] = useState(false);
  const isSmall = size === 'sm';
  const isLarge = size === 'lg';
  const ringSize = isSmall ? 80 : isLarge ? 180 : 140;
  const strokeWidth = isSmall ? 4 : isLarge ? 8 : 6;
  const r = (ringSize - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(score, 100) / 100) * circ;
  const fontSize = isSmall ? '0.85rem' : isLarge ? '2.25rem' : '1.75rem';

  return (
    <div className={`health-score ${isSmall ? 'health-score-sm' : ''}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div className="score-ring" style={{ width: ringSize, height: ringSize }}>
          <svg width={ringSize} height={ringSize} viewBox={`0 0 ${ringSize} ${ringSize}`}>
            <circle cx={ringSize / 2} cy={ringSize / 2} r={r}
              fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={strokeWidth} />
            <circle cx={ringSize / 2} cy={ringSize / 2} r={r}
              fill="none" stroke={color} strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={circ}
              strokeDashoffset={offset}
              style={{ transition: 'stroke-dashoffset 1.5s ease', filter: `drop-shadow(0 0 4px ${color})` }} />
          </svg>
          <div className="score-label">
            <div className="score-value" style={{ color, fontSize }}>
              {score}{!isSmall && <span style={{ fontSize: '0.5em', fontWeight: 400 }}>%</span>}
            </div>
            {!isSmall && (
              <div className="score-text" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                <TrendIcon trend={trend} />
                {label}
              </div>
            )}
          </div>
        </div>

        {!isSmall && (
          <div style={{ flex: 1, minWidth: 0 }}>
            {calculatedAt && (
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Updated {timeAgo(calculatedAt)}
              </div>
            )}
            {onRefresh && (
              <button className="btn btn-ghost btn-sm" onClick={onRefresh} title="Refresh score"
                style={{ padding: '0.2rem 0.4rem', float: 'right' }}>
                <FiRefreshCw size={12} />
              </button>
            )}
            {showBreakdown && breakdown && (
              <>
                <button className="btn btn-ghost btn-sm"
                  onClick={() => setExpanded(!expanded)}
                  style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <FiInfo size={12} />
                  {expanded ? 'Hide Details' : 'Show Details'}
                </button>
                {expanded && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
                    {Object.entries(breakdown).map(([key, val]) => {
                      const w = weights?.[key] || 100;
                      return (
                        <div key={key}
                          style={{ display: 'flex', justifyContent: 'space-between', padding: '0.15rem 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>{WEIGHT_LABELS[key] || key}</span>
                          <span style={{ color: val >= w ? 'var(--success-color)' : val > 0 ? 'var(--warning-color)' : 'var(--text-muted)' }}>
                            {val}/{w}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export { WEIGHT_LABELS };
