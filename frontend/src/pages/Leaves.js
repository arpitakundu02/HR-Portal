/**
 * pages/Leaves.js
 * Tabbed leave management page.
 * Employee tabs: Apply, My History, My Balance.
 * Admin tabs: Pending Requests, All Requests, Assign Balance.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import LeaveForm from '../components/forms/LeaveForm';
import { useToast } from '../components/common/Toast';
import {
  getLeaveBalances, applyLeave, getLeaveHistory,
  getLeaveRequests, actionLeaveRequest, assignLeaveBalance, getEmployees,
} from '../services/api';
import { PlusIcon, CheckIcon, CloseIcon, SaveIcon, InboxIcon } from '../components/common/Icons';

export default function Leaves() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [tab, setTab] = useState(isAdmin ? 'pending' : 'apply');

  const ADMIN_TABS  = [
    { key: 'pending',        label: '⏳ Pending Requests' },
    { key: 'all-requests',   label: '📋 All Requests' },
    { key: 'assign-balance', label: '💳 Assign Balance' },
  ];
  const EMP_TABS = [
    { key: 'apply',          label: '➕ Apply Leave' },
    { key: 'my-history',     label: '📋 My History' },
    { key: 'my-balance',     label: '💳 My Balance' },
  ];
  const tabs = isAdmin ? [...ADMIN_TABS, ...EMP_TABS] : EMP_TABS;

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>Leave Management</h2>
          <p>Manage leave requests and balances</p>
        </div>
      </div>

      <div className="tabs">
        {tabs.map((t) => (
          <button key={t.key} className={`tab-btn ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'pending'        && <PendingRequests toast={toast} />}
      {tab === 'all-requests'   && <AllRequests     toast={toast} />}
      {tab === 'assign-balance' && <AssignBalance   toast={toast} />}
      {tab === 'apply'          && <ApplyLeave    toast={toast} />}
      {tab === 'my-history'     && <MyHistory     toast={toast} />}
      {tab === 'my-balance'     && <MyBalance     toast={toast} />}
    </div>
  );
}

function ApplyLeave({ toast }) {
  const { user, isAdmin } = useAuth();
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState([]);

  const load = useCallback(async () => {
    try {
      const params = {};
      if (isAdmin) params.employee_id = user.id;
      const { data } = await getLeaveHistory(params);
      setRecent(data.slice(0, 5));
    } catch {}
    // eslint-disable-next-line
  }, [isAdmin, user?.id]);

  useEffect(() => { load(); }, [load]);

  const handleSubmit = async (form) => {
    setLoading(true);
    try {
      await applyLeave(form);
      toast.success('Leave request submitted! Admin will review shortly.');
      setShow(false);
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Submission failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 20 }}>
        <button className="btn btn-primary" onClick={() => setShow(true)}><PlusIcon style={{ marginRight: 6 }} /> New Leave Request</button>
      </div>
      <div className="card">
        <div className="card-header"><div className="card-title">Recent Requests</div></div>
        <div className="table-wrapper">
          <table>
            <thead><tr><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Status</th><th>Applied On</th></tr></thead>
            <tbody>
              {recent.length === 0 && <tr><td colSpan={6}><div className="empty-state"><div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div><h3>No requests yet</h3></div></td></tr>}
              {recent.map((l) => (
                <tr key={l.id}>
                  <td><Badge status={l.leave_type} /></td>
                  <td className="td-muted">{l.start_date}</td>
                  <td className="td-muted">{l.end_date}</td>
                  <td>{l.days_requested}</td>
                  <td><Badge status={l.status} /></td>
                  <td className="td-muted">{new Date(l.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <Modal isOpen={show} onClose={() => setShow(false)} title="Apply for Leave" size="sm">
        <LeaveForm onSubmit={handleSubmit} onCancel={() => setShow(false)} loading={loading} />
      </Modal>
    </div>
  );
}

function MyHistory({ toast }) {
  const { user, isAdmin } = useAuth();
  const [history,    setHistory]    = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = {};
        if (typeFilter) params.leave_type = typeFilter;
        if (statusFilter) params.status = statusFilter;
        if (isAdmin) params.employee_id = user.id;
        const { data } = await getLeaveHistory(params);
        setHistory(data);
      } catch { toast.error('Failed to load history.'); }
      finally { setLoading(false); }
    })();
    // eslint-disable-next-line
  }, [typeFilter, statusFilter, isAdmin, user?.id]);

  return (
    <div>
      <div className="search-filter-row">
        <select className="form-control filter-select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All Types</option>
          <option value="APL">APL</option>
          <option value="WFH">WFH</option>
        </select>
        <select className="form-control filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="Pending">Pending</option>
          <option value="Approved">Approved</option>
          <option value="Rejected">Rejected</option>
        </select>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th><th>Applied</th></tr></thead>
              <tbody>
                {history.length === 0 && <tr><td colSpan={7}><div className="empty-state"><div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div><h3>No records found</h3></div></td></tr>}
                {history.map((l) => (
                  <tr key={l.id}>
                    <td><Badge status={l.leave_type} /></td>
                    <td className="td-muted">{l.start_date}</td>
                    <td className="td-muted">{l.end_date}</td>
                    <td>{l.days_requested}</td>
                    <td className="td-muted" style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.reason || '—'}</td>
                    <td><Badge status={l.status} /></td>
                    <td className="td-muted">{new Date(l.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Employee: My Balance ---- */
