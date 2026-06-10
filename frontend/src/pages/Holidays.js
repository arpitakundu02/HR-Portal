import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import { getHolidays, createHoliday, updateHoliday, deleteHoliday } from '../services/api';
import { CalendarIcon, PlusIcon, EditIcon, TrashIcon, InboxIcon, CloseIcon, SaveIcon } from '../components/common/Icons';

export default function Holidays() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [upcomingHolidays, setUpcomingHolidays] = useState([]);
  const [pastHolidays, setPastHolidays] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form Modal state
  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({ name: '', date: '', description: '' });

  // Delete modal state
  const [showDelete, setShowDelete] = useState(null);

  const loadHolidays = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch upcoming holidays
      const upcomingRes = await getHolidays({ upcoming: true });
      setUpcomingHolidays(upcomingRes.data);

      // Fetch all holidays, then filter past ones locally
      const allRes = await getHolidays({});
      const todayStr = new Date().toISOString().split('T')[0];
      const past = allRes.data.filter(h => h.date < todayStr);
      setPastHolidays(past);
    } catch (err) {
      toast.error('Failed to load holidays.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadHolidays();
  }, [loadHolidays]);

  const handleOpenForm = (holiday = null) => {
    if (holiday) {
      setEditTarget(holiday);
      setFormData({
        name: holiday.name,
        date: holiday.date,
        description: holiday.description || '',
      });
    } else {
      setEditTarget(null);
      // Default date to today
      setFormData({
        name: '',
        date: new Date().toISOString().split('T')[0],
        description: '',
      });
    }
    setShowForm(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Holiday name is required.');
      return;
    }
    if (!formData.date) {
      toast.error('Holiday date is required.');
      return;
    }

    setFormLoading(true);
    try {
      if (editTarget) {
        await updateHoliday(editTarget.id, formData);
        toast.success('Holiday updated successfully.');
      } else {
        await createHoliday(formData);
        toast.success('Holiday scheduled successfully.');
      }
      setShowForm(false);
      loadHolidays();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save holiday.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!showDelete) return;
    try {
      await deleteHoliday(showDelete.id);
      toast.success('Holiday deleted successfully.');
      setShowDelete(null);
      loadHolidays();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete holiday.');
    }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-IN', {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Holidays</h2>
          <p>Company holiday calendar and schedule</p>
        </div>
        {isAdmin && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => handleOpenForm()} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <PlusIcon /> Add Holiday
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <Spinner />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Upcoming Holidays Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <CalendarIcon style={{ width: 16, height: 16 }} /> Upcoming Holidays
              </div>
            </div>
            {upcomingHolidays.length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}>
                <div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div>
                <h3>No upcoming holidays</h3>
                <p>Enjoy your working days!</p>
              </div>
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Holiday Name</th>
                      <th>Description</th>
                      {isAdmin && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {upcomingHolidays.map((h) => (
                      <tr key={h.id}>
                        <td style={{ fontWeight: 600 }}>{formatDate(h.date)}</td>
                        <td style={{ fontWeight: 600, color: 'var(--accent)' }}>{h.name}</td>
                        <td className="td-muted">{h.description || '—'}</td>
                        {isAdmin && (
                          <td>
                            <div className="table-actions">
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: 8, borderRadius: 8 }}
                                onClick={() => handleOpenForm(h)}
                                title="Edit"
                              >
                                <EditIcon />
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                style={{ padding: 8, borderRadius: 8 }}
                                onClick={() => setShowDelete(h)}
                                title="Delete"
                              >
                                <TrashIcon />
                              </button>
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Past Holidays Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <CalendarIcon style={{ width: 16, height: 16 }} /> Past Holidays
              </div>
            </div>
            {pastHolidays.length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}>
                <div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div>
                <h3>No past holidays</h3>
              </div>
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Holiday Name</th>
                      <th>Description</th>
                      {isAdmin && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {pastHolidays.map((h) => (
                      <tr key={h.id}>
                        <td className="td-muted">{formatDate(h.date)}</td>
                        <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{h.name}</td>
                        <td className="td-muted">{h.description || '—'}</td>
                        {isAdmin && (
                          <td>
                            <div className="table-actions">
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: 8, borderRadius: 8 }}
                                onClick={() => handleOpenForm(h)}
                                title="Edit"
                              >
                                <EditIcon />
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                style={{ padding: 8, borderRadius: 8 }}
                                onClick={() => setShowDelete(h)}
                                title="Delete"
                              >
                                <TrashIcon />
                              </button>
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Holiday form modal */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={editTarget ? 'Edit Holiday' : 'Add Holiday'}
        size="sm"
      >
        <form onSubmit={handleFormSubmit}>
          <div className="form-group">
            <label className="form-label">Holiday Name <span style={{ color: 'var(--danger)' }}>*</span></label>
            <input
              type="text"
              className="form-control"
              value={formData.name}
              onChange={(e) => setFormData(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Christmas Day"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Date <span style={{ color: 'var(--danger)' }}>*</span></label>
            <input
              type="date"
              className="form-control"
              value={formData.date}
              onChange={(e) => setFormData(f => ({ ...f, date: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description (Optional)</label>
            <textarea
              className="form-control"
              value={formData.description}
              onChange={(e) => setFormData(f => ({ ...f, description: e.target.value }))}
              placeholder="Brief description of the holiday..."
              rows={3}
            />
          </div>
          <div className="form-actions" style={{ marginTop: 20 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <CloseIcon /> Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formLoading} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <SaveIcon /> {editTarget ? 'Save Changes' : 'Add Holiday'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={!!showDelete} onClose={() => setShowDelete(null)} title="Delete Holiday" size="sm">
        <p style={{ color: 'var(--text-secondary)' }}>
          Are you sure you want to delete the holiday <strong>"{showDelete?.name}"</strong> on <strong>{showDelete && formatDate(showDelete.date)}</strong>? This action cannot be undone.
        </p>
        <div className="form-actions" style={{ marginTop: 24 }}>
          <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <TrashIcon /> Delete Holiday
          </button>
        </div>
      </Modal>
    </div>
  );
}
