/**
 * pages/Meetings.js
 * Upcoming/past meetings with tabbed view.
 * Admin: Can create, edit, delete. Employee: Read-only.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import MeetingForm from '../components/forms/MeetingForm';
import { useToast } from '../components/common/Toast';
import { getMeetings, createMeeting, updateMeeting, deleteMeeting, getDepartments } from '../services/api';
import { EditIcon, TrashIcon, PlusIcon, InboxIcon } from '../components/common/Icons';

export default function Meetings() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [tab,         setTab]         = useState('upcoming');
  const [meetings,    setMeetings]    = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [showForm,    setShowForm]    = useState(false);
  const [editTarget,  setEditTarget]  = useState(null);
  const [showDelete,  setShowDelete]  = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => { getDepartments().then((r) => setDepartments(r.data)); }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = tab === 'upcoming' ? { upcoming: true } : {};
      const { data } = await getMeetings(params);
      const now = new Date();
      const filtered = tab === 'past'
        ? data.filter((m) => new Date(m.scheduled_at) < now)
        : data;
      setMeetings(filtered);
    } catch { toast.error('Failed to load meetings.'); }
    finally { setLoading(false); }
    // eslint-disable-next-line
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  const handleSubmit = async (formData) => {
    setFormLoading(true);
    try {
      if (editTarget) { await updateMeeting(editTarget.id, formData); toast.success('Meeting updated.'); }
      else            { await createMeeting(formData);                toast.success('Meeting scheduled.'); }
      setShowForm(false); setEditTarget(null); load();
    } catch (err) { toast.error(err.response?.data?.error || 'Operation failed.'); }
    finally { setFormLoading(false); }
  };

  const handleDelete = async () => {
    try {
      await deleteMeeting(showDelete.id);
      toast.success('Meeting cancelled.');
      setShowDelete(null); load();
    } catch (err) { toast.error(err.response?.data?.error || 'Delete failed.'); }
  };

  const formatDate = (dt) => new Date(dt).toLocaleString('en-IN', {
    weekday: 'short', day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Meetings</h2>
          <p>View and manage scheduled meetings</p>
        </div>
        {isAdmin && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => { setEditTarget(null); setShowForm(true); }}>
              <PlusIcon style={{ marginRight: 6 }} /> Schedule Meeting
            </button>
          </div>
        )}
      </div>

      <div className="tabs">
        {[{ key: 'upcoming', label: '📅 Upcoming' }, { key: 'past', label: '🕐 Past' }].map((t) => (
          <button key={t.key} className={`tab-btn ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? <Spinner /> : (
        meetings.length === 0 ? (
          <div className="card">
            <div className="empty-state" style={{ padding: 60 }}>
              <div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div>
              <h3>No {tab} meetings</h3>
              {isAdmin && tab === 'upcoming' && (
                <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={() => setShowForm(true)}>
                  Schedule one now
                </button>
              )}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {meetings.map((m) => {
              const isPast = new Date(m.scheduled_at) < new Date();
              const isDept = !!m.department_id;
              return (
                <div
                  key={m.id}
                  className={`meeting-card ${isDept ? 'dept-meeting' : 'company-meeting'}`}
                  style={{ opacity: isPast ? 0.7 : 1, padding: '20px 24px', borderRadius: 'var(--radius)', border: '1px solid var(--border)', background: 'var(--card-bg)' }}
                >
                  <div style={{ display: 'flex', gap: 20, alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', gap: 20, alignItems: 'center', flex: 1, minWidth: '280px' }}>
                      <div style={{
                        width: 56, height: 56, borderRadius: 14, flexShrink: 0,
                        background: isDept ? 'rgba(59, 130, 246, 0.12)' : 'rgba(139, 92, 246, 0.12)',
                        color: isDept ? '#3b82f6' : '#8b5cf6',
                        display: 'flex', alignItems: 'center',
                        justifyContent: 'center', fontSize: 24,
                      }}>🤝</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
                          <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center' }}>
                            {m.title}
                            <span className="meeting-arrow-indicator">→</span>
                          </h3>
                          <span className={`badge ${isDept ? 'badge-employee' : 'badge-admin'}`} style={{
                            backgroundColor: isDept ? 'rgba(59, 130, 246, 0.1)' : 'rgba(139, 92, 246, 0.1)',
                            color: isDept ? '#3b82f6' : '#8b5cf6',
                            border: `1px solid ${isDept ? 'rgba(59, 130, 246, 0.2)' : 'rgba(139, 92, 246, 0.2)'}`
                          }}>
                            {m.department_name}
                          </span>
                        </div>
                        {m.description && <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 10, lineHeight: 1.5 }}>{m.description}</p>}
                        <div style={{ display: 'flex', gap: 20, fontSize: 13, color: 'var(--text-muted)', flexWrap: 'wrap', alignItems: 'center' }}>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>📅 {formatDate(m.scheduled_at)}</span>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>⏱ {m.duration_minutes} min</span>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>👤 {m.creator_name}</span>
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexShrink: 0, flexWrap: 'wrap', alignItems: 'center' }}>
                      {m.link && (
                        <a href={m.link} target="_blank" rel="noreferrer" className="btn btn-success btn-sm" style={{ padding: '8px 16px', borderRadius: 8 }}>🔗 Join</a>
                      )}
                      {isAdmin && (
                        <>
                          <button className="btn btn-secondary btn-sm" style={{ padding: 8, borderRadius: 8 }} onClick={() => { setEditTarget(m); setShowForm(true); }} title="Edit"><EditIcon /></button>
                          <button className="btn btn-danger btn-sm" style={{ padding: 8, borderRadius: 8 }} onClick={() => setShowDelete(m)} title="Cancel"><TrashIcon /></button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}

      <Modal isOpen={showForm} onClose={() => { setShowForm(false); setEditTarget(null); }}
        title={editTarget ? 'Edit Meeting' : 'Schedule Meeting'}>
        <MeetingForm
          initialData={editTarget}
          departments={departments}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditTarget(null); }}
          loading={formLoading}
        />
      </Modal>

      <Modal isOpen={!!showDelete} onClose={() => setShowDelete(null)} title="Cancel Meeting" size="sm">
        <p style={{ color: 'var(--text-secondary)' }}>
          Cancel <strong>"{showDelete?.title}"</strong>? This will remove it for all participants.
        </p>
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Keep Meeting</button>
          <button className="btn btn-danger" onClick={handleDelete}><TrashIcon style={{ marginRight: 6 }} /> Cancel Meeting</button>
        </div>
      </Modal>
    </div>
  );
}
