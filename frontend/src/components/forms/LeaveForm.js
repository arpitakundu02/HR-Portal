import { useState, useEffect } from 'react';
import { getEmployees } from '../../services/api';

export default function LeaveForm({ onSubmit, onCancel, loading }) {
  const [form, setForm] = useState({ leave_type: 'APL', start_date: '', end_date: '', reason: '', responsibility_transfer_id: '' });
  const [deptMembers, setDeptMembers] = useState([]);
  const change = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  // Load department members
  useEffect(() => {
    (async () => {
      try {
        const currentUser = JSON.parse(sessionStorage.getItem('hr_user') || '{}');
        if (currentUser.id) {
          // Fetch employees (limited to department by default in backend directory API for employees)
          const { data } = await getEmployees({ per_page: 200 });
          // Filter to active, same department, and exclude self
          const members = (data.employees || []).filter(e => 
            e.id !== currentUser.id && 
            e.is_active && 
            e.department_id === currentUser.department_id
          );
          setDeptMembers(members);
        }
      } catch (err) {
        console.error('Failed to load department members for responsibility transfer', err);
      }
    })();
  }, []);

  const days = form.start_date && form.end_date
    ? Math.max(0, Math.round((new Date(form.end_date) - new Date(form.start_date)) / 86400000) + 1)
    : 0;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...form,
      responsibility_transfer_id: Number(form.responsibility_transfer_id)
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">Leave Type <span className="form-required">*</span></label>
        <select className="form-control" name="leave_type" value={form.leave_type} onChange={change} required>
          <option value="APL">All Purpose Leave (APL)</option>
          <option value="WFH">Work From Home (WFH)</option>
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Start Date <span className="form-required">*</span></label>
          <input className="form-control" type="date" name="start_date" value={form.start_date}
            onChange={change} required min={new Date().toISOString().split('T')[0]} />
        </div>
        <div className="form-group">
          <label className="form-label">End Date <span className="form-required">*</span></label>
          <input className="form-control" type="date" name="end_date" value={form.end_date}
            onChange={change} required min={form.start_date} />
        </div>
      </div>

      {days > 0 && (
        <div className="alert alert-info" style={{ marginBottom: 16 }}>
          📅 <strong>{days} day{days > 1 ? 's' : ''}</strong> of leave requested
        </div>
      )}

      <div className="form-group">
        <label className="form-label">Responsibility Transfer <span className="form-required">*</span></label>
        <select
          className="form-control"
          name="responsibility_transfer_id"
          value={form.responsibility_transfer_id}
          onChange={change}
          required
        >
          <option value="">Select Temporary Owner</option>
          {deptMembers.map(m => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Reason</label>
        <textarea className="form-control" name="reason" value={form.reason} onChange={change}
          rows={3} placeholder="Briefly describe the reason for your leave request…" />
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Submitting…' : '📤 Submit Request'}
        </button>
      </div>
    </form>
  );
}
