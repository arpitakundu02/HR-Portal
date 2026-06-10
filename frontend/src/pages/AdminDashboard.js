/**
 * pages/AdminDashboard.js
 * Admin overview: KPI cards, Recharts charts, pending leaves, recent employees.
 */
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, Tooltip,
  ResponsiveContainer, XAxis, YAxis, Legend,
  AreaChart, Area,
} from 'recharts';
import StatCard from '../components/common/StatCard';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import AnnouncementWidget from '../components/common/AnnouncementWidget';
import { getEmployees, getLeaveRequests, actionLeaveRequest, getMeetings, getEmployeeStats, getTaskStats, getAttendanceStats, getLeaveStats } from '../services/api';
import { useToast } from '../components/common/Toast';
import { UsersIcon, ClockIcon, DocumentTextIcon, ClipboardCheckIcon, CalendarIcon, CheckIcon, CloseIcon, HourglassIcon, UserIcon } from '../components/common/Icons';

const CHART_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#f43f5e', '#38bdf8', '#a78bfa', '#34d399', '#fb923c'];

export default function AdminDashboard() {
  const toast = useToast();
  const [stats, setStats]                 = useState({ employees: 0, presentToday: 0, pendingLeaves: 0, completedTasks: 0 });
  const [deptData, setDeptData]           = useState([]);
  const [leaveData, setLeaveData]         = useState([]);
  const [attendanceTodayData, setAttendanceTodayData] = useState([]);
  const [taskData, setTaskData]           = useState([]);
  const [meetingsDensityData, setMeetingsDensityData] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [recentEmps, setRecentEmps]       = useState([]);
  const [loading, setLoading]             = useState(true);

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [
        empStatsRes,
        taskStatsRes,
        attendanceStatsRes,
        leaveStatsRes,
        meetRes,
        recentEmpRes,
        pendingLeavesRes
      ] = await Promise.all([
        getEmployeeStats(),
        getTaskStats(),
        getAttendanceStats(),
        getLeaveStats(),
        getMeetings({ upcoming: true }),
        getEmployees({ per_page: 6 }),
        getLeaveRequests({ status: 'Pending' })
      ]);

      const empStats = empStatsRes.data;
      const taskStats = taskStatsRes.data;
      const attendanceStats = attendanceStatsRes.data;
      const leaveStats = leaveStatsRes.data;
      const meetings = meetRes.data || [];
      const recentEmployees = recentEmpRes.data.employees || [];
      const pendingLeavesList = pendingLeavesRes.data || [];

      // KPI stats
      setStats({
        employees: empStats.active_employees,
        presentToday: attendanceStats.present_today,
        pendingLeaves: leaveStats.pending_leaves,
        completedTasks: taskStats.status_distribution.Completed,
      });

      // Department distribution chart
      setDeptData(empStats.department_distribution);

      // Leave status pie
      setLeaveData([
        { name: 'Pending', value: leaveStats.status_distribution.Pending, color: '#f59e0b' },
        { name: 'Approved', value: leaveStats.status_distribution.Approved, color: '#10b981' },
        { name: 'Rejected', value: leaveStats.status_distribution.Rejected, color: '#f43f5e' },
      ]);

      // Daily Attendance Donut Chart
      setAttendanceTodayData([
        { name: 'Present', value: attendanceStats.present_today, color: '#10b981' },
        { name: 'Absent', value: attendanceStats.absent_today, color: '#f43f5e' }
      ]);

      // Task Progress Chart
      setTaskData([
        { name: 'Pending', value: taskStats.status_distribution.Pending, color: '#f59e0b' },
        { name: 'In Progress', value: taskStats.status_distribution["In Progress"], color: '#6366f1' },
        { name: 'Completed', value: taskStats.status_distribution.Completed, color: '#10b981' }
      ]);

      // Meetings Density Chart (Next 7 Days)
      const densityMap = {};
      for (let i = 0; i < 7; i++) {
        const d = new Date();
        d.setDate(d.getDate() + i);
        const dayStr = d.toISOString().split('T')[0];
        densityMap[dayStr] = 0;
      }
      meetings.forEach((m) => {
        const dayStr = m.scheduled_at.split('T')[0];
        if (dayStr in densityMap) {
          densityMap[dayStr] += 1;
        }
      });
      const densityList = Object.keys(densityMap).sort().map((dayStr) => {
        const d = new Date(dayStr);
        const label = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        return { label, count: densityMap[dayStr] };
      });
      setMeetingsDensityData(densityList);

      // Pending leaves list
      setPendingLeaves(pendingLeavesList.slice(0, 8));

      // Recent employees
      setRecentEmps(recentEmployees);
    } catch (err) {
      toast.error('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveAction = async (id, status) => {
    try {
      await actionLeaveRequest(id, status);
      toast.success(`Leave request ${status.toLowerCase()}.`);
      loadDashboard();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Action failed.');
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="fade-in">
      {/* KPI Cards */}
      <div className="stats-grid">
        <StatCard icon={<UsersIcon />} value={stats.employees}      label="Total Employees"      color="#6366f1" />
        <StatCard icon={<ClockIcon />} value={stats.presentToday}   label="Present Today"        color="#10b981" />
        <StatCard icon={<DocumentTextIcon />} value={stats.pendingLeaves}  label="Pending Leaves"       color="#f59e0b" />
        <StatCard icon={<ClipboardCheckIcon />} value={stats.completedTasks} label="Completed Tasks"      color="#a78bfa" />
      </div>

      <AnnouncementWidget />

      {/* Row 1: Department Distribution and Leave Status */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Department distribution bar chart */}
        <div className="chart-card">
          <div className="chart-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <UsersIcon style={{ width: 16, height: 16 }} /> Department Distribution
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={deptData} margin={{ top: 4, right: 16, left: -10, bottom: 40 }}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
              <Tooltip cursor={{ fill: 'rgba(99,102,241,0.1)' }} />
              <Bar dataKey="count" name="Employees" radius={[4, 4, 0, 0]}>
                {deptData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leave status pie chart */}
        <div className="chart-card">
          <div className="chart-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <CalendarIcon style={{ width: 16, height: 16 }} /> Leave Request Status
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={leaveData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                outerRadius={80} innerRadius={45} paddingAngle={3}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={{ stroke: '#94a3b8' }}
              >
                {leaveData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2: Attendance Donut and Task Progress Bar */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Daily Attendance Donut Chart */}
        <div className="chart-card">
          <div className="chart-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <ClockIcon style={{ width: 16, height: 16 }} /> Today's Attendance
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={attendanceTodayData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                outerRadius={80} innerRadius={50} paddingAngle={4}
                label={({ name, value }) => `${name}: ${value}`}
                labelLine={{ stroke: '#94a3b8' }}
              >
                {attendanceTodayData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Task Progress Chart */}
        <div className="chart-card">
          <div className="chart-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <ClipboardCheckIcon style={{ width: 16, height: 16 }} /> Task Progress & Completion
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={taskData} margin={{ top: 4, right: 16, left: -10, bottom: 10 }}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
              <Tooltip cursor={{ fill: 'rgba(99,102,241,0.1)' }} />
              <Bar dataKey="value" name="Tasks" radius={[4, 4, 0, 0]}>
                {taskData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 3: Meetings Density Line/Area Chart (Full Width) */}
      <div className="card" style={{ marginBottom: 24, padding: '20px 24px' }}>
        <div className="chart-title" style={{ marginBottom: 16, fontWeight: 700, fontSize: 16, display: 'flex', alignItems: 'center', gap: 6 }}>
          <CalendarIcon style={{ width: 16, height: 16 }} /> Meetings Density (Upcoming 7 Days)
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={meetingsDensityData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorMeetings" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} allowDecimals={false} />
            <Tooltip />
            <Area type="monotone" dataKey="count" name="Meetings Scheduled" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorMeetings)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Pending Leave Requests */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div>
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <HourglassIcon style={{ width: 16, height: 16, color: 'var(--warning)' }} /> Pending Leave Requests
            </div>
            <div className="card-subtitle">Requires your action</div>
          </div>
        </div>
        {pendingLeaves.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <CheckIcon style={{ width: 48, height: 48, color: 'var(--success)' }} />
            </div>
            <h3>All caught up!</h3>
            <p>No pending leave requests.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Type</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Days</th>
                  <th>Reason</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingLeaves.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 600 }}>{l.employee_name}</td>
                    <td><Badge status={l.leave_type} /></td>
                    <td className="td-muted">{l.start_date}</td>
                    <td className="td-muted">{l.end_date}</td>
                    <td>{l.days_requested}</td>
                    <td className="td-muted" style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {l.reason || '—'}
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="btn btn-success btn-sm" onClick={() => handleLeaveAction(l.id, 'Approved')} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <CheckIcon style={{ width: 12, height: 12 }} /> Approve
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleLeaveAction(l.id, 'Rejected')} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <CloseIcon style={{ width: 12, height: 12 }} /> Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Employees */}
      <div className="card">
        <div className="card-header">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <UserIcon style={{ width: 16, height: 16 }} /> Recent Employees
          </div>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Department</th><th>Role</th><th>Joined</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentEmps.map((e) => (
                <tr key={e.id}>
                  <td className="td-muted">{e.employee_id}</td>
                  <td style={{ fontWeight: 600 }}>{e.name}</td>
                  <td className="td-muted">{e.department_name || '—'}</td>
                  <td><Badge status={e.role} /></td>
                  <td className="td-muted">{e.date_of_joining || '—'}</td>
                  <td><Badge status={e.is_active ? 'Active' : 'Inactive'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

