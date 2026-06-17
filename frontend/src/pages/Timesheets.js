/**
 * pages/Timesheets.js
 * Daily Timesheet module.
 * - Employee view: Submit timesheet, View personal history.
 * - Supervisor/Admin view: View team timesheet, Filters by employee and date.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { submitTimesheet, getTimesheetHistory, getTeamTimesheets, getEmployees } from '../services/api';
import { useToast } from '../components/common/Toast';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { PlusIcon, UsersIcon, DownloadIcon } from '../components/common/Icons';

export default function Timesheets() {
  const { user, isAdmin } = useAuth();
  const toast = useToast();

  const [tab, setTab] = useState('overview'); // 'overview' (My Timesheets) or 'team-view'
  const [history, setHistory] = useState([]);
  const [teamHistory, setTeamHistory] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [isSupervisor, setIsSupervisor] = useState(false);

  // Filters
  const [empFilter, setEmpFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');

  // Submit Form Form
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    task_name: '',
    hours_spent: '',
    description: '',
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Fetch personal history
      const histRes = await getTimesheetHistory();
      setHistory(histRes.data);

      // 2. Fetch team history to check if supervisor (or if Admin)
      let hasTeamAccess = isAdmin;
      let teamData = [];
      try {
        const teamRes = await getTeamTimesheets();
        teamData = teamRes.data;
        if (teamRes.status === 200) {
          // If the supervisor endpoint doesn't error out, check if we have reports or data
          hasTeamAccess = true;
        }
      } catch (e) {
        // Safe to ignore if employee has no reports
      }

      setIsSupervisor(hasTeamAccess);
      setTeamHistory(teamData);

      // 3. Load employee list for filters if Admin or supervisor
      if (hasTeamAccess) {
        const empRes = await getEmployees({ per_page: 500 });
        const list = empRes.data.employees || [];
        if (isAdmin) {
          setEmployees(list);
        } else {
          // Filter to direct reports
          const reports = list.filter(e => e.manager_id === user.id);
          setEmployees(reports);
          // If no reports found but backend allowed the request, keep empty list or all in department
          if (reports.length === 0) {
            setEmployees(list.filter(e => e.id !== user.id));
          }
        }
      }
    } catch (err) {
      toast.error('Failed to load timesheet data.');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, user.id, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load team timesheets when filters change
  const loadFilteredTeamTimesheets = useCallback(async () => {
    if (!isSupervisor && !isAdmin) return;
    try {
      const params = {};
      if (empFilter) params.employee_id = empFilter;
      if (dateFilter) params.date = dateFilter;
      const res = await getTeamTimesheets(params);
      setTeamHistory(res.data);
    } catch (err) {
      toast.error('Failed to filter team timesheets.');
    }
  }, [empFilter, dateFilter, isSupervisor, isAdmin, toast]);

  useEffect(() => {
    if (tab === 'team-view') {
      loadFilteredTeamTimesheets();
    }
  }, [tab, loadFilteredTeamTimesheets]);

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.date || !form.task_name.trim() || !form.hours_spent) {
      toast.error('Date, task name, and hours spent are required.');
      return;
    }
    const hours = parseFloat(form.hours_spent);
    if (isNaN(hours) || hours <= 0 || hours > 24) {
      toast.error('Hours spent must be a valid number between 0 and 24.');
      return;
    }

    setSubmitting(true);
    try {
      await submitTimesheet({
        date: form.date,
        task_name: form.task_name.trim(),
        hours_spent: hours,
        description: form.description.trim(),
      });
      toast.success('Timesheet submitted successfully.');
      setForm({
        date: new Date().toISOString().slice(0, 10),
        task_name: '',
        hours_spent: '',
        description: '',
      });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit timesheet.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="timesheets-page fade-in">
      <div className="page-header" style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Daily Timesheets</h1>
          <p className="page-subtitle">Track daily tasks, hours worked, and submit logs</p>
        </div>

        {(isAdmin || isSupervisor) && (
          <div className="tab-buttons" style={{ display: 'flex', gap: 8 }}>
            <button
              className={`btn ${tab === 'overview' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTab('overview')}
            >
              My Timesheets
            </button>
            <button
              className={`btn ${tab === 'team-view' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTab('team-view')}
            >
              <UsersIcon style={{ width: 14, height: 14 }} /> Team Timesheets
            </button>
          </div>
        )}
      </div>

      {tab === 'overview' ? (
        <div className="grid-3-1" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
          {/* Left Column: History Table */}
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="card-title">My Timesheet History</h2>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  const params = new URLSearchParams();
                  params.append('employee_id', user.id);
                  const token = sessionStorage.getItem('hr_token');
                  fetch(`/api/exports/timesheets?${params.toString()}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                  })
                  .then(res => {
                    if (!res.ok) throw new Error('Export failed.');
                    return res.blob();
                  })
                  .then(blob => {
                    const blobUrl = window.URL.createObjectURL(blob);
                    const tempLink = document.createElement('a');
                    tempLink.href = blobUrl;
                    tempLink.setAttribute('download', `My_Timesheet_Report_${new Date().toISOString().slice(0,10)}.xlsx`);
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    document.body.removeChild(tempLink);
                  })
                  .catch(() => toast.error('Failed to export timesheets.'));
                }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                <DownloadIcon style={{ width: 12, height: 12 }} /> Export
              </button>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {history.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                  No timesheets submitted yet.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Task Name</th>
                        <th>Hours Spent</th>
                        <th>Description</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((t) => (
                        <tr key={t.id}>
                          <td style={{ fontWeight: 700 }}>{t.date}</td>
                          <td style={{ fontWeight: 600 }}>{t.task_name}</td>
                          <td>{t.hours_spent} hrs</td>
                          <td style={{ maxWidth: '250px', whiteSpace: 'normal', wordBreak: 'break-word' }}>{t.description || '—'}</td>
                          <td>
                            <Badge status={t.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Submit Form */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Submit Timesheet</h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label className="form-label">Date <span className="form-required">*</span></label>
                  <input
                    type="date"
                    name="date"
                    className="form-control"
                    required
                    value={form.date}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Task Name <span className="form-required">*</span></label>
                  <input
                    type="text"
                    name="task_name"
                    placeholder="e.g. Frontend integration, DB Schema Design..."
                    className="form-control"
                    required
                    value={form.task_name}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Hours Spent <span className="form-required">*</span></label>
                  <input
                    type="number"
                    step="0.5"
                    name="hours_spent"
                    placeholder="e.g. 4.5"
                    className="form-control"
                    required
                    value={form.hours_spent}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    name="description"
                    className="form-control"
                    rows={4}
                    placeholder="Describe what was accomplished..."
                    value={form.description}
                    onChange={handleChange}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary btn-lg"
                  style={{ width: '100%', justifyContent: 'center', marginTop: 12 }}
                  disabled={submitting}
                >
                  <PlusIcon style={{ width: 16, height: 16 }} /> {submitting ? 'Submitting...' : 'Submit Log'}
                </button>
              </form>
            </div>
          </div>
        </div>
      ) : (
        /* Supervisor/Admin View: Team timesheet table */
        <div className="fade-in">
          {/* Filters */}
          <div className="search-filter-row" style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
            <div style={{ flex: 1 }}>
              <label className="form-label" style={{ fontSize: 12 }}>Filter by Employee</label>
              <select
                className="form-control"
                value={empFilter}
                onChange={(e) => setEmpFilter(e.target.value)}
              >
                <option value="">All Employees</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>{e.name} ({e.employee_id})</option>
                ))}
              </select>
            </div>

            <div style={{ flex: 1 }}>
              <label className="form-label" style={{ fontSize: 12 }}>Filter by Date</label>
              <input
                type="date"
                className="form-control"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setEmpFilter('');
                  setDateFilter('');
                }}
              >
                Reset Filters
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  const params = new URLSearchParams();
                  if (empFilter) params.append('employee_id', empFilter);
                  if (dateFilter) {
                    params.append('start_date', dateFilter);
                    params.append('end_date', dateFilter);
                  }
                  const token = sessionStorage.getItem('hr_token');
                  fetch(`/api/exports/timesheets?${params.toString()}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                  })
                  .then(res => {
                    if (!res.ok) throw new Error('Export failed.');
                    return res.blob();
                  })
                  .then(blob => {
                    const blobUrl = window.URL.createObjectURL(blob);
                    const tempLink = document.createElement('a');
                    tempLink.href = blobUrl;
                    tempLink.setAttribute('download', `Team_Timesheet_Report_${new Date().toISOString().slice(0,10)}.xlsx`);
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    document.body.removeChild(tempLink);
                  })
                  .catch(() => toast.error('Failed to export timesheets.'));
                }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                <DownloadIcon style={{ width: 14, height: 14 }} /> Export
              </button>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Team Timesheet Logs</h2>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {teamHistory.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                  No team timesheet logs matching filters.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Employee</th>
                        <th>Task Name</th>
                        <th>Hours Spent</th>
                        <th>Description</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {teamHistory.map((t) => (
                        <tr key={t.id}>
                          <td style={{ fontWeight: 700 }}>{t.date}</td>
                          <td style={{ fontWeight: 600 }}>{t.employee_name}</td>
                          <td>{t.task_name}</td>
                          <td>{t.hours_spent} hrs</td>
                          <td style={{ maxWidth: '300px', whiteSpace: 'normal', wordBreak: 'break-word' }}>{t.description || '—'}</td>
                          <td>
                            <Badge status={t.status} />
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
      )}
    </div>
  );
}
