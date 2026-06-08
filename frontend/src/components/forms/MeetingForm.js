/** components/forms/MeetingForm.js — Create/edit meeting form */
import { useState, useEffect } from 'react';

const EMPTY = { title: '', description: '', department_id: '', scheduled_at: '', duration_minutes: 30, link: '' };

export default function MeetingForm({ initialData, departments, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState(EMPTY);

  useEffect(() => {
    if (initialData) {
      setForm({
        ...EMPTY, ...initialData,
        scheduled_at: initialData.scheduled_at
          ? initialData.scheduled_at.slice(0, 16)  // format for datetime-local input
          : '',
        department_id: initialData.department_id || '',
      });
    } else {
      setForm(EMPTY);
    }
  }, [initialData]);

  const change = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = { ...form };
    if (!payload.department_id) payload.department_id = null;
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">Meeting Title <span className="form-required">*</span></label>
        <input className="form-control" name="title" value={form.title} onChange={change} required placeholder="e.g. Weekly Sync" />
      </div>

      <div className="form-group">
        <label className="form-label">Description</label>
        <textarea className="form-control" name="description" value={form.description} onChange={change} rows={2} />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Department</label>
          <select className="form-control" name="department_id" value={form.department_id} onChange={change}>
            <option value="">🌐 Company-Wide</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Duration (minutes)</label>
          <input className="form-control" type="number" name="duration_minutes" value={form.duration_minutes} onChange={change} min={5} />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Date & Time <span className="form-required">*</span></label>
        <input className="form-control" type="datetime-local" name="scheduled_at" value={form.scheduled_at} onChange={change} required />
      </div>

      <div className="form-group">
        <label className="form-label">Meeting Link (Zoom / Google Meet)</label>
        <input className="form-control" name="link" value={form.link} onChange={change} placeholder="https://meet.google.com/..." />
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving…' : initialData ? '💾 Update Meeting' : '📅 Schedule Meeting'}
        </button>
      </div>
    </form>
  );
}
