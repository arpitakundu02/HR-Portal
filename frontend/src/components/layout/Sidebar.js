/**
 * components/layout/Sidebar.js
 * Role-aware collapsible navigation sidebar.
 */
import { useState, useEffect, useCallback } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../common/Toast';
import { getNotificationsUnreadCount, getBadgeCounts } from '../../services/api';
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
  MegaphoneIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
} from '../common/Icons';

const ADMIN_NAV = [
  { label: 'Dashboard',    path: '/dashboard',   icon: ChartBarIcon },
  { label: 'Notices & Announcements', path: '/notifications', icon: MegaphoneIcon },
  { label: 'Policies & Handbook', path: '/policies', icon: DocumentTextIcon },
  { label: 'Employees',    path: '/employees',   icon: UsersIcon },
  { label: 'Departments',  path: '/departments', icon: BuildingIcon },
  { label: 'Registrations', path: '/admin/registrations', icon: ShieldCheckIcon },
  { label: 'Approvals',    path: '/approvals',   icon: ShieldCheckIcon },
  { label: 'Comp-Off',     path: '/comp-off',    icon: CalendarIcon },
  { label: 'Leaves',       path: '/leaves',      icon: CalendarIcon },
  { label: 'Attendance',   path: '/attendance',  icon: ClockIcon },
  { label: 'Tasks',        path: '/tasks',       icon: ClipboardCheckIcon },
  { label: 'Timesheets',   path: '/timesheets',  icon: ClipboardCheckIcon },
  { label: 'Org Chart',    path: '/org-chart',   icon: UserGroupIcon },
  { label: 'Contact Directory', path: '/directory', icon: UsersIcon },
  { label: 'Meetings',     path: '/meetings',    icon: UserGroupIcon },
  { label: 'Holidays',     path: '/holidays',    icon: CalendarIcon },
  { label: 'Work Transfers', path: '/work-transfers', icon: UsersIcon },
  { label: 'Settings',     path: '/settings',    icon: CogIcon },
];

const EMPLOYEE_NAV = [
  { label: 'Dashboard',    path: '/dashboard',   icon: ChartBarIcon },
  { label: 'Notices & Announcements', path: '/notifications', icon: MegaphoneIcon },
  { label: 'Policies & Handbook', path: '/policies', icon: DocumentTextIcon },
  { label: 'Employees',    path: '/employees',   icon: UsersIcon },
  { label: 'Approvals',    path: '/approvals',   icon: ShieldCheckIcon },
  { label: 'Comp-Off',     path: '/comp-off',    icon: CalendarIcon },
  { label: 'Leaves',       path: '/leaves',      icon: CalendarIcon },
  { label: 'Attendance',   path: '/attendance',  icon: ClockIcon },
  { label: 'Tasks',        path: '/tasks',       icon: ClipboardCheckIcon },
  { label: 'Timesheets',   path: '/timesheets',  icon: ClipboardCheckIcon },
  { label: 'Org Chart',    path: '/org-chart',   icon: UserGroupIcon },
  { label: 'Contact Directory', path: '/directory', icon: UsersIcon },
  { label: 'Meetings',     path: '/meetings',    icon: UserGroupIcon },
  { label: 'Holidays',     path: '/holidays',    icon: CalendarIcon },
  { label: 'Work Transfers', path: '/work-transfers', icon: UsersIcon },
];

export default function Sidebar() {
  const { user, isAdmin, logout } = useAuth();
  const toast   = useToast();
  const navigate = useNavigate();

  const [unreadCount, setUnreadCount] = useState(0);
  const [badgeCounts, setBadgeCounts] = useState({
    approvals: 0,
    leaves: 0,
    tasks: 0,
    meetings: 0,
    timesheets: 0,
    registrations: 0
  });

  const refreshCounts = useCallback(async () => {
    if (!user) return;
    try {
      const [notifRes, badgeRes] = await Promise.all([
        getNotificationsUnreadCount(),
        getBadgeCounts()
      ]);
      setUnreadCount(notifRes.data.unread_count || 0);
      setBadgeCounts(badgeRes.data || {
        approvals: 0,
        leaves: 0,
        tasks: 0,
        meetings: 0,
        timesheets: 0,
        registrations: 0
      });
    } catch (e) {
      // Silently ignore background refresh errors
    }
  }, [user]);

  useEffect(() => {
    refreshCounts();
    // Poll every 10 seconds for real-time badge updates
    const interval = setInterval(refreshCounts, 10000);
    return () => clearInterval(interval);
  }, [refreshCounts]);

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
          
          let badgeVal = 0;
          if (item.label === 'Notices & Announcements') {
            badgeVal = unreadCount;
          } else if (item.label === 'Approvals') {
            badgeVal = badgeCounts.approvals;
          } else if (item.label === 'Leaves') {
            badgeVal = badgeCounts.leaves;
          } else if (item.label === 'Tasks') {
            badgeVal = badgeCounts.tasks;
          } else if (item.label === 'Meetings') {
            badgeVal = badgeCounts.meetings;
          } else if (item.label === 'Timesheets') {
            badgeVal = badgeCounts.timesheets;
          } else if (item.label === 'Registrations') {
            badgeVal = badgeCounts.registrations;
          }

          const showBadge = badgeVal > 0;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon"><Icon /></span>
              <span className="nav-label">{item.label}</span>
              {showBadge && (
                <span className="sidebar-badge" style={{
                  marginLeft: 'auto',
                  backgroundColor: 'var(--accent)',
                  color: 'white',
                  borderRadius: '10px',
                  padding: '2px 8px',
                  fontSize: 11,
                  fontWeight: 'bold'
                }}>
                  {badgeVal}
                </span>
              )}
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
          {user?.photo_url ? (
            <img src={user.photo_url} alt={user.name} style={{ width: 36, height: 36, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border)' }} />
          ) : (
            <div className="sidebar-avatar">{initials}</div>
          )}
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.name || 'User'}</div>
            <div className="sidebar-user-role">{user?.is_line_manager ? 'Line Manager' : user?.role}</div>
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