function MyBalance({ toast }) {
  const [balances, setBalances] = useState([]);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    (async () => {
      try { const { data } = await getLeaveBalances(); setBalances(data); }
      catch { toast.error('Failed to load balances.'); }
      finally { setLoading(false); }
    })();
    // eslint-disable-next-line
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="stats-grid">
      {balances.map((b) => (
        <div key={b.leave_type} className="card">
          <div style={{ fontSize: 36, marginBottom: 12 }}>{b.leave_type === 'APL' ? '📋' : '🏠'}</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            {b.leave_type === 'APL' ? 'All Purpose Leave' : 'Work From Home'}
          </div>
          <div style={{ margin: '14px 0 10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>
              <span>Used: <strong>{b.used}</strong></span>
              <span>Remaining: <strong style={{ color: b.remaining < 0 ? 'var(--danger)' : 'var(--success)' }}>{b.remaining}</strong> / {b.allocated}</span>
            </div>
            <div style={{ width: '100%', height: 8, background: 'var(--bg-elevated)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ 
                width: `${b.allocated > 0 ? Math.min(100, Math.max(0, (b.used / b.allocated) * 100)) : 0}%`, 
                height: '100%', 
                background: b.remaining < 0 ? 'var(--danger)' : 'linear-gradient(90deg, var(--accent), var(--success))',
                borderRadius: 4,
                transition: 'width 0.4s ease'
              }} />
            </div>
          </div>
          {b.remaining < 0 && (
            <div className="alert alert-warning" style={{ marginTop: 12, padding: '8px 12px', fontSize: 12 }}>
              ⚠️ Negative balance — {Math.abs(b.remaining)} day{Math.abs(b.remaining) !== 1 ? 's' : ''} overdrawn
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ---- Admin: Pending Requests ---- */
function PendingRequests({ toast }) {
  const [requests, setRequests] = useState([]);
  const [loading,  setLoading]  = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try { const { data } = await getLeaveRequests({ status: 'Pending' }); setRequests(data); }
    catch { toast.error('Failed to load requests.'); }
    finally { setLoading(false); }
    // eslint-disable-next-line
  }, []);

  useEffect(() => { load(); }, [load]);

  const action = async (id, status) => {
    try {
      await actionLeaveRequest(id, status);
      toast.success(`Request ${status.toLowerCase()}.`);
      load();
    } catch (err) { toast.error(err.response?.data?.error || 'Action failed.'); }
  };

  if (loading) return <Spinner />;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">⏳ Pending Leave Requests</div>
        <div className="card-subtitle">{requests.length} awaiting action</div>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr><th>Employee</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Applied On</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {requests.length === 0 && <tr><td colSpan={8}><div className="empty-state"><div className="empty-state-icon">🎉</div><h3>No pending requests</h3></div></td></tr>}
            {requests.map((l) => (
              <tr key={l.id}>
                <td style={{ fontWeight: 600 }}>{l.employee_name}</td>
                <td><Badge status={l.leave_type} /></td>
                <td className="td-muted">{l.start_date}</td>
                <td className="td-muted">{l.end_date}</td>
                <td>{l.days_requested}</td>
                <td className="td-muted" style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.reason || '—'}</td>
                <td className="td-muted">{new Date(l.created_at).toLocaleDateString()}</td>
                <td>
                  <div className="table-actions">
                    <button className="btn btn-success btn-sm" onClick={() => action(l.id, 'Approved')}><CheckIcon style={{ marginRight: 4 }} /> Approve</button>
                    <button className="btn btn-danger btn-sm" onClick={() => action(l.id, 'Rejected')}><CloseIcon style={{ marginRight: 4 }} /> Reject</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---- Admin: All Requests ---- */
function AllRequests({ toast }) {
  const [requests,     setRequests]     = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter,   setTypeFilter]   = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = { status: statusFilter };
        if (typeFilter) params.leave_type = typeFilter;
        const { data } = await getLeaveHistory(params);
        setRequests(data);
      } catch { toast.error('Failed to load requests.'); }
      finally { setLoading(false); }
    })();
    // eslint-disable-next-line
  }, [statusFilter, typeFilter]);

  return (
    <div>
      <div className="search-filter-row">
        <select className="form-control filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="Pending">Pending</option>
          <option value="Approved">Approved</option>
          <option value="Rejected">Rejected</option>
        </select>
        <select className="form-control filter-select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All Types</option>
          <option value="APL">APL</option>
          <option value="WFH">WFH</option>
        </select>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Employee</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Status</th><th>Actioned By</th><th>Applied</th></tr></thead>
              <tbody>
                {requests.length === 0 && <tr><td colSpan={8}><div className="empty-state"><div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div><h3>No records</h3></div></td></tr>}
                {requests.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 600 }}>{l.employee_name}</td>
                    <td><Badge status={l.leave_type} /></td>
                    <td className="td-muted">{l.start_date}</td>
                    <td className="td-muted">{l.end_date}</td>
                    <td>{l.days_requested}</td>
                    <td><Badge status={l.status} /></td>
                    <td className="td-muted">{l.actioned_by || '—'}</td>
                    <td className="td-muted">{new Date(l.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Admin: Assign Balance ---- */
function AssignBalance({ toast }) {
  const [employees, setEmployees] = useState([]);
  const [balances,  setBalances]  = useState([]);
  const [form, setForm] = useState({ employee_id: '', leave_type: 'APL', allocated: 0 });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getEmployees({ per_page: 200 }).then((r) => setEmployees(r.data.employees || []));
  }, []);

  useEffect(() => {
    if (form.employee_id) {
      getLeaveBalances({ employee_id: form.employee_id }).then((r) => setBalances(r.data));
    }
    // eslint-disable-next-line
  }, [form.employee_id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await assignLeaveBalance({ ...form, employee_id: Number(form.employee_id), allocated: Number(form.allocated) });
      toast.success('Leave balance updated successfully.');
      // Refresh balances
      const { data } = await getLeaveBalances({ employee_id: form.employee_id });
      setBalances(data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update balance.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid-2">
      <div className="card">
        <div className="card-header"><div className="card-title">💳 Assign Leave Balance</div></div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Employee <span className="form-required">*</span></label>
            <select className="form-control" value={form.employee_id} onChange={(e) => setForm((f) => ({ ...f, employee_id: e.target.value }))} required>
              <option value="">Select Employee</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.name} ({e.employee_id})</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Leave Type</label>
            <select className="form-control" value={form.leave_type} onChange={(e) => setForm((f) => ({ ...f, leave_type: e.target.value }))}>
              <option value="APL">All Purpose Leave (APL)</option>
              <option value="WFH">Work From Home (WFH)</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Days to Allocate</label>
            <input className="form-control" type="number" min={0} value={form.allocated} onChange={(e) => setForm((f) => ({ ...f, allocated: e.target.value }))} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={saving || !form.employee_id}>
            {saving ? 'Saving…' : <><SaveIcon style={{ marginRight: 6 }} /> Update Balance</>}
          </button>
        </form>
      </div>

      <div className="card">
        <div className="card-header"><div className="card-title">📊 Current Balances</div></div>
        {form.employee_id && balances.length > 0 ? balances.map((b) => (
          <div key={b.leave_type} style={{ padding: '14px 0', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>{b.leave_type === 'APL' ? 'All Purpose Leave' : 'Work From Home'}</div>
            <div style={{ display: 'flex', gap: 20, fontSize: 13, color: 'var(--text-muted)' }}>
              <span>Allocated: <strong style={{ color: 'var(--text-primary)' }}>{b.allocated}</strong></span>
              <span>Used: <strong style={{ color: 'var(--text-primary)' }}>{b.used}</strong></span>
              <span>Remaining: <strong style={{ color: b.remaining < 0 ? 'var(--danger)' : 'var(--success)' }}>{b.remaining}</strong></span>
            </div>
          </div>
        )) : (
          <div className="empty-state" style={{ padding: 30 }}>
            <div className="empty-state-icon">👤</div>
            <p>Select an employee to view their balances</p>
          </div>
        )}
      </div>
    </div>
  );
}
