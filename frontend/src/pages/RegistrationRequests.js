/**
 * pages/RegistrationRequests.js
 * Admin portal to review pending self-registration requests.
 */
import { useState, useEffect, useCallback } from 'react';
import { getRegistrationRequests, actionRegistrationRequest, getDepartments, getEmployees } from '../services/api';
import { useToast } from '../components/common/Toast';
import Spinner from '../components/common/Spinner';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import { CheckIcon, CloseIcon, UsersIcon } from '../components/common/Icons';

export default function RegistrationRequests() {
  const toast = useToast();
  const [requests, setRequests] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);

  // Assignments state mapping request ID -> { department_id, manager_id }
  const [assignments, setAssignments] = useState({});

  // Reject modal state
  const [rejectTarget, setRejectTarget] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actioning, setActioning] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [reqRes, deptRes, empRes] = await Promise.all([
        getRegistrationRequests(),
        getDepartments(),
        getEmployees({ per_page: 1000 })
      ]);
      // Show pending requests first
      const sorted = reqRes.data.sort((a, b) => {
        if (a.status === 'Pending' && b.status !== 'Pending') return -1;
        if (a.status !== 'Pending' && b.status === 'Pending') return 1;
        return new Date(b.created_at) - new Date(a.created_at);
      });
      setRequests(sorted);
      setDepartments(deptRes.data || []);
      setEmployees(empRes.data.employees || []);

      // Initialize assignments for pending requests
      const initial = {};
      sorted.forEach(r => {
        if (r.status === 'Pending') {
          initial[r.id] = {
            department_id: r.department_id || '',
            manager_id: r.manager_id || ''
          };
        }
      });
      setAssignments(initial);
    } catch (err) {
      toast.error('Failed to load registration data.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAssignmentChange = (requestId, field, value) => {
    setAssignments(prev => ({
      ...prev,
      [requestId]: {
        ...prev[requestId],
        [field]: value
      }
    }));
  };

  const handleApprove = async (id) => {
    const { department_id, manager_id } = assignments[id] || {};
    setActioning(true);
    try {
      await actionRegistrationRequest(id, {
        status: 'Approved',
        department_id: department_id ? parseInt(department_id, 10) : null,
        manager_id: manager_id ? parseInt(manager_id, 10) : null
      });
      toast.success('Registration request approved successfully!');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to approve request.');
    } finally {
      setActioning(false);
    }
  };

  const handleRejectClick = (req) => {
    setRejectTarget(req);
    setRejectionReason('');
  };

  const handleRejectSubmit = async (e) => {
    e.preventDefault();
    if (!rejectionReason.trim()) {
      toast.error('Rejection reason is required.');
      return;
    }
    setActioning(true);
    try {
      await actionRegistrationRequest(rejectTarget.id, {
        status: 'Rejected',
        rejection_reason: rejectionReason.trim()
      });
      toast.success('Registration request rejected.');
      setRejectTarget(null);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to reject request.');
    } finally {
      setActioning(false);
    }
  };

  if (loading) return <Spinner />;

  const pendingRequests = requests.filter(r => r.status === 'Pending');
  const pastRequests = requests.filter(r => r.status !== 'Pending');

  return (
    <div className="registration-requests-page fade-in">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="page-title">Employee Self-Registration</h1>
          <p className="page-subtitle">Review, approve, or reject pending employee accounts</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 32 }}>
        <div className="card-header">
          <h2 className="card-title">Pending Requests ({pendingRequests.length})</h2>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {pendingRequests.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-secondary)' }}>
              <UsersIcon style={{ width: 48, height: 48, strokeWidth: 1, color: 'var(--text-muted)', marginBottom: 12 }} />
              <p style={{ fontWeight: 600 }}>No Pending Registration Requests</p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                New employee signup requests will appear here for approval.
              </p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Candidate Detail</th>
                    <th>Personal Info</th>
                    <th>Assign Department</th>
                    <th>Assign Manager</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingRequests.map((req) => (
                    <tr key={req.id}>
                      <td>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{req.name}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{req.email}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                          Submitted: {new Date(req.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                          {req.fathers_name && <div><span style={{ color: 'var(--text-muted)' }}>Father:</span> {req.fathers_name}</div>}
                          {req.dob && <div><span style={{ color: 'var(--text-muted)' }}>DOB:</span> {req.dob}</div>}
                          {req.blood_group && <div><span style={{ color: 'var(--text-muted)' }}>Blood:</span> {req.blood_group}</div>}
                          {req.address && <div style={{ fontSize: 11, color: 'var(--text-muted)', maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{req.address}</div>}
                        </div>
                      </td>
                      <td>
                        <select
                          className="form-control form-control-sm"
                          value={assignments[req.id]?.department_id || ''}
                          onChange={(e) => handleAssignmentChange(req.id, 'department_id', e.target.value)}
                          style={{ maxWidth: 180 }}
                        >
                          <option value="">No Department</option>
                          {departments.map((d) => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className="form-control form-control-sm"
                          value={assignments[req.id]?.manager_id || ''}
                          onChange={(e) => handleAssignmentChange(req.id, 'manager_id', e.target.value)}
                          style={{ maxWidth: 180 }}
                        >
                          <option value="">No Manager</option>
                          {employees.map((emp) => (
                            <option key={emp.id} value={emp.id}>{emp.name}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                          <button
                            type="button"
                            className="btn btn-success btn-sm"
                            onClick={() => handleApprove(req.id)}
                            disabled={actioning}
                          >
                            <CheckIcon style={{ width: 14, height: 14 }} /> Approve
                          </button>
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            onClick={() => handleRejectClick(req)}
                            disabled={actioning}
                          >
                            <CloseIcon style={{ width: 14, height: 14 }} /> Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Past Requests History</h2>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {pastRequests.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 24px', color: 'var(--text-muted)' }}>
              No request history available.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Status</th>
                    <th>Action Details</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {pastRequests.map((req) => (
                    <tr key={req.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{req.name}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{req.email}</div>
                      </td>
                      <td>
                        <Badge type={req.status === 'Approved' ? 'success' : 'danger'}>
                          {req.status}
                        </Badge>
                      </td>
                      <td>
                        {req.status === 'Approved' ? (
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                            Account activated. Sequential ID auto-assigned.
                          </div>
                        ) : (
                          <div style={{ fontSize: 12, color: 'var(--danger)' }}>
                            Reason: {req.rejection_reason || 'No reason provided'}
                          </div>
                        )}
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                        {req.actioned_at ? new Date(req.actioned_at).toLocaleDateString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {rejectTarget && (
        <Modal
          title={`Reject Registration: ${rejectTarget.name}`}
          onClose={() => setRejectTarget(null)}
        >
          <form onSubmit={handleRejectSubmit}>
            <div className="form-group">
              <label className="form-label">Rejection Reason <span className="form-required">*</span></label>
              <textarea
                className="form-control"
                required
                rows={3}
                placeholder="Specify details or reason for rejection..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              />
            </div>
            <div className="form-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setRejectTarget(null)}
                disabled={actioning}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-danger"
                disabled={actioning}
              >
                Confirm Rejection
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
