import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import AdminDashboard from './AdminDashboard';
import EmployeeDashboard from './EmployeeDashboard';
import TeamDashboard from './TeamDashboard';
import Spinner from '../components/common/Spinner';
import { getTeamDashboardMetadata } from '../services/api';
import { ClockIcon, ShieldCheckIcon, UserIcon, UsersIcon } from '../components/common/Icons';

export default function Dashboard() {
  const { user, isAdmin } = useAuth();
  const [viewMode, setViewMode] = useState(isAdmin ? 'admin' : 'employee');
  const [isSupervisor, setIsSupervisor] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAdmin) {
      getTeamDashboardMetadata()
        .then((res) => {
          if (res.data.is_supervisor) {
            setIsSupervisor(true);
            setViewMode('team');
          }
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [isAdmin]);

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
            Role: <span style={{ color: 'var(--accent-light)', fontWeight: 700 }}>{user?.is_line_manager ? 'Line Manager' : user?.role}</span> · Employee ID: <span style={{ fontWeight: 600 }}>{user?.employee_id}</span>
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

  if (loading) return <Spinner />;

  if (!isAdmin && !isSupervisor) {
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
      
      {/* View Switcher */}
      <div className="dashboard-view-switcher" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16, gap: 8 }}>
        {isAdmin && (
          <>
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
          </>
        )}
        
        {!isAdmin && isSupervisor && (
          <>
            <button 
              className={`btn ${viewMode === 'team' ? 'btn-primary' : 'btn-secondary'}`} 
              onClick={() => setViewMode('team')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <UsersIcon /> Team Dashboard
            </button>
            <button 
              className={`btn ${viewMode === 'employee' ? 'btn-primary' : 'btn-secondary'}`} 
              onClick={() => setViewMode('employee')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <UserIcon /> My Employee View
            </button>
          </>
        )}
      </div>

      {/* Renders based on active view mode */}
      {viewMode === 'admin' && <AdminDashboard />}
      {viewMode === 'team' && <TeamDashboard />}
      {viewMode === 'employee' && <EmployeeDashboard />}
    </div>
  );
}
