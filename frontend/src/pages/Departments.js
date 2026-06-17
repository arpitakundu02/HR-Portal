/**
 * pages/Departments.js
 * Department management and details panel.
 * Admins: Full CRUD + View Details.
 * Employees: View Directory + View Details.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import RoleRoute from '../components/common/RoleRoute';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import StatCard from '../components/common/StatCard';
import Badge from '../components/common/Badge';
import { useToast } from '../components/common/Toast';
import {
  BarChart, Bar, PieChart, Pie, Cell, Tooltip,
  ResponsiveContainer, XAxis, YAxis, Legend
} from 'recharts';
import {
  getDepartments, getDepartmentDetails, createDepartment,
  updateDepartment, deleteDepartment
} from '../services/api';
import {
  EditIcon, TrashIcon, PlusIcon, SaveIcon, BuildingIcon,
  UsersIcon, ClockIcon, DocumentTextIcon, ClipboardCheckIcon, CalendarIcon
} from '../components/common/Icons';

// Custom lightweight back arrow icon
const ArrowLeftIcon = ({ style = {} }) => (
  <svg style={{ width: 16, height: 16, display: 'inline-block', verticalAlign: 'middle', ...style }} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
  </svg>
);

function DepartmentDetails({ deptId, onBack }) {
  const toast = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await getDepartmentDetails(deptId);
        setData(res.data);
      } catch (err) {
        toast.error('Failed to load department details.');
      } finally {
        setLoading(false);
      }
    })();
  }, [deptId, toast]);

  if (loading) return <Spinner />;
  if (!data) return <p style={{ textAlign: 'center', padding: 24 }}>Department not found.</p>;

  const { department, stats, employees, tasks, leaves, meetings } = data;

  // Chart structures
  const leaveData = [
    { name: 'Pending', value: leaves.pending, color: '#f59e0b' },
    { name: 'Approved', value: leaves.approved, color: '#10b981' },
    { name: 'Rejected', value: leaves.rejected, color: '#f43f5e' },
  ];

  const taskData = [
    { name: 'Pending', value: tasks.pending, color: '#f59e0b' },
    { name: 'In Progress', value: tasks.in_progress, color: '#6366f1' },
    { name: 'Completed', value: tasks.completed, color: '#10b981' }
  ];

  return (
    <div className="fade-in">
      {/* Header with Back button */}
      <div className="page-header" style={{ marginBottom: 20 }}>
        <div className="page-header-left">
          <button className="btn btn-secondary btn-sm" onClick={onBack} style={{ marginBottom: 12 }}>
            <ArrowLeftIcon style={{ marginRight: 6 }} /> Back to Departments
          </button>
          <h2>🏢 {department.name} Details</h2>
          <p className="td-muted">Department ID: DEP-{department.id} · Created: {new Date(department.created_at).toLocaleDateString()}</p>
        </div>
      </div>

      {/* Description Card */}
      {department.description && (
        <div className="card" style={{ marginBottom: 24, padding: '16px 20px' }}>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}><strong>Description:</strong> {department.description}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <StatCard icon={<UsersIcon />} value={stats.total_employees} label="Total Employees" color="#6366f1" />
        <StatCard icon={<ClockIcon />} value={stats.present_today} label="Present Today" color="#10b981" />
        <StatCard icon={<DocumentTextIcon />} value={stats.on_leave_today} label="On Leave" color="#f59e0b" />
        <StatCard icon={<ClipboardCheckIcon />} value={stats.pending_tasks} label="Pending Tasks" color="#ef4444" />
        <StatCard icon={<ClipboardCheckIcon />} value={stats.completed_tasks} label="Completed Tasks" color="#10b981" />
        <StatCard icon={<CalendarIcon />} value={stats.upcoming_meetings_count} label="Upcoming Meetings" color="#a78bfa" />
      </div>

      {/* Row 1: Charts Row */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Task Progress Distribution */}
        <div className="chart-card">
          <div className="chart-title">✅ Task Progress & Completion</div>
          {tasks.total === 0 ? (
            <div className="empty-state" style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <p className="td-muted">No task metrics available</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={taskData} margin={{ top: 4, right: 16, left: -10, bottom: 10 }}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" name="Tasks" radius={[4, 4, 0, 0]}>
                  {taskData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Leave status distribution */}
        <div className="chart-card">
          <div className="chart-title">📅 Leave Request Distribution</div>
          {leaves.pending + leaves.approved + leaves.rejected === 0 ? (
            <div className="empty-state" style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <p className="td-muted">No leave metrics available</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={leaveData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                  outerRadius={80} innerRadius={45} paddingAngle={3}
                >
                  {leaveData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip />
                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 13 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Grid 2: Employees Section */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div className="card-title">👥 Department Employee Directory</div>
        </div>
        {employees.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><UsersIcon style={{ width: 48, height: 48 }} /></div>
            <h3>No employees registered in this department</h3>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Employee ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Rank/Designation</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((e) => (
                  <tr key={e.id}>
                    <td className="td-muted">{e.employee_id}</td>
                    <td style={{ fontWeight: 600 }}>{e.name}</td>
                    <td className="td-muted">{e.email}</td>
                    <td><Badge status={e.is_line_manager ? 'Line Manager' : e.role} /></td>
                    <td className="td-muted">{e.rank || '—'}</td>
                    <td><Badge status={e.is_active ? 'Active' : 'Inactive'} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Meetings Section */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">📅 Upcoming Department Meetings</div>
        </div>
        {meetings.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><CalendarIcon style={{ width: 48, height: 48 }} /></div>
            <h3>No upcoming meetings scheduled</h3>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Meeting Title</th>
                  <th>Scheduled Date/Time</th>
                  <th>Organizer</th>
                  <th>Virtual Link</th>
                </tr>
              </thead>
              <tbody>
                {meetings.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 600 }}>{m.title}</td>
                    <td className="td-muted">{new Date(m.scheduled_at).toLocaleString()}</td>
                    <td className="td-muted">{m.creator_name || 'Admin'}</td>
                    <td>
                      {m.link ? (
                        <a href={m.link} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ padding: '4px 8px', fontSize: 11 }}>
                          Join Meeting
                        </a>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function DepartmentsContent() {
  const { isAdmin } = useAuth();
  const toast = useToast();
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDeptId, setSelectedDeptId] = useState(null);

  // Forms and Modals
  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [showDelete, setShowDelete] = useState(null);
  const [form, setForm] = useState({ name: '', description: '' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getDepartments();
      setDepartments(data);
    } catch {
      toast.error('Failed to load departments.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const openAdd = () => { setEditTarget(null); setForm({ name: '', description: '' }); setShowForm(true); };
  const openEdit = (d) => { setEditTarget(d); setForm({ name: d.name, description: d.description || '' }); setShowForm(true); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editTarget) {
        await updateDepartment(editTarget.id, form);
        toast.success('Department updated.');
      } else {
        await createDepartment(form);
        toast.success('Department created.');
      }
      setShowForm(false);
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Operation failed.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteDepartment(showDelete.id);
      toast.success('Department deleted.');
      setShowDelete(null);
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Cannot delete department.');
    }
  };

  if (loading) return <Spinner />;

  if (selectedDeptId) {
    return <DepartmentDetails deptId={selectedDeptId} onBack={() => setSelectedDeptId(null)} />;
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Departments</h2>
          <p>{departments.length} department{departments.length !== 1 ? 's' : ''} configured</p>
        </div>
        {isAdmin && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={openAdd}><PlusIcon style={{ marginRight: 6 }} /> Add Department</button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Description</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {departments.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state">
                      <div className="empty-state-icon"><BuildingIcon style={{ width: 48, height: 48 }} /></div>
                      <h3>No departments yet</h3>
                    </div>
                  </td>
                </tr>
              )}
              {departments.map((d, i) => (
                <tr key={d.id}>
                  <td className="td-muted">{i + 1}</td>
                  <td style={{ fontWeight: 600 }}>{d.name}</td>
                  <td className="td-muted">{d.description || '—'}</td>
                  <td className="td-muted">{new Date(d.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="table-actions">
                      <button className="btn btn-secondary btn-sm" onClick={() => setSelectedDeptId(d.id)}>
                        View Details
                      </button>
                      {isAdmin && (
                        <>
                          <button className="btn btn-secondary btn-sm" onClick={() => openEdit(d)}>
                            <EditIcon style={{ marginRight: 6 }} /> Edit
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(d)}>
                            <TrashIcon style={{ marginRight: 6 }} /> Delete
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Modal */}
      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={editTarget ? `Edit: ${editTarget.name}` : 'New Department'} size="sm">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Department Name <span className="form-required">*</span></label>
            <input className="form-control" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required placeholder="e.g. Engineering" />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea className="form-control" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={3} />
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)} disabled={saving}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving…' : editTarget ? <><SaveIcon style={{ marginRight: 6 }} /> Update</> : <><PlusIcon style={{ marginRight: 6 }} /> Create</>}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirm */}
      <Modal isOpen={!!showDelete} onClose={() => setShowDelete(null)} title="Delete Department" size="sm">
        <p style={{ color: 'var(--text-secondary)' }}>
          Delete <strong>{showDelete?.name}</strong>? This cannot be undone.
          Departments with active employees cannot be deleted.
        </p>
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete}><TrashIcon style={{ marginRight: 6 }} /> Delete</button>
        </div>
      </Modal>
    </div>
  );
}

export default function Departments() {
  return <RoleRoute roles={['Admin', 'Employee']}><DepartmentsContent /></RoleRoute>;
}
