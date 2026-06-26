import { StrictMode, Component } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0b0f19', color: '#f8fafc', flexDirection: 'column', gap: '1rem', padding: '2rem' }}>
          <h1 style={{ fontSize: '2rem', margin: 0 }}>Something went wrong</h1>
          <p style={{ color: '#94a3b8' }}>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()} style={{ padding: '0.75rem 1.5rem', background: '#3b82f6', border: 'none', borderRadius: '10px', color: '#fff', cursor: 'pointer', fontWeight: 600 }}>
            Reload Page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
