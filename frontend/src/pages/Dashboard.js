import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import AdminDashboard from './AdminDashboard';
import EmployeeDashboard from './EmployeeDashboard';
import { ClockIcon, ShieldCheckIcon, UserIcon } from '../components/common/Icons';

export default function Dashboard() {
  const { user, isAdmin } = useAuth();
  const [viewMode, setViewMode] = useState('admin');

  // Format current date/time on render
  const getFormattedDateTime = () => {
    return new Date().toLocaleString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const welcomeBanner = (
    <div className="card" style={{ marginBottom: 24, padding: '20px 24px', background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            Welcome back, {user?.name}!
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: 4, marginBottom: 0, fontSize: 13 }}>
            Role: <span style={{ color: 'var(--accent-light)', fontWeight: 700 }}>{user?.role}</span> · Employee ID: <span style={{ fontWeight: 600 }}>{user?.employee_id}</span>
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <p style={{ color: 'var(--text-muted)', fontSize: 10, margin: 0, fontWeight: 700, letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: 4 }}>
            <ClockIcon style={{ width: 12, height: 12 }} /> CURRENT SYSTEM TIME
          </p>
          <p style={{ color: 'var(--text-primary)', fontSize: 15, fontWeight: 700, marginTop: 4, margin: 0 }}>
            {getFormattedDateTime()}
          </p>
        </div>
      </div>
    </div>
  );

  if (!isAdmin) {
    return (
      <div className="fade-in">
        {welcomeBanner}
        <EmployeeDashboard />
      </div>
    );
  }

  return (
    <div className="fade-in">
      {welcomeBanner}
      <div className="dashboard-view-switcher" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16, gap: 8 }}>
        <button 
          className={`btn ${viewMode === 'admin' ? 'btn-primary' : 'btn-secondary'}`} 
          onClick={() => setViewMode('admin')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <ShieldCheckIcon /> Admin Dashboard
        </button>
        <button 
          className={`btn ${viewMode === 'employee' ? 'btn-primary' : 'btn-secondary'}`} 
          onClick={() => setViewMode('employee')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <UserIcon /> My Employee View
        </button>
      </div>
      {viewMode === 'admin' ? <AdminDashboard /> : <EmployeeDashboard />}
    </div>
  );
}
