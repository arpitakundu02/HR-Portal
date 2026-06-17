/**
 * pages/TeamDashboard.js
 * Supervisor Team Dashboard view: scoped KPIs, timesheets, meetings, and Recharts charts.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import StatCard from '../components/common/StatCard';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { getTeamDashboardStats } from '../services/api';
import { useToast } from '../components/common/Toast';
import {
  UsersIcon, DocumentTextIcon, ClipboardCheckIcon, InboxIcon
} from '../components/common/Icons';

export default function TeamDashboard() {
  const navigate = useNavigate();
  const toast = useToast();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTeamDashboardStats();
      setStats(res.data);
    } catch (err) {
      toast.error('Failed to load team dashboard stats.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <Spinner />;
  if (!stats) return <p style={{ textAlign: 'center', padding: 24 }}>Failed to load data.</p>;

  // Data for Charts
  const attendanceData = [
    { name: 'Present', value: stats.present_today, color: '#10b981' },
    { name: 'Absent', value: stats.absent_today, color: '#f43f5e' },
    { name: 'On Leave', value: stats.on_leave_today, color: '#f59e0b' }
  ].filter(d => d.value > 0);

  const taskData = [
    { name: 'Open (Pending/In Progress)', value: stats.pending_tasks, color: '#6366f1' },
    { name: 'Completed', value: stats.completed_tasks, color: '#10b981' }
  ].filter(d => d.value > 0);

  return (
    <div className="fade-in">
      {/* Quick Actions / Navigation */}
      <div className="card" style={{ marginBottom: 24, padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Team Management Actions</h3>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>Quickly access detailed logs for your direct reports.</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-secondary" onClick={() => navigate('/attendance')}>
            📅 Team Attendance
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/leaves')}>
            🌴 Team Leaves
          </button>
        </div>
      </div>

      {/* Team KPIs */}
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <StatCard icon={<UsersIcon />} value={stats.present_today} label="Team Present Today" color="#10b981" />
        <StatCard icon={<UsersIcon />} value={stats.absent_today} label="Team Absent Today" color="#f43f5e" />
        <StatCard icon={<DocumentTextIcon />} value={stats.on_leave_today} label="Team On Leave Today" color="#f59e0b" />
        <StatCard icon={<DocumentTextIcon />} value={stats.pending_approvals} label="Pending Approvals" color="#f59e0b" />
        <StatCard icon={<ClipboardCheckIcon />} value={stats.pending_tasks} label="Pending Team Tasks" color="#6366f1" />
        <StatCard icon={<ClipboardCheckIcon />} value={stats.completed_tasks} label="Completed Team Tasks" color="#10b981" />
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Attendance Distribution */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Team Attendance Status</h3></div>
          <div className="card-body" style={{ height: 280, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {attendanceData.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No attendance logs today</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={attendanceData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                    {attendanceData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value} employee(s)`, 'Count']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Task Progress */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Team Task Status</h3></div>
          <div className="card-body" style={{ height: 280, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {taskData.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No team tasks assigned</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={taskData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                    {taskData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value} task(s)`, 'Count']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Timesheets & Meetings Grid */}
      <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 24 }}>
        {/* Recent Timesheets */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Recent Team Timesheets</h3></div>
          <div className="card-body" style={{ padding: 0 }}>
            {stats.recent_timesheets.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                No recent timesheets submitted by direct reports.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Date</th>
                      <th>Task</th>
                      <th>Hours</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_timesheets.map((t) => (
                      <tr key={t.id}>
                        <td style={{ fontWeight: 600 }}>{t.employee_name}</td>
                        <td>{t.date}</td>
                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.task_name}</td>
                        <td>{t.hours_spent} hrs</td>
                        <td><Badge status={t.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Upcoming Team Meetings */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Upcoming Team Meetings</h3></div>
          <div className="card-body">
            {stats.upcoming_meetings.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                <InboxIcon style={{ width: 48, height: 48, marginBottom: 12, opacity: 0.5 }} />
                <p>No upcoming team meetings</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {stats.upcoming_meetings.map((m) => (
                  <div key={m.id} className="card" style={{ padding: 12, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>{m.title}</div>
                    <div style={{ display: 'flex', gap: 16, marginTop: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
                      <span>📅 {new Date(m.scheduled_at).toLocaleDateString()}</span>
                      <span>⏰ {new Date(m.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    {m.link && (
                      <a href={m.link} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginTop: 8, fontSize: 12, color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>
                        🔗 Join Meeting
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
