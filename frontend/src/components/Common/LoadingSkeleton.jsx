export function LoadingSkeleton({ variant = 'text', count = 1, height, width }) {
  const items = Array.from({ length: count });
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {items.map((_, i) => (
        <div
          key={i}
          className={`skeleton skeleton-${variant}`}
          style={{
            ...(height ? { height } : {}),
            ...(width ? { width } : {}),
          }}
        />
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="glass-panel" style={{ padding: '1.5rem' }}>
      <div className="skeleton skeleton-title" style={{ marginBottom: '1rem' }} />
      <div className="skeleton skeleton-text" style={{ width: '60%' }} />
      <div className="skeleton skeleton-text" style={{ width: '40%', marginTop: '0.5rem' }} />
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      <div style={{ display: 'flex', gap: '1rem', padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)' }}>
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="skeleton skeleton-text" style={{ flex: 1 }} />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} style={{ display: 'flex', gap: '1rem', padding: '0.75rem 1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="skeleton skeleton-text" style={{ flex: 1 }} />
          ))}
        </div>
      ))}
    </div>
  );
}
