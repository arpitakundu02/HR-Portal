/**
 * pages/Departments.js
 * Admin-only department management with add/edit/delete.
 */
import { useState, useEffect, useCallback } from 'react';
import RoleRoute from '../components/common/RoleRoute';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import { useToast } from '../components/common/Toast';
import { getDepartments, createDepartment, updateDepartment, deleteDepartment } from '../services/api';
import { EditIcon, TrashIcon, PlusIcon, SaveIcon, BuildingIcon } from '../components/common/Icons';

function DepartmentsContent() {
  const toast = useToast();
  const [departments, setDepartments] = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [showForm,    setShowForm]    = useState(false);
  const [editTarget,  setEditTarget]  = useState(null);
  const [showDelete,  setShowDelete]  = useState(null);
  const [form,        setForm]        = useState({ name: '', description: '' });
  const [saving,      setSaving]      = useState(false);

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
    // eslint-disable-next-line
  }, []);

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

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Departments</h2>
          <p>{departments.length} department{departments.length !== 1 ? 's' : ''} configured</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={openAdd}><PlusIcon style={{ marginRight: 6 }} /> Add Department</button>
        </div>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr><th>#</th><th>Name</th><th>Description</th><th>Created</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {departments.length === 0 && (
                <tr><td colSpan={5}>
                  <div className="empty-state">
                    <div className="empty-state-icon"><BuildingIcon style={{ width: 48, height: 48 }} /></div><h3>No departments yet</h3>
                  </div>
                </td></tr>
              )}
              {departments.map((d, i) => (
                <tr key={d.id}>
                  <td className="td-muted">{i + 1}</td>
                  <td style={{ fontWeight: 600 }}>{d.name}</td>
                  <td className="td-muted">{d.description || '—'}</td>
                  <td className="td-muted">{new Date(d.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="table-actions">
                      <button className="btn btn-secondary btn-sm" onClick={() => openEdit(d)}><EditIcon style={{ marginRight: 6 }} /> Edit</button>
                      <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(d)}><TrashIcon style={{ marginRight: 6 }} /> Delete</button>
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
  return <RoleRoute roles={['Admin']}><DepartmentsContent /></RoleRoute>;
}
