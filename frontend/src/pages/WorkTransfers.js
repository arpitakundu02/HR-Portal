import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import { 
  getWorkTransfers, 
  createWorkTransfer, 
  getEmployees 
} from '../services/api';
import { 
  CalendarIcon, 
  PlusIcon, 
  InboxIcon, 
  CloseIcon, 
  SaveIcon, 
  UsersIcon,
  CheckIcon
} from '../components/common/Icons';

export default function WorkTransfers() {
  const { user } = useAuth();
  const toast = useToast();

  const [myRequests, setMyRequests] = useState([]);
  const [pendingTransfers, setPendingTransfers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form Modal state
  const [showForm, setShowForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({
    delegate_to_id: '',
    start_date: '',
    end_date: '',
    transfer_tasks: true,
    transfer_approvals: true,
    transfer_meetings: true
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getWorkTransfers();
      setMyRequests(res.data.my_requests || []);
      setPendingTransfers(res.data.received_transfers || []);

      const empRes = await getEmployees({ per_page: 1000 });
      // Exclude current user from delegate list
      const otherEmps = (empRes.data.employees || []).filter(e => e.id !== user?.id && e.is_active);
      setEmployees(otherEmps);
    } catch (err) {
      toast.error('Failed to load work transfers.');
    } finally {
      setLoading(false);
    }
  }, [user, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenForm = () => {
    setFormData({
      delegate_to_id: '',
      start_date: '',
      end_date: '',
      transfer_tasks: true,
      transfer_approvals: true,
      transfer_meetings: true
    });
    setShowForm(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!formData.delegate_to_id) {
      toast.error('Please select a delegate.');
      return;
    }
    if (!formData.start_date || !formData.end_date) {
      toast.error('Start and end dates are required.');
      return;
    }
    if (new Date(formData.start_date) > new Date(formData.end_date)) {
      toast.error('Start date cannot be after end date.');
      return;
    }

    setFormLoading(true);
    try {
      await createWorkTransfer({
        delegate_to_id: parseInt(formData.delegate_to_id, 10),
        start_date: formData.start_date,
        end_date: formData.end_date,
        transfer_tasks: formData.transfer_tasks,
        transfer_approvals: formData.transfer_approvals,
        transfer_meetings: formData.transfer_meetings
      });
      toast.success('Work transfer request submitted successfully.');
      setShowForm(false);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit work transfer request.');
    } finally {
      setFormLoading(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'Approved': return 'badge badge-admin'; // Green / Admin equivalent styling
      case 'Rejected': return 'badge badge-danger';
      case 'Pending': return 'badge badge-employee';
      default: return 'badge';
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Work Transfer & Delegation</h2>
          <p>Delegate approvals, tasks, and meeting ownership to another colleague during leave or absence.</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={handleOpenForm} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <PlusIcon /> Create Transfer Request
          </button>
        </div>
      </div>

      {loading ? (
        <Spinner />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
          
          {/* My Requests Section */}
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>My Requests</h3>
            {myRequests.length === 0 ? (
              <div className="card empty-state" style={{ padding: 24, textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', margin: 0 }}>You have not submitted any work transfer requests.</p>
              </div>
            ) : (
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Delegate To</th>
                      <th>Start Date</th>
                      <th>End Date</th>
                      <th>Delegated Items</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myRequests.map((req) => (
                      <tr key={req.id}>
                        <td><strong>{req.delegate_name}</strong></td>
                        <td>{new Date(req.start_date).toLocaleDateString()}</td>
                        <td>{new Date(req.end_date).toLocaleDateString()}</td>
                        <td>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {req.transfer_tasks && <span className="badge" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>Tasks</span>}
                            {req.transfer_approvals && <span className="badge" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>Approvals</span>}
                            {req.transfer_meetings && <span className="badge" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>Meetings</span>}
                          </div>
                        </td>
                        <td><span className={getStatusBadgeClass(req.status)}>{req.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pending / Received Transfers Section */}
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>Transfers Delegated to Me</h3>
            {pendingTransfers.length === 0 ? (
              <div className="card empty-state" style={{ padding: 24, textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', margin: 0 }}>No work transfers have been delegated to you.</p>
              </div>
            ) : (
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Delegated By</th>
                      <th>Start Date</th>
                      <th>End Date</th>
                      <th>Delegated Items</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingTransfers.map((req) => (
                      <tr key={req.id}>
                        <td><strong>{req.requester_name}</strong></td>
                        <td>{new Date(req.start_date).toLocaleDateString()}</td>
                        <td>{new Date(req.end_date).toLocaleDateString()}</td>
                        <td>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {req.transfer_tasks && <span className="badge" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>Tasks</span>}
                            {req.transfer_approvals && <span className="badge" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>Approvals</span>}
                            {req.transfer_meetings && <span className="badge" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>Meetings</span>}
                          </div>
                        </td>
                        <td><span className={getStatusBadgeClass(req.status)}>{req.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      )}

      {/* Form Modal */}
      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title="Create Work Transfer / Delegation Request"
        size="md"
      >
        <form onSubmit={handleFormSubmit}>
          <div className="form-group">
            <label className="form-label">Delegate To <span style={{ color: 'var(--danger)' }}>*</span></label>
            <select
              className="form-control"
              value={formData.delegate_to_id}
              onChange={(e) => setFormData(f => ({ ...f, delegate_to_id: e.target.value }))}
              required
            >
              <option value="">-- Select Employee --</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.first_name} {emp.last_name} ({emp.email})
                </option>
              ))}
            </select>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Start Date <span style={{ color: 'var(--danger)' }}>*</span></label>
              <input
                type="date"
                className="form-control"
                value={formData.start_date}
                onChange={(e) => setFormData(f => ({ ...f, start_date: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">End Date <span style={{ color: 'var(--danger)' }}>*</span></label>
              <input
                type="date"
                className="form-control"
                value={formData.end_date}
                onChange={(e) => setFormData(f => ({ ...f, end_date: e.target.value }))}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: 16 }}>
            <label className="form-label">Select Delegated Authorities</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.transfer_tasks}
                  onChange={(e) => setFormData(f => ({ ...f, transfer_tasks: e.target.checked }))}
                  style={{ width: 18, height: 18 }}
                />
                <span><strong>Transfer Task Visibility</strong> (Delegate can view and progress tasks assigned to me)</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.transfer_approvals}
                  onChange={(e) => setFormData(f => ({ ...f, transfer_approvals: e.target.checked }))}
                  style={{ width: 18, height: 18 }}
                />
                <span><strong>Transfer Approval Routing</strong> (Delegate can review and take actions on approvals pending my request)</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.transfer_meetings}
                  onChange={(e) => setFormData(f => ({ ...f, transfer_meetings: e.target.checked }))}
                  style={{ width: 18, height: 18 }}
                />
                <span><strong>Share Meeting Ownership</strong> (Delegate shares ownership and calendar visibility for my departmental meetings)</span>
              </label>
            </div>
          </div>

          <div className="form-actions" style={{ marginTop: 24 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <CloseIcon /> Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formLoading} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <SaveIcon /> Submit Request
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
