/** components/forms/TaskForm.js — Create/edit task form (Admin only) */
import { useState, useEffect } from 'react';

const EMPTY = { title: '', description: '', employee_id: '', status: 'Pending', due_date: '' };

export default function TaskForm({ initialData, employees, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState(EMPTY);

  useEffect(() => {
    setForm(initialData ? { ...EMPTY, ...initialData, due_date: initialData.due_date || '' } : EMPTY);
  }, [initialData]);

  const change = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = { ...form };
    if (!payload.due_date) delete payload.due_date;
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">Task Title <span className="form-required">*</span></label>
        <input className="form-control" name="title" value={form.title} onChange={change} required placeholder="e.g. Prepare Q3 Report" />
      </div>

      <div className="form-group">
        <label className="form-label">Description</label>
        <textarea className="form-control" name="description" value={form.description} onChange={change} rows={3} />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Assign To <span className="form-required">*</span></label>
          <select className="form-control" name="employee_id" value={form.employee_id} onChange={change} required>
            <option value="">Select Employee</option>
            {employees.map((e) => (
              <option key={e.id} value={e.id}>{e.name} — {e.department_name || 'No Dept'}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Status</label>
          <select className="form-control" name="status" value={form.status} onChange={change}>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Due Date</label>
        <input className="form-control" type="date" name="due_date" value={form.due_date} onChange={change} />
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving…' : initialData ? '💾 Update Task' : '➕ Assign Task'}
        </button>
      </div>
    </form>
  );
}
