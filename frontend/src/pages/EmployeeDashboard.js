/**
 * pages/EmployeeDashboard.js
 * Employee overview: leave balances, today's attendance, tasks, upcoming meetings.
 */
import { useState, useEffect } from 'react';
import StatCard from '../components/common/StatCard';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import AnnouncementWidget from '../components/common/AnnouncementWidget';
import { getLeaveBalances, getTodayStatus, getTasks, getMeetings, getHolidays, getPoliciesStats } from '../services/api';
import { useToast } from '../components/common/Toast';
import { DocumentTextIcon, HomeIcon, ClipboardCheckIcon, UserGroupIcon, InboxIcon, ClockIcon, CalendarIcon, CheckIcon, UsersIcon } from '../components/common/Icons';

export default function EmployeeDashboard() {
  const toast    = useToast();

  const [balances,   setBalances]   = useState([]);
  const [attendance, setAttendance] = useState(null);
  const [tasks,      setTasks]      = useState([]);
  const [meetings,   setMeetings]   = useState([]);
  const [holidays,   setHolidays]   = useState([]);
  const [policyStats, setPolicyStats] = useState(null);
  const [loading,    setLoading]    = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [balRes, attRes, taskRes, meetRes, holRes, polRes] = await Promise.all([
          getLeaveBalances(),
          getTodayStatus(),
          getTasks({ status: 'Pending' }),
          getMeetings({ upcoming: true }),
          getHolidays({ upcoming: true, limit: 3 }),
          getPoliciesStats()
        ]);
        setBalances(balRes.data);
        setAttendance(attRes.data);
        setTasks(taskRes.data.tasks || []);
        setMeetings(meetRes.data || []);
        setHolidays(holRes.data || []);
        setPolicyStats(polRes.data);
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

  return (
    <div className="fade-in">

      {/* Leave Balance Cards */}
      <div className="stats-grid">
        <StatCard icon={<DocumentTextIcon />} value={aplBalance?.remaining ?? '—'} label="APL Days Remaining"  color="#6366f1" />
        <StatCard icon={<HomeIcon />} value={wfhBalance?.remaining ?? '—'} label="WFH Days Remaining" color="#10b981" />
        <StatCard icon={<ClipboardCheckIcon />} value={tasks.length}                  label="Pending Tasks"       color="#f59e0b" />
        <StatCard icon={<UserGroupIcon />} value={meetings.length}               label="Upcoming Meetings"   color="#38bdf8" />
      </div>

      <AnnouncementWidget />

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Today's Attendance */}
        <div className="card">
          <div className="card-header">
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ClockIcon style={{ width: 16, height: 16 }} /> Today's Attendance
            </div>
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
              <div className="empty-state-icon">
                <ClockIcon style={{ width: 48, height: 48 }} />
              </div>
              <h3>Not checked in yet</h3>
              <p>Go to Attendance to check in for today.</p>
            </div>
          )}
        </div>

        {/* Leave Balance Detail */}
        <div className="card">
          <div className="card-header">
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <CalendarIcon style={{ width: 16, height: 16 }} /> Leave Balance
            </div>
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
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <ClipboardCheckIcon style={{ width: 16, height: 16 }} /> My Pending Tasks
          </div>
        </div>
        {tasks.length === 0 ? (
          <div className="empty-state" style={{ padding: 30 }}>
            <div className="empty-state-icon">
              <CheckIcon style={{ width: 48, height: 48, color: 'var(--success)' }} />
            </div>
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
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <UsersIcon style={{ width: 16, height: 16 }} /> Upcoming Meetings
          </div>
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
                justifyContent: 'center', flexShrink: 0,
              }}>
                <UsersIcon style={{ width: 20, height: 20, color: 'var(--accent-light)' }} />
              </div>
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

      {/* Bottom Widgets: Company Policies + Upcoming Holidays */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Company Policies Widget */}
        <div className="card">
          <div className="card-header">
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <DocumentTextIcon style={{ width: 16, height: 16 }} /> Company Policies
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg-elevated)' }}>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total Policies</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-light)', marginTop: 4 }}>
                  {policyStats?.total_policies ?? 0}
                </div>
              </div>
              <DocumentTextIcon style={{ width: 32, height: 32, color: 'var(--accent)', opacity: 0.8 }} />
            </div>

            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)', marginBottom: 8 }}>Recently Updated</div>
              {!policyStats?.recently_updated || policyStats.recently_updated.length === 0 ? (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', padding: '10px 0' }}>
                  No recently updated policies.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {policyStats.recently_updated.slice(0, 3).map((p) => (
                    <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 8, borderBottom: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, flex: 1, marginRight: 12 }}>
                        <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={p.title}>
                          {p.title}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{p.category}</span>
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {new Date(p.updated_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Upcoming Holidays Widget */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <CalendarIcon style={{ width: 16, height: 16 }} /> Upcoming Holidays
            </div>
          </div>
          {holidays.length === 0 ? (
            <div className="empty-state" style={{ padding: 30 }}>
              <div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div>
              <h3>No upcoming holidays</h3>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {holidays.map((h) => (
                <div key={h.id} style={{
                  display: 'flex', gap: 12, paddingBottom: 10,
                  borderBottom: '1px solid var(--border)',
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 8,
                    background: 'var(--accent-glow)', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', flexShrink: 0,
                  }}>
                    <CalendarIcon style={{ width: 18, height: 18, color: 'var(--accent-light)' }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{h.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {new Date(h.date).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
