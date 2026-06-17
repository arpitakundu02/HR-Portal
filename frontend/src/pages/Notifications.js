/**
 * pages/Notifications.js
 * Consolidated "Notices & Announcements" view.
 * Displays Alerts/Notifications in Tab 1, and Announcements in Tab 2.
 * Includes Admin CRUD management for Announcements directly inside Tab 2.
 */
import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import { 
  getNotifications, 
  markNotificationRead, 
  markAllNotificationsRead,
  getAnnouncements, 
  createAnnouncement, 
  updateAnnouncement, 
  deleteAnnouncement,
  getDepartments
} from '../services/api';
import { 
  PlusIcon, 
  EditIcon, 
  TrashIcon, 
  MegaphoneIcon,
  CloseIcon, 
  SaveIcon,
  DownloadIcon,
  UploadIcon
} from '../components/common/Icons';

export default function Notifications() {
  const { user, isAdmin } = useAuth();
  const toast = useToast();
  const location = useLocation();

  const [activeTab, setActiveTab] = useState(
    location.state?.openAnnouncementId ? 'announcements' : 'notifications'
  );
  
  // Notifications state
  const [notifications, setNotifications] = useState([]);
  const [notifLoading, setNotifLoading] = useState(true);

  // Announcements state
  const [announcements, setAnnouncements] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [annLoading, setAnnLoading] = useState(true);

  // Form Modal state (Announcements CRUD)
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
  
  // Selected Announcement for detail view modal
  const [selectedAnn, setSelectedAnn] = useState(null);

  // File upload state for attachments
  const [file, setFile] = useState(null);

  // Load Notifications
  const loadNotifications = useCallback(async () => {
    setNotifLoading(true);
    try {
      const res = await getNotifications({ page: 1, per_page: 50 });
      setNotifications(res.data.notifications || []);
    } catch (err) {
      toast.error('Failed to load notifications.');
    } finally {
      setNotifLoading(false);
    }
  }, [toast]);

  // Load Announcements
  const loadAnnouncements = useCallback(async () => {
    setAnnLoading(true);
    try {
      const annRes = await getAnnouncements();
      const list = annRes.data || [];
      setAnnouncements(list);
      
      // Auto-open modal if navigated from dashboard
      if (location.state?.openAnnouncementId) {
        const target = list.find(a => a.id === location.state.openAnnouncementId);
        if (target) {
          setSelectedAnn(target);
          // Clear history state so it doesn't reopen on subsequent actions/reloads
          window.history.replaceState(null, '');
        }
      }

      if (isAdmin) {
        const deptRes = await getDepartments();
        setDepartments(deptRes.data || []);
      }
    } catch (err) {
      toast.error('Failed to load announcements.');
    } finally {
      setAnnLoading(false);
    }
  }, [isAdmin, toast, location.state]);

  useEffect(() => {
    if (activeTab === 'notifications') {
      loadNotifications();
    } else {
      loadAnnouncements();
    }
  }, [activeTab, loadNotifications, loadAnnouncements]);

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      toast.success('Notification marked as read.');
      loadNotifications();
    } catch (err) {
      toast.error('Failed to update notification.');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      toast.success('All notifications marked as read.');
      loadNotifications();
    } catch (err) {
      toast.error('Failed to update notifications.');
    }
  };

  // Announcement Actions
  const handleOpenForm = (announcement = null) => {
    setFile(null);
    if (announcement) {
      setEditTarget(announcement);
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

    const submissionData = new FormData();
    submissionData.append('title', formData.title.trim());
    submissionData.append('content', formData.content.trim());
    submissionData.append('audience_type', formData.audience_type);
    if (formData.audience_type === 'Department' && formData.department_id) {
      submissionData.append('department_id', formData.department_id);
    }
    if (formData.expires_at) {
      submissionData.append('expires_at', new Date(formData.expires_at).toISOString());
    }
    submissionData.append('is_active', formData.is_active);
    if (file) {
      submissionData.append('attachment', file);
    }

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
      loadAnnouncements();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save announcement.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteAnnouncement = async () => {
    if (!showDelete) return;
    try {
      await deleteAnnouncement(showDelete.id);
      toast.success('Announcement deleted successfully.');
      setShowDelete(null);
      loadAnnouncements();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete announcement.');
    }
  };

  return (
    <div className="fade-in" style={{ paddingBottom: 40 }}>
      {/* Tab Switcher / Page Header */}
      <div className="page-header" style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="page-title">Notices & Announcements</h1>
          <p className="page-subtitle">Central space for notifications, alerts, and company notices</p>
        </div>
        
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setActiveTab('notifications')}
            style={{
              padding: '10px 18px',
              fontWeight: 600,
              fontSize: 13,
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              background: activeTab === 'notifications' ? 'var(--accent)' : 'var(--bg-elevated)',
              color: activeTab === 'notifications' ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.2s ease'
            }}
          >
            🔔 Alerts & Notifications {notifications.some(n => !n.is_read) && `(${notifications.filter(n => !n.is_read).length})`}
          </button>
          <button
            onClick={() => setActiveTab('announcements')}
            style={{
              padding: '10px 18px',
              fontWeight: 600,
              fontSize: 13,
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              background: activeTab === 'announcements' ? 'var(--accent)' : 'var(--bg-elevated)',
              color: activeTab === 'announcements' ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.2s ease'
            }}
          >
            📢 Announcements
          </button>
        </div>
      </div>

      {/* Tabs Content */}
      {activeTab === 'notifications' ? (
        <div>
          <div className="card" style={{ marginBottom: 16, padding: '12px 20px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
            {notifications.some(n => !n.is_read) ? (
              <button className="btn btn-secondary btn-sm" onClick={handleMarkAllRead}>
                Mark all as read
              </button>
            ) : (
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>All caught up!</span>
            )}
          </div>

          <div className="card">
            <div className="card-body" style={{ padding: 0 }}>
              {notifLoading ? <Spinner /> : notifications.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
                  No notifications to display.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {notifications.map((notif) => (
                    <div
                      key={notif.id}
                      style={{
                        padding: '16px 24px',
                        borderBottom: '1px solid var(--border)',
                        background: notif.is_read ? 'transparent' : 'rgba(99, 102, 241, 0.04)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 16
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: notif.is_read ? 600 : 800, color: 'var(--text-primary)', fontSize: 14 }}>
                          {notif.title}
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
                          {notif.content}
                        </div>
                        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 6 }}>
                          {new Date(notif.created_at).toLocaleString()}
                        </div>
                      </div>
                      {!notif.is_read && (
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleMarkRead(notif.id)}
                        >
                          Mark read
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Announcements Tab Content */
        <div>
          {isAdmin && (
            <div className="card" style={{ marginBottom: 16, padding: '12px 20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary btn-sm" onClick={() => handleOpenForm()} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <PlusIcon /> Post Announcement
              </button>
            </div>
          )}

          {annLoading ? <Spinner /> : (
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
                    background: 'var(--bg-surface)',
                    cursor: 'pointer'
                  }}
                  onClick={() => setSelectedAnn(ann)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                      <div>
                        <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                          {ann.title}
                          {!ann.is_active && <span className="badge badge-employee">Draft/Inactive</span>}
                          {ann.expires_at && new Date(ann.expires_at) < new Date() && <span className="badge badge-employee">Expired</span>}
                        </h3>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                          Posted on {new Date(ann.created_at).toLocaleString()} by <strong>{ann.creator_name}</strong> &middot; Target: <strong>{ann.audience_type} {ann.department_name ? `(${ann.department_name})` : ''}</strong>
                          {ann.expires_at && ` &middot; Expires: ${new Date(ann.expires_at).toLocaleString()}`}
                        </div>
                      </div>
                      {isAdmin && (
                        <div className="table-actions" style={{ gap: 8 }} onClick={(e) => e.stopPropagation()}>
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
                    <div style={{ marginTop: 14, color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6 }}>
                      {ann.content.length > 200 ? ann.content.slice(0, 200) + '...' : ann.content}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Announcement Form Modal */}
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
              <div className="form-group">
                <label className="form-label">Attachment (PDF or DOCX) {editTarget && "(Leave empty to keep existing)"}</label>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <input
                    type="file"
                    id="announcement-attachment"
                    accept=".pdf,.docx"
                    style={{ display: 'none' }}
                    onChange={(e) => setFile(e.target.files[0])}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => document.getElementById('announcement-attachment').click()}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                  >
                    <UploadIcon style={{ width: 16, height: 16 }} /> {file ? "Change File" : "Choose File"}
                  </button>
                  {file && <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{file.name}</span>}
                  {!file && editTarget?.attachment_url && (
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Has existing attachment</span>
                  )}
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
              <button className="btn btn-danger" onClick={handleDeleteAnnouncement} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <TrashIcon /> Delete Announcement
              </button>
            </div>
          </Modal>

          {/* Announcement Detail Modal */}
          {selectedAnn && (
            <Modal isOpen={!!selectedAnn} onClose={() => setSelectedAnn(null)} title={selectedAnn.title} size="md">
              <div style={{ padding: '4px 0' }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', color: 'var(--text-muted)', fontSize: 13, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 12 }}>
                  <div>Posted by: <strong>{selectedAnn.creator_name}</strong></div>
                  <div>&middot;</div>
                  <div>Date: {new Date(selectedAnn.created_at).toLocaleString('en-IN')}</div>
                  {selectedAnn.audience_type && (
                    <>
                      <div>&middot;</div>
                      <div>Audience: {selectedAnn.audience_type} {selectedAnn.department_name ? `(${selectedAnn.department_name})` : ''}</div>
                    </>
                  )}
                </div>
                <div style={{ color: 'var(--text-primary)', fontSize: 15, lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 24 }}>
                  {selectedAnn.content}
                </div>
                {selectedAnn.attachment_url && (
                  <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Attachment:</span>
                    <a href={selectedAnn.attachment_url} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <DownloadIcon style={{ width: 16, height: 16 }} /> Download Attachment
                    </a>
                  </div>
                )}
              </div>
              <div className="form-actions" style={{ marginTop: 24 }}>
                <button className="btn btn-secondary" onClick={() => setSelectedAnn(null)}>Close</button>
              </div>
            </Modal>
          )}
        </div>
      )}
    </div>
  );
}
