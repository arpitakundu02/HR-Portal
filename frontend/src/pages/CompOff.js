/**
 * pages/CompOff.js
 * Compensatory Off (Comp-Off) dashboard.
 * - Balance Card
 * - Apply Request Form
 * - Request History
 * - Admin view: Reports, Employee balances list, Export to Excel.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { applyCompOff, getCompOffHistory, getCompOffBalance, getAdminCompOffAll } from '../services/api';
import { useToast } from '../components/common/Toast';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { ClockIcon, CalendarIcon, PlusIcon, DownloadIcon, UsersIcon } from '../components/common/Icons';

export default function CompOff() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [tab, setTab] = useState('overview'); // overview or admin-view
  const [balance, setBalance] = useState({ allocated: 0, used: 0, remaining: 0 });
  const [history, setHistory] = useState([]);
  const [adminData, setAdminData] = useState({ requests: [], balances: [] });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Form
  const [form, setForm] = useState({ date_worked: '', reason: '' });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [balRes, histRes, adminRes] = await Promise.all([
          getCompOffBalance(),
          getCompOffHistory(),
          getAdminCompOffAll()
        ]);
        setBalance(balRes.data);
        setHistory(histRes.data);
        setAdminData(adminRes.data);
      } else {
        const [balRes, histRes] = await Promise.all([
          getCompOffBalance(),
          getCompOffHistory()
        ]);
        setBalance(balRes.data);
        setHistory(histRes.data);
      }
    } catch (err) {
      toast.error('Failed to load Comp-Off dashboard data.');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.date_worked || !form.reason.trim()) {
      toast.error('All fields are required.');
      return;
    }
    setSubmitting(true);
    try {
      await applyCompOff({
        date_worked: form.date_worked,
        reason: form.reason.trim()
      });
      toast.success('Comp-Off request submitted successfully! Pending approval.');
      setForm({ date_worked: '', reason: '' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit Comp-Off request.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await fetch('/api/exports/comp-off', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('hr_token')}`
        }
      });
      if (!response.ok) throw new Error('Report generation failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CompOff_Report_${new Date().toISOString().slice(0,10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast.success('Comp-Off report exported successfully.');
    } catch (err) {
      toast.error('Failed to export Comp-Off report.');
    } finally {
      setExporting(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="comp-off-page fade-in">
      <div className="page-header" style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Compensatory Off (Comp-Off)</h1>
          <p className="page-subtitle">Claim credit balance for weekend/holiday working hours</p>
        </div>
        
        {isAdmin && (
          <div className="tab-buttons" style={{ display: 'flex', gap: 8 }}>
            <button
              className={`btn ${tab === 'overview' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTab('overview')}
            >
              My requests
            </button>
            <button
              className={`btn ${tab === 'admin-view' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTab('admin-view')}
            >
              <UsersIcon style={{ width: 14, height: 14 }} /> Employee Balances & Requests
            </button>
          </div>
        )}
      </div>

      {tab === 'overview' ? (
        <div className="grid-3-1" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
          {/* Main Area */}
          <div>
            {/* KPI widgets */}
            <div className="grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
              <div className="stat-card" style={{ padding: 18 }}>
                <div className="stat-icon" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent)' }}>
                  <CalendarIcon style={{ width: 22, height: 22 }} />
                </div>
                <div className="stat-info">
                  <div className="stat-value">{balance.allocated}</div>
                  <div className="stat-label" style={{ fontSize: 10 }}>Total Credited</div>
                </div>
              </div>
              <div className="stat-card" style={{ padding: 18 }}>
                <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}>
                  <ClockIcon style={{ width: 22, height: 22 }} />
                </div>
                <div className="stat-info">
                  <div className="stat-value">{balance.used}</div>
                  <div className="stat-label" style={{ fontSize: 10 }}>Total Availed</div>
                </div>
              </div>
              <div className="stat-card" style={{ padding: 18 }}>
                <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                  <ClockIcon style={{ width: 22, height: 22 }} />
                </div>
                <div className="stat-info">
                  <div className="stat-value" style={{ color: '#10b981' }}>{balance.remaining}</div>
                  <div className="stat-label" style={{ fontSize: 10 }}>Available Balance</div>
                </div>
              </div>
            </div>

            {/* History Table */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Claim History</h2>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                {history.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                    No Comp-Off requests submitted yet.
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Date Worked</th>
                          <th>Reason</th>
                          <th>Status</th>
                          <th>Resolution Detail</th>
                          <th>Submitted</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((req) => (
                          <tr key={req.id}>
                            <td style={{ fontWeight: 700 }}>{req.date_worked}</td>
                            <td>{req.reason}</td>
                            <td>
                              <Badge status={req.status} />
                            </td>
                            <td>
                              {req.status === 'Rejected' ? (
                                <span style={{ color: 'var(--danger)', fontSize: 12 }}>
                                  Reason: {req.rejection_reason || 'No details provided.'}
                                </span>
                              ) : req.status === 'Approved' ? (
                                <span style={{ color: 'var(--success)', fontSize: 12 }}>
                                  Balance credited (+1)
                                </span>
                              ) : (
                                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                                  Pending approval
                                </span>
                              )}
                            </td>
                            <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                              {new Date(req.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Area: Form */}
          <div>
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Apply for Comp-Off</h2>
              </div>
              <div className="card-body">
                <form onSubmit={handleSubmit}>
                  <div className="form-group">
                    <label className="form-label">Date Worked <span className="form-required">*</span></label>
                    <input
                      type="date"
                      name="date_worked"
                      className="form-control"
                      required
                      value={form.date_worked}
                      onChange={handleChange}
                    />
                    <small style={{ color: 'var(--text-muted)', fontSize: 11, display: 'block', marginTop: 4 }}>
                      Must be a past weekend or configured public holiday on which you checked in.
                    </small>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Reason / Work Details <span className="form-required">*</span></label>
                    <textarea
                      name="reason"
                      className="form-control"
                      required
                      rows={4}
                      placeholder="e.g. Worked on emergency server maintenance or weekend project delivery support..."
                      value={form.reason}
                      onChange={handleChange}
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary btn-lg"
                    style={{ width: '100%', justifyContent: 'center', marginTop: 12 }}
                    disabled={submitting}
                  >
                    <PlusIcon style={{ width: 16, height: 16 }} /> Submit Request
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Admin View: Balances and requests from all employees */
        <div className="fade-in">
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button
              className="btn btn-secondary"
              onClick={handleExport}
              disabled={exporting}
            >
              <DownloadIcon style={{ width: 14, height: 14 }} /> {exporting ? 'Exporting...' : 'Export Report'}
            </button>
          </div>

          <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 24 }}>
            {/* Claims list */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">All Comp-Off Requests History</h2>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                {adminData.requests.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                    No employee requests found.
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Employee</th>
                          <th>Date Worked</th>
                          <th>Reason</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminData.requests.map((req) => (
                          <tr key={req.id}>
                            <td>
                              <div style={{ fontWeight: 600 }}>{req.employee_name}</div>
                            </td>
                            <td style={{ fontWeight: 700 }}>{req.date_worked}</td>
                            <td>{req.reason}</td>
                            <td>
                              <Badge status={req.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Balances list */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Employee Balances Overview</h2>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                {adminData.balances.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                    No employee balances found.
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Employee</th>
                          <th style={{ textAlign: 'center' }}>Credited</th>
                          <th style={{ textAlign: 'center' }}>Availed</th>
                          <th style={{ textAlign: 'center' }}>Remaining</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminData.balances.map((b) => (
                          <tr key={b.id}>
                            <td>
                              <div style={{ fontWeight: 600 }}>{b.employee_name}</div>
                              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{b.employee_id_code}</div>
                            </td>
                            <td style={{ textAlign: 'center' }}>{b.allocated}</td>
                            <td style={{ textAlign: 'center' }}>{b.used}</td>
                            <td style={{ textAlign: 'center', fontWeight: 700, color: 'var(--accent)' }}>{b.remaining}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
