/**
 * components/layout/Header.js
 * Fixed top header bar with page title, theme toggle, and notification bell quick actions.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { 
  getNotifications, 
  getNotificationsUnreadCount, 
  markNotificationRead, 
  markAllNotificationsRead 
} from '../../services/api';

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

  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const meta = PAGE_TITLES[pathname] || { title: 'HR Portal', subtitle: '' };

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  const fetchUnreadCount = async () => {
    try {
      const res = await getNotificationsUnreadCount();
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  };

  const fetchRecentNotifications = async () => {
    try {
      const res = await getNotifications({ page: 1, per_page: 5 });
      setNotifications(res.data.notifications);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      fetchRecentNotifications();
      // Poll every 10 seconds for real-time badge count
      const interval = setInterval(() => {
        fetchUnreadCount();
        if (showDropdown) {
          fetchRecentNotifications();
        }
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [user, showDropdown]);

  // Click outside listener to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggleDropdown = () => {
    setShowDropdown(!showDropdown);
    if (!showDropdown) {
      fetchRecentNotifications();
    }
  };

  const handleMarkRead = async (id, e) => {
    e.stopPropagation();
    try {
      await markNotificationRead(id);
      fetchUnreadCount();
      fetchRecentNotifications();
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      fetchUnreadCount();
      fetchRecentNotifications();
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await markNotificationRead(notif.id);
        fetchUnreadCount();
        fetchRecentNotifications();
      } catch (err) {
        console.error('Failed to mark notification as read:', err);
      }
    }
    setShowDropdown(false);
    if (notif.action_url) {
      navigate(notif.action_url);
    }
  };

  return (
    <header className="header">
      <div className="header-title">
        <h1>{meta.title}</h1>
        {meta.subtitle && <p>{meta.subtitle}</p>}
      </div>

      <div className="header-actions">
        {/* Notification Bell Container */}
        <div className="notification-container" ref={dropdownRef}>
          <button
            className="header-btn"
            onClick={handleToggleDropdown}
            title="Notifications"
          >
            {/* Bell SVG */}
            <svg xmlns="http://www.w3.org/2000/svg" style={{ width: 20, height: 20 }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {unreadCount > 0 && (
              <span className="notification-badge">{unreadCount}</span>
            )}
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <div className="notification-dropdown">
              <div className="notification-dropdown-header">
                <span>Notifications</span>
                {unreadCount > 0 && (
                  <button onClick={handleMarkAllRead}>Mark all read</button>
                )}
              </div>
              <div className="notification-list">
                {notifications.length === 0 ? (
                  <div className="notification-empty">No notifications yet.</div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`notification-item ${!notif.is_read ? 'unread' : ''}`}
                      onClick={() => handleNotificationClick(notif)}
                    >
                      <div className="notification-item-title">
                        <span>{notif.title}</span>
                        {!notif.is_read && (
                          <span 
                            className="notification-unread-dot" 
                            title="Mark as read"
                            onClick={(e) => handleMarkRead(notif.id, e)}
                          />
                        )}
                      </div>
                      <div className="notification-item-content">{notif.content}</div>
                      <div className="notification-item-time">
                        {new Date(notif.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle Button */}
        <button
          className="header-btn"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>

        {/* Role badge */}
        <span
          className={`badge ${user?.role === 'Admin' ? 'badge-admin' : user?.is_line_manager ? 'badge-in-progress' : 'badge-employee'}`}
          style={{ padding: '6px 14px' }}
        >
          {user?.is_line_manager ? 'Line Manager' : user?.role}
        </span>

        {/* Profile shortcut */}
        <button
          className="header-btn"
          onClick={() => navigate('/profile')}
          title="My Profile"
          style={{
            width: 38, height: 38, borderRadius: '50%',
            background: user?.photo_url ? 'none' : 'linear-gradient(135deg, var(--accent), #8b5cf6)',
            color: 'white', fontWeight: 700, fontSize: 14, border: 'none',
            padding: 0, overflow: 'hidden'
          }}
        >
          {user?.photo_url ? (
            <img src={user.photo_url} alt={user.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            initials
          )}
        </button>
      </div>
    </header>
  );
}
