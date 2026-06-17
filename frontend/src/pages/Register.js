/**
 * pages/Register.js
 * Premium SaaS split-screen employee self-registration.
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { registerEmployee } from '../services/api';
import { useToast } from '../components/common/Toast';
import { EyeIcon, EyeOffIcon, BuildingIcon, SunIcon, MoonIcon, SparklesIcon, UsersIcon, ClockIcon, CalendarIcon, ChartBarIcon, ShieldCheckIcon, UserIcon } from '../components/common/Icons';

export default function Register() {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const toast = useToast();

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    fathers_name: '',
    dob: '',
    blood_group: '',
    address: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await registerEmployee({
        name: form.name,
        email: form.email,
        password: form.password,
        fathers_name: form.fathers_name || null,
        dob: form.dob || null,
        blood_group: form.blood_group || null,
        address: form.address || null
      });
      toast.success('Registration request submitted successfully! Pending admin approval.');
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit registration request.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page fade-in role-theme-employee">
      {/* Floating particles background */}
      <div className="floating-particles">
        <div className="bubble" style={{ width: 80, height: 80, left: '10%', animationDelay: '0s', animationDuration: '18s' }}></div>
        <div className="bubble" style={{ width: 60, height: 60, left: '30%', animationDelay: '2s', animationDuration: '22s' }}></div>
        <div className="bubble" style={{ width: 100, height: 100, left: '55%', animationDelay: '1s', animationDuration: '25s' }}></div>
        <div className="bubble" style={{ width: 70, height: 70, left: '80%', animationDelay: '4s', animationDuration: '15s' }}></div>
      </div>

      {/* LEFT PANEL: Branding & Visuals */}
      <div className="login-left-panel">
        <div className="landing-top-bar">
          <div className="landing-logo">
            <div className="landing-logo-icon">
              <BuildingIcon style={{ width: 24, height: 24 }} />
            </div>
            <span className="landing-logo-text">HR Portal</span>
          </div>
          <button 
            type="button" 
            className="theme-switch-btn" 
            onClick={toggleTheme}
            title={`Toggle ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
          >
            {theme === 'dark' ? <SunIcon style={{ width: 16, height: 16 }} /> : <MoonIcon style={{ width: 16, height: 16 }} />}
          </button>
        </div>

        <div className="landing-hero">
          <div className="landing-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <SparklesIcon style={{ width: 14, height: 14 }} /> Self-Service Registration
          </div>
          <h2>Join the <span>HR Ecosystem</span> Today</h2>
          <p>
            Submit your details to register as an employee. An Administrator will review your submission, verify your profile, and activate your account.
          </p>
        </div>

        {/* Live Metrics Widget */}
        <div className="landing-stats-grid">
          <div className="landing-stat-card">
            <div className="landing-stat-icon">
              <UsersIcon style={{ width: 18, height: 18 }} />
            </div>
            <div className="landing-stat-info">
              <h4>Easy</h4>
              <p>Self Signup Process</p>
            </div>
          </div>
          <div className="landing-stat-card">
            <div className="landing-stat-icon">
              <ShieldCheckIcon style={{ width: 18, height: 18 }} />
            </div>
            <div className="landing-stat-info">
              <h4>Secure</h4>
              <p>Password Hashing</p>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 40, fontSize: 12, color: 'var(--text-muted)' }}>
          <span>© {new Date().getFullYear()} HR Portal Inc. All rights reserved.</span>
        </div>
      </div>

      {/* RIGHT PANEL: Form */}
      <div className="login-right-panel" style={{ padding: '20px 40px' }}>
        <div className="glass-auth-container fade-in" style={{ maxWidth: 500, width: '100%', padding: '30px 40px' }}>
          <h3 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>
            Create Account
          </h3>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
            Submit your application for review
          </p>

          <form onSubmit={handleSubmit}>
            {error && (
              <div className="alert alert-error" style={{ fontSize: 13, padding: '10px 12px', marginBottom: 16 }}>
                {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Full Name <span className="form-required">*</span></label>
              <input
                type="text"
                name="name"
                className="form-control"
                required
                placeholder="John Doe"
                value={form.name}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Email Address <span className="form-required">*</span></label>
              <input
                type="email"
                name="email"
                className="form-control"
                required
                placeholder="john.doe@company.com"
                value={form.email}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Password <span className="form-required">*</span></label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="form-control"
                    required
                    placeholder="••••••••"
                    value={form.password}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(p => !p)}
                  >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm Password <span className="form-required">*</span></label>
                <div className="password-input-wrapper">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    className="form-control"
                    required
                    placeholder="••••••••"
                    value={form.confirmPassword}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(p => !p)}
                  >
                    {showConfirmPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Father's Name</label>
                <input
                  type="text"
                  name="fathers_name"
                  className="form-control"
                  placeholder="Robert Doe"
                  value={form.fathers_name}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Date of Birth</label>
                <input
                  type="date"
                  name="dob"
                  className="form-control"
                  value={form.dob}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Blood Group</label>
              <select
                name="blood_group"
                className="form-control"
                value={form.blood_group}
                onChange={handleChange}
              >
                <option value="">Select Blood Group</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Contact Address</label>
              <textarea
                name="address"
                className="form-control"
                placeholder="123 Main St, Springfield"
                value={form.address}
                onChange={handleChange}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 10, justifyContent: 'center' }}
              disabled={loading}
            >
              {loading ? 'Submitting request…' : 'Submit Registration Request'}
            </button>

            <div style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
              Already have an account? <Link to="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>Login here</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
