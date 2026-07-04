import { FiTerminal } from 'react-icons/fi';

export function LogViewer({ logs = [], title = 'Live Logs' }) {
  return (
    <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: '1.25rem 1.5rem', background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <FiTerminal /> <h3 style={{ margin: 0 }}>{title}</h3>
      </div>
      <div className="terminal-window" style={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
        {logs.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Waiting for logs...</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className={`terminal-line ${log.includes('[ERROR]') ? 'terminal-error' : log.includes('[WARN]') ? 'terminal-warn' : 'terminal-info'}`}>
              <span style={{ color: '#64748b' }}>[{new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })}]</span> {log}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
