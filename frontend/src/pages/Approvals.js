/**
 * pages/Approvals.js
 * Centralized approval panel for Profile Updates, Work Delegations, and Comp-Off requests.
 */
import { useState, useEffect, useCallback } from 'react';
import { getPendingApprovals, actionApproval } from '../services/api';
import { useToast } from '../components/common/Toast';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { CheckIcon, CloseIcon, InboxIcon } from '../components/common/Icons';

export default function Approvals() {
  const toast = useToast();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);

  // Comments mapping approval ID -> text comment
  const [comments, setComments] = useState({});

  const loadApprovals = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getPendingApprovals();
      setApprovals(data || []);
    } catch {
      toast.error('Failed to load pending approvals.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const handleCommentChange = (id, text) => {
    setComments(prev => ({ ...prev, [id]: text }));
  };

  const handleAction = async (id, status) => {
    const comment = comments[id] || '';
    if (status === 'Rejected' && !comment.trim()) {
      toast.error('Comments / rejection reason is required for rejection.');
      return;
    }
    setActioningId(id);
    try {
      await actionApproval(id, {
        status,
        comments: comment.trim() || undefined
      });
      toast.success(`Request marked as ${status.toLowerCase()} successfully.`);
      loadApprovals();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Operation failed.');
    } finally {
      setActioningId(null);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="approvals-page fade-in">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="page-title">Approvals Dashboard</h1>
          <p className="page-subtitle">Centralized inbox to review and action pending organizational workflows</p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Pending Action Items ({approvals.length})</h2>
        </div>
        <div className="card-body" style={{ padding: approvals.length === 0 ? '40px 24px' : '16px 24px' }}>
          {approvals.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
              <InboxIcon style={{ width: 48, height: 48, strokeWidth: 1, color: 'var(--text-muted)', marginBottom: 12 }} />
              <p style={{ fontWeight: 600 }}>Your approvals inbox is clean!</p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                No pending Profile Updates, Work Delegations, or Comp-Off claims require your action.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {approvals.map((app) => {
                const details = app.target_details;
                return (
                  <div
                    key={app.id}
                    className="card"
                    style={{
                      border: '1px solid var(--border)',
                      background: 'var(--bg-surface)',
                      borderRadius: 'var(--radius)',
                      padding: 20
                    }}
                  >
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontWeight: 700, fontSize: 15 }}>{app.requester_name}</span>
                          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>submitted a request</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                          Applied: {new Date(app.created_at).toLocaleString()}
                        </div>
                      </div>
                      <Badge status={app.module_type} />
                    </div>

                    {/* Dynamic Detail Body based on module type */}
                    <div
                      style={{
                        padding: 14,
                        background: 'var(--bg-elevated)',
                        borderRadius: 'var(--radius)',
                        marginBottom: 16,
                        fontSize: 13,
                        border: '1px solid var(--border)'
                      }}
                    >
                      {app.module_type === 'CompOff' && details && (
                        <div>
                          <p style={{ marginBottom: 6 }}>
                            <strong>Requested Comp-Off Date Worked:</strong>{' '}
                            <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{details.date_worked}</span>
                          </p>
                          <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                            <strong>Reason:</strong> "{details.reason}"
                          </p>
                        </div>
                      )}

                      {app.module_type === 'WorkTransfer' && details && (
                        <div>
                          <p style={{ marginBottom: 6 }}>
                            <strong>Delegate Colleague:</strong> {details.delegate_name}
                          </p>
                          <p style={{ marginBottom: 6 }}>
                            <strong>Delegation Duration:</strong> {details.start_date} to {details.end_date}
                          </p>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
                            {details.transfer_approvals && <Badge status="Approvals" />}
                            {details.transfer_tasks && <Badge status="Tasks" />}
                            {details.transfer_meetings && <Badge status="Meetings" />}
                          </div>
                        </div>
                      )}

                      {app.module_type === 'UserProfileUpdate' && details && details.requested_changes && (
                        <div>
                          <p style={{ fontWeight: 600, marginBottom: 8 }}>Requested Profile Modifications:</p>
                          <table className="table" style={{ margin: 0, fontSize: 12 }}>
                            <thead>
                              <tr>
                                <th>Field</th>
                                <th>Current / Old Value</th>
                                <th>New Requested Value</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.keys(details.requested_changes).map((field) => (
                                <tr key={field}>
                                  <td style={{ fontWeight: 600 }}>{field.replace('_', ' ').toUpperCase()}</td>
                                  <td style={{ color: 'var(--text-secondary)' }}>{String(details.original_values[field] || '—')}</td>
                                  <td style={{ color: 'var(--accent)', fontWeight: 600 }}>{String(details.requested_changes[field] || '—')}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {app.module_type === 'ResumeUpdate' && details && (
                        <div>
                          <p style={{ marginBottom: 6 }}>
                            <strong>Requested Resume Upload:</strong>{' '}
                            <a 
                              href={`${details.resume_url}?auth_token=${sessionStorage.getItem('hr_token')}`} 
                              target="_blank" 
                              rel="noreferrer" 
                              style={{ color: 'var(--accent)', fontWeight: 700, textDecoration: 'underline' }}
                            >
                              Download/View Uploaded Resume
                            </a>
                          </p>
                        </div>
                      )}

                      {!details && (
                        <div style={{ color: 'var(--text-muted)' }}>Target request details could not be loaded.</div>
                      )}
                    </div>

                    {/* Actions and Comments footer */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'center' }}>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Add comments / rejection reason here..."
                        value={comments[app.id] || ''}
                        onChange={(e) => handleCommentChange(app.id, e.target.value)}
                        disabled={actioningId === app.id}
                      />
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          type="button"
                          className="btn btn-success"
                          onClick={() => handleAction(app.id, 'Approved')}
                          disabled={actioningId !== null}
                        >
                          <CheckIcon style={{ width: 14, height: 14 }} /> Approve
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger"
                          onClick={() => handleAction(app.id, 'Rejected')}
                          disabled={actioningId !== null}
                        >
                          <CloseIcon style={{ width: 14, height: 14 }} /> Reject
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
