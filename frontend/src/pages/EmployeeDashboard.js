/**
 * pages/EmployeeDashboard.js
 * Employee overview: leave balances, today's attendance, tasks, upcoming meetings.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import StatCard from '../components/common/StatCard';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { getLeaveBalances, getTodayStatus, getTasks, getMeetings } from '../services/api';
import { useToast } from '../components/common/Toast';
import { DocumentTextIcon, HomeIcon, ClipboardCheckIcon, UserGroupIcon, InboxIcon } from '../components/common/Icons';

export default function EmployeeDashboard() {
  const { user } = useAuth();
  const toast    = useToast();

  const [balances,   setBalances]   = useState([]);
  const [attendance, setAttendance] = useState(null);
  const [tasks,      setTasks]      = useState([]);
  const [meetings,   setMeetings]   = useState([]);
  const [loading,    setLoading]    = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [balRes, attRes, taskRes, meetRes] = await Promise.all([
          getLeaveBalances(),
          getTodayStatus(),
          getTasks({ status: 'Pending' }),
          getMeetings({ upcoming: true }),
        ]);
        setBalances(balRes.data);
        setAttendance(attRes.data);
        setTasks(taskRes.data.tasks || []);
        setMeetings(meetRes.data || []);
      } catch {
        toast.error('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line
  }, []);

  if (loading) return <Spinner />;

  const aplBalance = balances.find((b) => b.leave_type === 'APL');
  const wfhBalance = balances.find((b) => b.leave_type === 'WFH');

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="fade-in">
      {/* Greeting */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)' }}>
          {greeting()}, {user?.name?.split(' ')[0]} 👋
        </h2>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
          Here's what's happening with your account today.
        </p>
      </div>

      {/* Leave Balance Cards */}
      <div className="stats-grid">
        <StatCard icon={<DocumentTextIcon />} value={aplBalance?.remaining ?? '—'} label="APL Days Remaining"  color="#6366f1" />
        <StatCard icon={<HomeIcon />} value={wfhBalance?.remaining ?? '—'} label="WFH Days Remaining" color="#10b981" />
        <StatCard icon={<ClipboardCheckIcon />} value={tasks.length}                  label="Pending Tasks"       color="#f59e0b" />
        <StatCard icon={<UserGroupIcon />} value={meetings.length}               label="Upcoming Meetings"   color="#38bdf8" />
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Today's Attendance */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">⏱️ Today's Attendance</div>
          </div>
          {attendance && attendance.status !== 'not_checked_in' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="info-item" style={{ border: '1px solid var(--border)', borderRadius: 8, padding: '12px 16px' }}>
                <div className="info-label">Check-In Time</div>
                <div className="info-value" style={{ color: 'var(--success)', fontWeight: 700 }}>
                  {attendance.check_in ? new Date(attendance.check_in).toLocaleTimeString() : '—'}
                </div>
              </div>
              {attendance.check_out && (
                <div className="info-item" style={{ border: '1px solid var(--border)', borderRadius: 8, padding: '12px 16px' }}>
                  <div className="info-label">Check-Out Time</div>
                  <div className="info-value">{new Date(attendance.check_out).toLocaleTimeString()}</div>
                </div>
              )}
              {attendance.working_hours > 0 && (
                <div className="info-item" style={{ border: '1px solid var(--border)', borderRadius: 8, padding: '12px 16px' }}>
                  <div className="info-label">Working Hours</div>
                  <div className="info-value" style={{ color: 'var(--accent-light)', fontWeight: 700 }}>
                    {attendance.working_hours.toFixed(2)}h
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '30px 20px' }}>
              <div className="empty-state-icon">⏰</div>
              <h3>Not checked in yet</h3>
              <p>Go to Attendance to check in for today.</p>
            </div>
          )}
        </div>

        {/* Leave Balance Detail */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">📅 Leave Balance</div>
          </div>
          {balances.map((b) => (
            <div key={b.leave_type} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '14px 0', borderBottom: '1px solid var(--border)',
            }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{b.leave_type === 'APL' ? 'All Purpose Leave' : 'Work From Home'}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  Used: {b.used} / Allocated: {b.allocated}
                </div>
              </div>
              <div style={{
                fontSize: 22, fontWeight: 800,
                color: b.remaining < 0 ? 'var(--danger)' : b.remaining <= 3 ? 'var(--warning)' : 'var(--success)',
              }}>
                {b.remaining}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* My Pending Tasks */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div className="card-title">✅ My Pending Tasks</div>
        </div>
        {tasks.length === 0 ? (
          <div className="empty-state" style={{ padding: 30 }}>
            <div className="empty-state-icon">🎉</div>
            <h3>No pending tasks!</h3>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>Task</th><th>Assigned By</th><th>Due Date</th><th>Status</th></tr>
              </thead>
              <tbody>
                {tasks.slice(0, 5).map((t) => (
                  <tr key={t.id}>
                    <td style={{ fontWeight: 600 }}>{t.title}</td>
                    <td className="td-muted">{t.assigner_name}</td>
                    <td className="td-muted">{t.due_date || '—'}</td>
                    <td><Badge status={t.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upcoming Meetings */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">🤝 Upcoming Meetings</div>
        </div>
        {meetings.length === 0 ? (
          <div className="empty-state" style={{ padding: 30 }}>
            <div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div>
            <h3>No upcoming meetings</h3>
          </div>
        ) : (
          meetings.slice(0, 4).map((m) => (
            <div key={m.id} style={{
              display: 'flex', gap: 14, padding: '14px 0',
              borderBottom: '1px solid var(--border)',
            }}>
              <div style={{
                width: 44, height: 44, borderRadius: 10,
                background: 'var(--accent-glow)', display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 20, flexShrink: 0,
              }}>🤝</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{m.title}</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                  {new Date(m.scheduled_at).toLocaleString()} · {m.duration_minutes} min · {m.department_name}
                </div>
              </div>
              {m.link && (
                <a href={m.link} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">Join</a>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
