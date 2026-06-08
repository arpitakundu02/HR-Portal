/**
 * components/layout/Sidebar.js
 * Role-aware collapsible navigation sidebar.
 */
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../common/Toast';
import {
  ChartBarIcon,
  UsersIcon,
  BuildingIcon,
  CalendarIcon,
  ClockIcon,
  ClipboardCheckIcon,
  UserGroupIcon,
  CogIcon,
  AcademyIcon,
  UserIcon,
  LogoutIcon,
} from '../common/Icons';

const ADMIN_NAV = [
  { label: 'Dashboard',    path: '/dashboard',   icon: ChartBarIcon },
  { label: 'Employees',    path: '/employees',   icon: UsersIcon },
  { label: 'Departments',  path: '/departments', icon: BuildingIcon },
  { label: 'Leaves',       path: '/leaves',      icon: CalendarIcon },
  { label: 'Attendance',   path: '/attendance',  icon: ClockIcon },
  { label: 'Tasks',        path: '/tasks',       icon: ClipboardCheckIcon },
  { label: 'Meetings',     path: '/meetings',    icon: UserGroupIcon },
  { label: 'Settings',     path: '/settings',    icon: CogIcon },
];

const EMPLOYEE_NAV = [
  { label: 'Dashboard',    path: '/dashboard',   icon: ChartBarIcon },
  { label: 'Employees',    path: '/employees',   icon: UsersIcon },
  { label: 'Leaves',       path: '/leaves',      icon: CalendarIcon },
  { label: 'Attendance',   path: '/attendance',  icon: ClockIcon },
  { label: 'Tasks',        path: '/tasks',       icon: ClipboardCheckIcon },
  { label: 'Meetings',     path: '/meetings',    icon: UserGroupIcon },
];

export default function Sidebar() {
  const { user, isAdmin, logout } = useAuth();
  const toast   = useToast();
  const navigate = useNavigate();

  const navItems = isAdmin ? ADMIN_NAV : EMPLOYEE_NAV;

  const handleLogout = () => {
    logout();
    toast.info('Logged out successfully.');
    navigate('/login');
  };

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <AcademyIcon style={{ width: 24, height: 24 }} />
        </div>
        <div className="sidebar-logo-text">
          <strong>HR Portal</strong>
          <span>Management System</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Navigation</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon"><Icon /></span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          );
        })}

        <div className="sidebar-section-label" style={{ marginTop: 16 }}>Account</div>
        <NavLink
          to="/profile"
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon"><UserIcon /></span>
          <span className="nav-label">My Profile</span>
        </NavLink>
      </nav>

      {/* Footer: user info + logout */}
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.name || 'User'}</div>
            <div className="sidebar-user-role">{user?.role}</div>
          </div>
        </div>
        <button
          className="btn btn-ghost btn-sm"
          style={{ width: '100%', marginTop: 8, justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '8px' }}
          onClick={handleLogout}
        >
          <LogoutIcon /> <span className="nav-label">Logout</span>
        </button>
      </div>
    </aside>
  );
}
