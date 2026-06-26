import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiLayers } from 'react-icons/fi';
import { login } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';

export default function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { saveAuth } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Username and password are required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await login(username, password);
      saveAuth(data.access_token, data.user);
      navigate('/');
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Invalid credentials');
      } else if (!err.response) {
        setError('Cannot connect to server. Please ensure the backend is running.');
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', width: '100vw' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="sidebar-logo" style={{ width: '48px', height: '48px', fontSize: '1.5rem' }}>
            <FiLayers />
          </div>
        </div>
        <h2 style={{ textAlign: 'center', marginBottom: '2rem', fontSize: '1.75rem' }}>Welcome to DevFlow</h2>
        {error && <div className="badge danger" style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In to Console'}
          </button>
        </form>
      </div>
    </div>
  );
}
