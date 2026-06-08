/**
 * pages/Login.js
 * Redesigned premium SaaS split-screen authentication and landing experience.
 */
import { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { loginUser } from '../services/api';
import { useToast } from '../components/common/Toast';

export default function Login() {
  const { isAuthenticated, login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const toast = useToast();

  // State machine: 'role-select' or 'auth-flow'
  const [step, setStep] = useState('role-select');
  // Selected portal: 'Admin' or 'Employee'
  const [selectedRole, setSelectedRole] = useState('Employee');


  // Login Form
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');

  // Clear error when portal is changed
  useEffect(() => {
    setLoginError('');
  }, [selectedRole]);

  // Already logged in — redirect
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  // Form input changes
  const handleLoginChange = (e) => {
    setLoginForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };



  // Submit Login
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    try {
      const { data } = await loginUser({ ...loginForm, role: selectedRole });
      login(data.token, data.user);
      toast.success(`Welcome back, ${data.user.name}!`);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setLoginError(err.response?.data?.error || 'Login failed. Please verify your credentials.');
    } finally {
      setLoginLoading(false);
    }
  };



  return (
    <div className={`login-page fade-in role-theme-${selectedRole.toLowerCase()}`}>
      
      {/* Floating particles animation in background */}
      <div className="floating-particles">
        <div className="bubble" style={{ width: 80, height: 80, left: '10%', animationDelay: '0s', animationDuration: '18s' }}></div>
        <div className="bubble" style={{ width: 60, height: 60, left: '30%', animationDelay: '2s', animationDuration: '22s' }}></div>
        <div className="bubble" style={{ width: 100, height: 100, left: '55%', animationDelay: '1s', animationDuration: '25s' }}></div>
        <div className="bubble" style={{ width: 70, height: 70, left: '80%', animationDelay: '4s', animationDuration: '15s' }}></div>
      </div>

      {/* LEFT PANEL: Branding & Visuals */}
      <div className="login-left-panel">
        
        {/* Top Header Logo */}
        <div className="landing-top-bar">
          <div className="landing-logo">
            <div className="landing-logo-icon">🏛️</div>
            <span className="landing-logo-text">HR Portal</span>
          </div>
          <button 
            type="button" 
            className="theme-switch-btn" 
            onClick={toggleTheme}
            title={`Toggle ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>

        {/* Hero Copy */}
        <div className="landing-hero">
          <div className="landing-badge">✨ Next-Generation HR Solutions</div>
          <h2>Smart <span>HR Management</span> System</h2>
          <p>
            An integrated SaaS system designed to manage employees, tracking, leaves, meetings, and team workflows efficiently. Experiencing a smooth, premium employee management ecosystem.
          </p>
        </div>

        {/* SVG Illustration */}
        <div style={{ display: 'flex', justifyContent: 'center', margin: '10px 0' }}>
          <svg width="320" height="200" viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ maxWidth: '100%' }}>
            <rect x="10" y="40" width="300" height="150" rx="16" fill="var(--bg-surface)" stroke="var(--border)" strokeWidth="2" />
            <rect x="25" y="55" width="270" height="24" rx="6" fill="var(--bg-elevated)" />
            <circle cx="40" cy="67" r="5" fill="#f43f5e" />
            <circle cx="55" cy="67" r="5" fill="#f59e0b" />
            <circle cx="70" cy="67" r="5" fill="#10b981" />
            
            {/* Mock stats card inside vector */}
            <rect x="30" y="100" width="110" height="70" rx="10" fill="rgba(99, 102, 241, 0.08)" stroke="rgba(99, 102, 241, 0.2)" />
            <line x1="45" y1="120" x2="95" y2="120" stroke="var(--text-secondary)" strokeWidth="4" strokeLinecap="round" />
            <line x1="45" y1="135" x2="115" y2="135" stroke="var(--text-muted)" strokeWidth="3" strokeLinecap="round" />
            <line x1="45" y1="150" x2="75" y2="150" stroke="var(--accent)" strokeWidth="5" strokeLinecap="round" />

            {/* Another chart element */}
            <rect x="155" y="100" width="135" height="70" rx="10" fill="var(--bg-elevated)" stroke="var(--border)" />
            <path d="M170 150 L195 125 L220 140 L250 115 L275 130" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="250" cy="115" r="4" fill="var(--success)" />
          </svg>
        </div>

        {/* Live Metrics Widget */}
        <div className="landing-stats-grid">
          <div className="landing-stat-card">
            <div className="landing-stat-icon">👥</div>
            <div className="landing-stat-info">
              <h4>120+</h4>
              <p>Employees Managed</p>
            </div>
          </div>
          <div className="landing-stat-card">
            <div className="landing-stat-icon">⏱️</div>
            <div className="landing-stat-info">
              <h4>98.5%</h4>
              <p>Attendance Tracking</p>
            </div>
          </div>
          <div className="landing-stat-card">
            <div className="landing-stat-icon">📅</div>
            <div className="landing-stat-info">
              <h4>24h</h4>
              <p>Leave Requests SLA</p>
            </div>
          </div>
          <div className="landing-stat-card">
            <div className="landing-stat-icon">📈</div>
            <div className="landing-stat-info">
              <h4>A+</h4>
              <p>Performance Reviews</p>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div style={{ marginTop: 40, fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 16 }}>
          <span>© {new Date().getFullYear()} HR Portal Inc.</span>
          <span>Privacy Policy</span>
          <span>Terms of Service</span>
        </div>
      </div>

      {/* RIGHT PANEL: Auth Wizard */}
      <div className="login-right-panel">
        
        {step === 'role-select' ? (
          <div className="glass-auth-container fade-in">
            <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', textAlign: 'center' }}>
              Welcome to HR Portal
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', textAlign: 'center', marginTop: 6, marginBottom: 30 }}>
              Select your specific portal to proceed
            </p>

            <div className="role-cards-container">
              
              {/* Admin Card */}
              <div 
                className={`role-card ${selectedRole === 'Admin' ? 'admin-selected' : ''}`}
                onClick={() => setSelectedRole('Admin')}
              >
                <div className="role-card-icon">💼</div>
                <h3>Admin Portal</h3>
                <p>Company settings & management</p>
              </div>

              {/* Employee Card */}
              <div 
                className={`role-card ${selectedRole === 'Employee' ? 'employee-selected' : ''}`}
                onClick={() => setSelectedRole('Employee')}
              >
                <div className="role-card-icon">👤</div>
                <h3>Employee Portal</h3>
                <p>Personal profile & logs</p>
              </div>
            </div>

            <button
              type="button"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 32, justifyContent: 'center' }}
              onClick={() => setStep('auth-flow')}
            >
              Continue to {selectedRole} Portal →
            </button>
          </div>
        ) : (
          <div className="glass-auth-container fade-in">
            
            {/* Back Button */}
            <button 
              type="button" 
              className="auth-back-btn" 
              onClick={() => setStep('role-select')}
            >
              ← Back to role selection
            </button>

            <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>
              {selectedRole} Portal Access
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
              Secure authentication layer
            </p>

            {/* LOGIN FORM */}
            <form onSubmit={handleLoginSubmit}>
              {loginError && (
                <div className="alert alert-error" style={{ fontSize: 13, padding: '10px 12px' }}>
                  {loginError}
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="form-control"
                  required
                  placeholder={`e.g. name@company.com`}
                  value={loginForm.email}
                  onChange={handleLoginChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  className="form-control"
                  required
                  placeholder="••••••••"
                  value={loginForm.password}
                  onChange={handleLoginChange}
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-lg"
                style={{ width: '100%', marginTop: 16, justifyContent: 'center' }}
                disabled={loginLoading}
              >
                {loginLoading ? 'Authenticating…' : `Secure Login`}
              </button>
            </form>

          </div>
        )}

      </div>
    </div>
  );
}
