import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiLayers, FiUser, FiCheck, FiAlertCircle, FiArrowRight } from 'react-icons/fi';
import { login, register } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';

export default function Login() {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const { saveAuth } = useAuth();

  const switchMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
    setError('');
    setSuccess(false);
  };

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
        setError(err.response?.data?.msg || 'Invalid credentials');
      } else if (!err.response) {
        setError('Cannot connect to server. Please ensure the backend is running.');
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim() || !email.trim() || !regUsername.trim() || !regPassword.trim() || !confirmPassword.trim()) {
      setError('All fields are required');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address');
      return;
    }

    if (regPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (regPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const data = await register({
        name: name.trim(),
        email: email.trim(),
        username: regUsername.trim(),
        password: regPassword,
      });
      setSuccess(true);
      setTimeout(() => {
        saveAuth(data.access_token, data.user);
        navigate('/');
      }, 1200);
    } catch (err) {
      if (err.response?.data?.msg) {
        setError(err.response.data.msg);
      } else if (!err.response) {
        setError('Cannot connect to server. Please ensure the backend is running.');
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const containerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    width: '100vw',
    padding: '1rem',
  };

  const cardStyle = {
    width: '100%',
    maxWidth: '440px',
    padding: '2.5rem',
    position: 'relative',
  };

  const toggleRowStyle = {
    display: 'flex',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '12px',
    padding: '3px',
    marginBottom: '2rem',
    border: '1px solid rgba(255, 255, 255, 0.04)',
  };

  const toggleBtnStyle = (isActive) => ({
    flex: 1,
    padding: '0.6rem 1rem',
    border: 'none',
    borderRadius: '10px',
    fontFamily: 'inherit',
    fontSize: '0.85rem',
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
    background: isActive
      ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(34, 211, 238, 0.1))'
      : 'transparent',
    color: isActive ? '#e2e8f0' : '#64748b',
    boxShadow: isActive
      ? '0 4px 20px rgba(139, 92, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.06)'
      : 'none',
  });

  const logoContainerStyle = {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '1rem',
  };

  const logoStyle = {
    width: '52px',
    height: '52px',
    borderRadius: '16px',
    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(34, 211, 238, 0.1))',
    border: '1px solid rgba(139, 92, 246, 0.15)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.5rem',
    color: '#a78bfa',
    boxShadow: '0 0 30px rgba(139, 92, 246, 0.08)',
  };

  const headingStyle = {
    textAlign: 'center',
    marginBottom: '0.5rem',
    fontSize: '1.5rem',
    fontWeight: 800,
    letterSpacing: '-0.02em',
  };

  const subtitleStyle = {
    textAlign: 'center',
    color: '#64748b',
    fontSize: '0.85rem',
    marginBottom: '1.75rem',
  };

  const errorStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    justifyContent: 'center',
    padding: '0.6rem 1rem',
    marginBottom: '1.25rem',
    borderRadius: '10px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.15)',
    color: '#f87171',
    fontSize: '0.82rem',
    fontWeight: 600,
  };

  const successStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.75rem',
    justifyContent: 'center',
    padding: '1.5rem',
    marginBottom: '1.25rem',
    borderRadius: '12px',
    background: 'rgba(16, 185, 129, 0.08)',
    border: '1px solid rgba(16, 185, 129, 0.15)',
    color: '#34d399',
    fontSize: '0.9rem',
    fontWeight: 600,
    animation: 'fadeIn 0.5s ease',
  };

  const linkStyle = {
    textAlign: 'center',
    marginTop: '1.25rem',
    fontSize: '0.82rem',
    color: '#64748b',
  };

  const linkBtnStyle = {
    background: 'none',
    border: 'none',
    color: '#a78bfa',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
    fontSize: '0.82rem',
    padding: '0',
    transition: 'color 0.2s',
  };

  const spinnerStyle = {
    width: '18px',
    height: '18px',
    border: '2px solid rgba(255,255,255,0.2)',
    borderTop: '2px solid #e2e8f0',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
    display: 'inline-block',
  };

  return (
    <div style={containerStyle}>
      <div className="glass-panel" style={cardStyle}>
        <div style={logoContainerStyle}>
          <div style={logoStyle}>
            <FiLayers />
          </div>
        </div>

        <div style={toggleRowStyle}>
          <button
            style={toggleBtnStyle(mode === 'login')}
            onClick={() => mode !== 'login' && switchMode()}
          >
            Sign In
          </button>
          <button
            style={toggleBtnStyle(mode === 'signup')}
            onClick={() => mode !== 'signup' && switchMode()}
          >
            Create Account
          </button>
        </div>

        {mode === 'login' && (
          <>
            <h2 style={headingStyle}>Welcome to DevFlow</h2>
            <p style={subtitleStyle}>Sign in to your account to continue</p>

            {error && (
              <div style={errorStyle}>
                <FiAlertCircle size={14} />
                {error}
              </div>
            )}

            <form onSubmit={handleLogin}>
              <div className="input-group">
                <label>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                />
              </div>
              <div className="input-group">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: '0.5rem' }}
                disabled={loading}
              >
                {loading ? (
                  <><span style={spinnerStyle} /> Signing in...</>
                ) : (
                  <><FiArrowRight size={16} /> Sign In to Console</>
                )}
              </button>
            </form>

            <div style={linkStyle}>
              New to DevFlow?{' '}
              <button style={linkBtnStyle} onClick={() => { setMode('signup'); setError(''); }}>
                Create Account
              </button>
            </div>
          </>
        )}

        {mode === 'signup' && (
          <>
            <h2 style={headingStyle}>Create Account</h2>
            <p style={subtitleStyle}>Join DevFlow and start managing your DevOps pipeline</p>

            {success && (
              <div style={successStyle}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem',
                }}>
                  <FiCheck size={24} />
                </div>
                Account created successfully! Redirecting...
              </div>
            )}

            {error && !success && (
              <div style={errorStyle}>
                <FiAlertCircle size={14} />
                {error}
              </div>
            )}

            <form onSubmit={handleRegister} style={success ? { display: 'none' } : {}}>
              <div className="input-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                />
              </div>
              <div className="input-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="john@example.com"
                  required
                />
              </div>
              <div className="input-group">
                <label>Username</label>
                <input
                  type="text"
                  value={regUsername}
                  onChange={e => setRegUsername(e.target.value)}
                  placeholder="johndoe"
                  required
                />
              </div>
              <div className="input-group">
                <label>Password</label>
                <input
                  type="password"
                  value={regPassword}
                  onChange={e => setRegPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                />
              </div>
              <div className="input-group">
                <label>Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Repeat your password"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: '0.5rem' }}
                disabled={loading}
              >
                {loading ? (
                  <><span style={spinnerStyle} /> Creating account...</>
                ) : (
                  <><FiUser size={16} /> Create Account</>
                )}
              </button>
            </form>

            <div style={linkStyle}>
              Already have an account?{' '}
              <button style={linkBtnStyle} onClick={() => { setMode('login'); setError(''); }}>
                Sign In
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
