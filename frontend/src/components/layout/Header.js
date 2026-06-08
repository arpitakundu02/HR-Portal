/**
 * components/layout/Header.js
 * Fixed top header bar with page title and quick actions.
 */
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';

const PAGE_TITLES = {
  '/dashboard':   { title: 'Dashboard',           subtitle: 'Overview and key metrics' },
  '/employees':   { title: 'Employee Management', subtitle: 'View, add, edit and manage employees' },
  '/departments': { title: 'Departments',          subtitle: 'Manage company departments' },
  '/leaves':      { title: 'Leave Management',     subtitle: 'Apply, approve, and track leave requests' },
  '/attendance':  { title: 'Attendance',           subtitle: 'Check-in, check-out and view history' },
  '/tasks':       { title: 'Tasks',                subtitle: 'Assigned work and project tracking' },
  '/meetings':    { title: 'Meetings',             subtitle: 'Scheduled and upcoming meetings' },
  '/profile':     { title: 'My Profile',           subtitle: 'Personal information and settings' },
  '/settings':    { title: 'Admin Settings',      subtitle: 'Configure office geofencing coordinates and policies' },
};

export default function Header() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const meta = PAGE_TITLES[pathname] || { title: 'HR Portal', subtitle: '' };

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  return (
    <header className="header">
      <div className="header-title">
        <h1>{meta.title}</h1>
        {meta.subtitle && <p>{meta.subtitle}</p>}
      </div>

      <div className="header-actions">
        {/* Theme Toggle Button */}
        <button
          className="header-btn"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          style={{ marginRight: 4 }}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>

        {/* Role badge */}
        <span
          className={`badge ${user?.role === 'Admin' ? 'badge-admin' : 'badge-employee'}`}
          style={{ padding: '6px 14px' }}
        >
          {user?.role}
        </span>

        {/* Profile shortcut */}
        <button
          className="header-btn"
          onClick={() => navigate('/profile')}
          title="My Profile"
          style={{
            width: 38, height: 38, borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--accent), #8b5cf6)',
            color: 'white', fontWeight: 700, fontSize: 14, border: 'none',
          }}
        >
          {initials}
        </button>
      </div>
    </header>
  );
}
