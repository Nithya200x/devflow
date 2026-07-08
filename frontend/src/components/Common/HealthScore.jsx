import { useState } from 'react';
import { FiChevronDown, FiChevronRight, FiArrowUp, FiArrowDown, FiMinus } from 'react-icons/fi';

const WEIGHT_LABELS = {
  github: 'GitHub',
  cicd: 'CI/CD',
  deployment: 'Deployment',
  infrastructure: 'Infrastructure',
  monitoring: 'Monitoring',
  activity: 'Activity',
  incidents: 'Incidents',
};

function TrendIcon({ trend }) {
  if (trend === 'improving') return <FiArrowUp size={14} style={{ color: 'var(--success-color)' }} />;
  if (trend === 'degrading') return <FiArrowDown size={14} style={{ color: 'var(--danger-color)' }} />;
  return <FiMinus size={14} style={{ color: 'var(--text-muted)' }} />;
}

const SIZE_CONFIG = {
  sm: { ring: 72, stroke: 5, fontSize: '0.95rem', labelSize: '0.6rem', showMeta: false },
  md: { ring: 120, stroke: 7, fontSize: '1.5rem', labelSize: '0.7rem', showMeta: true },
  lg: { ring: 160, stroke: 9, fontSize: '2rem', labelSize: '0.8rem', showMeta: true },
};

export default function HealthScore({
  score = 0,
  trend = 'stable',
  color = '#6b7280',
  label = 'Unknown',
  breakdown,
  weights,
  size = 'md',
  showBreakdown = true,
}) {
  const [expanded, setExpanded] = useState(false);
  const cfg = SIZE_CONFIG[size] || SIZE_CONFIG.md;
  const clamped = Math.max(0, Math.min(100, score));
  const r = (cfg.ring - cfg.stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (clamped / 100) * circ;

  return (
    <div className={`health-score health-score--${size}`}
      style={{ display: 'flex', alignItems: 'center', gap: cfg.showMeta ? '1rem' : '0' }}>
      <div className="score-ring" style={{ width: cfg.ring, height: cfg.ring }}>
        <svg width={cfg.ring} height={cfg.ring} viewBox={`0 0 ${cfg.ring} ${cfg.ring}`}
          style={{ transform: 'rotate(-90deg)', transformOrigin: 'center center' }}>
          <circle cx={cfg.ring / 2} cy={cfg.ring / 2} r={r}
            fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={cfg.stroke} />
          <circle cx={cfg.ring / 2} cy={cfg.ring / 2} r={r}
            fill="none" stroke={color} strokeWidth={cfg.stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{
              transition: 'stroke-dashoffset 1.2s ease',
              filter: `drop-shadow(0 0 6px ${color}40)`,
            }} />
        </svg>
        <div className="score-label">
          <div className="score-value" style={{ color, fontSize: cfg.fontSize }}>
            {clamped}%
          </div>
          {cfg.showMeta && (
            <div className="score-text" style={{ fontSize: cfg.labelSize, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
              <TrendIcon trend={trend} />
              {label}
            </div>
          )}
        </div>
      </div>

      {cfg.showMeta && showBreakdown && breakdown && (
        <div style={{ alignSelf: 'stretch', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '0.35rem' }}>
          <button className="btn btn-ghost btn-sm"
            onClick={() => setExpanded(v => !v)}
            style={{
              fontSize: '0.72rem', padding: '0.25rem 0.5rem',
              display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
              whiteSpace: 'nowrap',
            }}>
            {expanded ? <FiChevronDown size={12} /> : <FiChevronRight size={12} />}
            {expanded ? 'Hide Breakdown' : 'View Breakdown'}
          </button>
          {expanded && (
            <div style={{ fontSize: '0.72rem', minWidth: 140 }}>
              {Object.entries(breakdown).map(([key, val]) => {
                const w = weights?.[key] || 100;
                return (
                  <div key={key}
                    style={{ display: 'flex', justifyContent: 'space-between', padding: '0.15rem 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{WEIGHT_LABELS[key] || key}</span>
                    <span style={{
                      color: val >= w ? 'var(--success-color)' : val > 0 ? 'var(--warning-color)' : 'var(--text-muted)',
                      fontFamily: 'var(--mono-font)', fontSize: '0.68rem',
                    }}>
                      {val}/{w}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export { WEIGHT_LABELS };
