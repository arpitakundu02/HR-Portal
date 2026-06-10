import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import { 
  getAnnouncements, 
  createAnnouncement, 
  updateAnnouncement, 
  deleteAnnouncement,
  getDepartments 
} from '../services/api';
import { 
  CalendarIcon, 
  PlusIcon, 
  EditIcon, 
  TrashIcon, 
  InboxIcon, 
  CloseIcon, 
  SaveIcon,
  MegaphoneIcon 
} from '../components/common/Icons';

export default function Announcements() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [announcements, setAnnouncements] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form Modal state
  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    audience_type: 'All',
    department_id: '',
    expires_at: '',
    is_active: true
  });

  // Delete modal state
  const [showDelete, setShowDelete] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const annRes = await getAnnouncements();
      setAnnouncements(annRes.data);

      if (isAdmin) {
        const deptRes = await getDepartments();
        setDepartments(deptRes.data);
      }
    } catch (err) {
      toast.error('Failed to load announcements.');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenForm = (announcement = null) => {
    if (announcement) {
      setEditTarget(announcement);
      // Format expires_at from ISO to local datetime string or date string if present
      let formattedExpiry = '';
      if (announcement.expires_at) {
        formattedExpiry = announcement.expires_at.slice(0, 16);
      }
      setFormData({
        title: announcement.title,
        content: announcement.content,
        audience_type: announcement.audience_type,
        department_id: announcement.department_id || '',
        expires_at: formattedExpiry,
        is_active: announcement.is_active
      });
    } else {
      setEditTarget(null);
      setFormData({
        title: '',
        content: '',
        audience_type: 'All',
        department_id: '',
        expires_at: '',
        is_active: true
      });
    }
    setShowForm(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      toast.error('Title is required.');
      return;
    }
    if (!formData.content.trim()) {
      toast.error('Content is required.');
      return;
    }
    if (formData.audience_type === 'Department' && !formData.department_id) {
      toast.error('Department is required when target audience is Department.');
      return;
    }

    const submissionData = {
      title: formData.title.trim(),
      content: formData.content.trim(),
      audience_type: formData.audience_type,
      department_id: formData.audience_type === 'Department' ? parseInt(formData.department_id, 10) : null,
      expires_at: formData.expires_at ? new Date(formData.expires_at).toISOString() : null,
      is_active: formData.is_active
    };

    setFormLoading(true);
    try {
      if (editTarget) {
        await updateAnnouncement(editTarget.id, submissionData);
        toast.success('Announcement updated successfully.');
      } else {
        await createAnnouncement(submissionData);
        toast.success('Announcement posted successfully.');
      }
      setShowForm(false);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save announcement.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!showDelete) return;
    try {
      await deleteAnnouncement(showDelete.id);
      toast.success('Announcement deleted successfully.');
      setShowDelete(null);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete announcement.');
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Announcements</h2>
          <p>Important company updates and notice board</p>
        </div>
        {isAdmin && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => handleOpenForm()} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <PlusIcon /> Post Announcement
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <Spinner />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {announcements.length === 0 ? (
            <div className="card empty-state" style={{ padding: 40 }}>
              <div className="empty-state-icon">
                <MegaphoneIcon style={{ width: 48, height: 48, color: 'var(--text-muted)' }} />
              </div>
              <h3>No announcements</h3>
              <p>Check back later for company updates.</p>
            </div>
          ) : (
            announcements.map((ann) => (
              <div key={ann.id} className="card" style={{ 
                borderLeft: '4px solid var(--accent)', 
                opacity: ann.is_active ? 1 : 0.65,
                background: 'var(--bg-surface)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                      {ann.title}
                      {!ann.is_active && <span className="badge badge-employee">Draft/Inactive</span>}
                      {ann.expires_at && new Date(ann.expires_at) < new Date() && <span className="badge badge-employee">Expired</span>}
                    </h3>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      Posted on {new Date(ann.created_at).toLocaleString()} by <strong>{ann.creator_name}</strong> · Target: <strong>{ann.audience_type} {ann.department_name ? `(${ann.department_name})` : ''}</strong>
                      {ann.expires_at && ` · Expires: ${new Date(ann.expires_at).toLocaleString()}`}
                    </div>
                  </div>
                  {isAdmin && (
                    <div className="table-actions" style={{ gap: 8 }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '6px 10px', borderRadius: 8 }}
                        onClick={() => handleOpenForm(ann)}
                        title="Edit"
                      >
                        <EditIcon /> Edit
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        style={{ padding: '6px 10px', borderRadius: 8 }}
                        onClick={() => setShowDelete(ann)}
                        title="Delete"
                      >
                        <TrashIcon /> Delete
                      </button>
                    </div>
                  )}
                </div>
                <div style={{ marginTop: 14, color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {ann.content}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Announcement form modal */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={editTarget ? 'Edit Announcement' : 'Post Announcement'}
        size="md"
      >
        <form onSubmit={handleFormSubmit}>
          <div className="form-group">
            <label className="form-label">Title <span style={{ color: 'var(--danger)' }}>*</span></label>
            <input
              type="text"
              className="form-control"
              value={formData.title}
              onChange={(e) => setFormData(f => ({ ...f, title: e.target.value }))}
              placeholder="e.g. Town Hall Meeting Tomorrow"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Content <span style={{ color: 'var(--danger)' }}>*</span></label>
            <textarea
              className="form-control"
              value={formData.content}
              onChange={(e) => setFormData(f => ({ ...f, content: e.target.value }))}
              placeholder="Write your announcement message here..."
              rows={5}
              required
            />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Target Audience</label>
              <select
                className="form-control"
                value={formData.audience_type}
                onChange={(e) => setFormData(f => ({ ...f, audience_type: e.target.value }))}
              >
                <option value="All">All Staff</option>
                <option value="Department">Department Only</option>
                <option value="Employees">Non-Admin Employees</option>
                <option value="Managers">Managers Only</option>
              </select>
            </div>
            {formData.audience_type === 'Department' && (
              <div className="form-group">
                <label className="form-label">Select Department <span style={{ color: 'var(--danger)' }}>*</span></label>
                <select
                  className="form-control"
                  value={formData.department_id}
                  onChange={(e) => setFormData(f => ({ ...f, department_id: e.target.value }))}
                  required
                >
                  <option value="">-- Select Department --</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Expiry Date & Time (Optional)</label>
              <input
                type="datetime-local"
                className="form-control"
                value={formData.expires_at}
                onChange={(e) => setFormData(f => ({ ...f, expires_at: e.target.value }))}
              />
            </div>
            <div className="form-group" style={{ display: 'flex', alignItems: 'center', marginTop: 32 }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0 }}>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(f => ({ ...f, is_active: e.target.checked }))}
                  style={{ width: 18, height: 18 }}
                />
                Active (Published)
              </label>
            </div>
          </div>
          <div className="form-actions" style={{ marginTop: 24 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <CloseIcon /> Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formLoading} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <SaveIcon /> {editTarget ? 'Save Changes' : 'Post Announcement'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={!!showDelete} onClose={() => setShowDelete(null)} title="Delete Announcement" size="sm">
        <p style={{ color: 'var(--text-secondary)' }}>
          Are you sure you want to delete the announcement <strong>"{showDelete?.title}"</strong>? This action cannot be undone.
        </p>
        <div className="form-actions" style={{ marginTop: 24 }}>
          <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <TrashIcon /> Delete Announcement
          </button>
        </div>
      </Modal>
    </div>
  );
}
