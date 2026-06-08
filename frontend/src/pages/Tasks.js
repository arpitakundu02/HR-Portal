/**
 * pages/Tasks.js
 * Admin: Assign tasks, view all tasks in a table, filter by employee/status.
 * Employee: Kanban-style column view with status dropdown to update own tasks.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import TaskForm from '../components/forms/TaskForm';
import { useToast } from '../components/common/Toast';
import { getTasks, createTask, updateTask, deleteTask, getEmployees } from '../services/api';
import { EditIcon, TrashIcon, PlusIcon, InboxIcon } from '../components/common/Icons';

const STATUSES = ['Pending', 'In Progress', 'Completed'];

export default function Tasks() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [tasks,      setTasks]      = useState([]);
  const [employees,  setEmployees]  = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [formLoading,setFormLoading]= useState(false);
  const [showForm,   setShowForm]   = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [showDelete, setShowDelete] = useState(null);
  const [empFilter,  setEmpFilter]  = useState('');
  const [statFilter, setStatFilter] = useState('');

  useEffect(() => {
    if (isAdmin) getEmployees({ per_page: 200 }).then((r) => setEmployees(r.data.employees || []));
  }, [isAdmin]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { per_page: 200 };
      if (empFilter)  params.employee_id = empFilter;
      if (statFilter) params.status      = statFilter;
      const { data } = await getTasks(params);
      setTasks(data.tasks || []);
    } catch { toast.error('Failed to load tasks.'); }
    finally { setLoading(false); }
    // eslint-disable-next-line
  }, [empFilter, statFilter]);

  useEffect(() => { load(); }, [load]);

  const handleSubmit = async (formData) => {
    setFormLoading(true);
    try {
      if (editTarget) { await updateTask(editTarget.id, formData); toast.success('Task updated.'); }
      else            { await createTask(formData);                toast.success('Task assigned.'); }
      setShowForm(false); setEditTarget(null); load();
    } catch (err) { toast.error(err.response?.data?.error || 'Operation failed.'); }
    finally { setFormLoading(false); }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await updateTask(taskId, { status: newStatus });
      toast.success('Task status updated.');
      load();
    } catch (err) { toast.error(err.response?.data?.error || 'Update failed.'); }
  };

  const handleDelete = async () => {
    try {
      await deleteTask(showDelete.id);
      toast.success('Task deleted.');
      setShowDelete(null);
      load();
    } catch (err) { toast.error(err.response?.data?.error || 'Delete failed.'); }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Task Management</h2>
          <p>{tasks.length} task{tasks.length !== 1 ? 's' : ''}</p>
        </div>
        {isAdmin && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => { setEditTarget(null); setShowForm(true); }}><PlusIcon style={{ marginRight: 6 }} /> Assign Task</button>
          </div>
        )}
      </div>

      {/* Filters (Admin only) */}
      {isAdmin && (
        <div className="search-filter-row">
          <select className="form-control filter-select" value={empFilter} onChange={(e) => setEmpFilter(e.target.value)}>
            <option value="">All Employees</option>
            {employees.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
          <select className="form-control filter-select" value={statFilter} onChange={(e) => setStatFilter(e.target.value)}>
            <option value="">All Statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      )}

      {loading ? <Spinner /> : (
        isAdmin ? (
          /* Admin: Table view */
          <div className="card">
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr><th>Title</th><th>Assigned To</th><th>Assigned By</th><th>Status</th><th>Due Date</th><th>Created</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {tasks.length === 0 && (
                    <tr><td colSpan={7}><div className="empty-state"><div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div><h3>No tasks found</h3></div></td></tr>
                  )}
                  {tasks.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontWeight: 600 }}>{t.title}</td>
                      <td className="td-muted">{t.employee_name}</td>
                      <td className="td-muted">{t.assigner_name}</td>
                      <td><Badge status={t.status} /></td>
                      <td className="td-muted">{t.due_date || '—'}</td>
                      <td className="td-muted">{new Date(t.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="table-actions">
                          <button className="btn btn-secondary btn-sm" onClick={() => { setEditTarget(t); setShowForm(true); }} title="Edit"><EditIcon /></button>
                          <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(t)} title="Delete"><TrashIcon /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* Employee: Kanban columns */
          <div className="kanban-board">
            {STATUSES.map((col) => {
              const colTasks = tasks.filter((t) => t.status === col);
              return (
                <div key={col} className="kanban-col">
                  <div className="kanban-col-header">
                    <span className="kanban-col-title">{col}</span>
                    <span className="kanban-count">{colTasks.length}</span>
                  </div>
                  {colTasks.length === 0 && (
                    <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, padding: '20px 0' }}>No tasks</div>
                  )}
                  {colTasks.map((t) => (
                    <div key={t.id} className="task-card">
                      <div className="task-card-title">{t.title}</div>
                      {t.description && (
                        <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 6 }}>{t.description}</div>
                      )}
                      <div className="task-card-meta">
                        <span>👤 {t.assigner_name}</span>
                        {t.due_date && <span>📅 {t.due_date}</span>}
                      </div>
                      <div className="task-card-actions">
                        <select
                          className="form-control"
                          style={{ padding: '4px 8px', fontSize: 12 }}
                          value={t.status}
                          onChange={(e) => handleStatusChange(t.id, e.target.value)}
                        >
                          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )
      )}

      {/* Task Form Modal */}
      <Modal isOpen={showForm} onClose={() => { setShowForm(false); setEditTarget(null); }}
        title={editTarget ? 'Edit Task' : 'Assign New Task'}>
        <TaskForm
          initialData={editTarget}
          employees={employees}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditTarget(null); }}
          loading={formLoading}
        />
      </Modal>

      {/* Delete Confirm */}
      <Modal isOpen={!!showDelete} onClose={() => setShowDelete(null)} title="Delete Task" size="sm">
        <p style={{ color: 'var(--text-secondary)' }}>Delete task <strong>"{showDelete?.title}"</strong>? This cannot be undone.</p>
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete}><TrashIcon style={{ marginRight: 6 }} /> Delete</button>
        </div>
      </Modal>
    </div>
  );
}
