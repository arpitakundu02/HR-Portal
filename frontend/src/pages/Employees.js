import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import Pagination from '../components/common/Pagination';
import EmployeeForm from '../components/forms/EmployeeForm';
import { useToast } from '../components/common/Toast';
import {
  getEmployees, createEmployee, updateEmployee, deleteEmployee,
  getDepartments, uploadResume, getEmployeeDashboardDetails,
} from '../services/api';
import { EditIcon, TrashIcon, PaperclipIcon, PlusIcon, UploadIcon, UsersIcon } from '../components/common/Icons';

export default function Employees() {
  const navigate = useNavigate();
  const { isAdmin, user } = useAuth();
  const isManager = user?.is_line_manager === true;
  const canManage = isAdmin || isManager;
  const toast       = useToast();

  const [employees,    setEmployees]    = useState([]);
  const [departments,  setDepartments]  = useState([]);
  const [total,        setTotal]        = useState(0);
  const [page,         setPage]         = useState(1);
  const [pages,        setPages]        = useState(1);
  const [search,       setSearch]       = useState('');
  const [deptFilter,   setDeptFilter]   = useState('');
  const [loading,      setLoading]      = useState(true);
  const [formLoading,  setFormLoading]  = useState(false);

  // Modals
  const [showForm,     setShowForm]     = useState(false);
  const [editTarget,   setEditTarget]   = useState(null);
  const [showDelete,   setShowDelete]   = useState(null);
  const [showResume,   setShowResume]   = useState(null);
  const [resumeFile,   setResumeFile]   = useState(null);
  const [quickProfile, setQuickProfile] = useState(null);
  const [selectedEmpDetails, setSelectedEmpDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const handleOpenQuickProfile = async (emp) => {
    setDetailsLoading(true);
    setSelectedEmpDetails(null);
    setQuickProfile(emp);
    try {
      const { data } = await getEmployeeDashboardDetails(emp.id);
      setSelectedEmpDetails(data);
    } catch {
      toast.error('Failed to load employee details.');
      setQuickProfile(null);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleOpenFullProfile = () => {
    const id = quickProfile.id;
    setQuickProfile(null);
    navigate(`/employees/${id}`);
  };

  useEffect(() => { getDepartments().then((r) => setDepartments(r.data)); }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getEmployees({
        page, per_page: 15,
        search: search || undefined,
        department: deptFilter || undefined,
      });
      setEmployees(data.employees);
      setTotal(data.total);
      setPages(data.pages);
    } catch {
      toast.error('Failed to load employees.');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line
  }, [page, search, deptFilter]);

  useEffect(() => { load(); }, [load]);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => setPage(1), 400);
    return () => clearTimeout(t);
  }, [search, deptFilter]);

  const handleSubmit = async (formData) => {
    setFormLoading(true);
    try {
      if (editTarget) {
        await updateEmployee(editTarget.id, formData);
        toast.success('Employee updated successfully.');
      } else {
        await createEmployee(formData);
        toast.success('Employee created successfully.');
      }
      setShowForm(false);
      setEditTarget(null);
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Operation failed.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteEmployee(showDelete.id);
      toast.success(`${showDelete.name} has been deactivated.`);
      setShowDelete(null);
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Delete failed.');
    }
  };

  const handleResumeUpload = async () => {
    if (!resumeFile) return;
    const fd = new FormData();
    fd.append('resume', resumeFile);
    try {
      await uploadResume(showResume.id, fd);
      toast.success('Resume uploaded successfully.');
      setShowResume(null);
      setResumeFile(null);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed.');
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h2>{canManage ? 'Employee Directory' : 'Team Directory'}</h2>
          <p>{total} {canManage ? 'employee' : 'team member'}{total !== 1 ? 's' : ''} found</p>
        </div>
        {canManage && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => { setEditTarget(null); setShowForm(true); }}>
              <PlusIcon style={{ marginRight: 6 }} /> Add Employee
            </button>
          </div>
        )}
      </div>

      {/* Search & Filter */}
      <div className="search-filter-row">
        <div className="search-input-wrap">
          <span className="search-icon">🔍</span>
          <input
            className="form-control"
            placeholder={canManage ? "Search by name, ID or email…" : "Search by name or email…"}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {canManage && (
          <select
            className="form-control filter-select"
            value={deptFilter}
            onChange={(e) => { setDeptFilter(e.target.value); setPage(1); }}
          >
            <option value="">All Departments</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        )}
      </div>

      {/* Table */}
      <div className="card">
        {loading ? <Spinner /> : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  {canManage ? (
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Phone</th>
                      <th>Department</th>
                      <th>Rank</th>
                      <th>Role</th>
                      <th>Joined</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  ) : (
                    <tr>
                      <th>Name</th>
                      <th>Designation / Role</th>
                      <th>Department</th>
                      <th>Contact Information</th>
                      <th>Availability Status</th>
                    </tr>
                  )}
                </thead>
                <tbody>
                  {employees.length === 0 && (
                    <tr>
                      <td colSpan={canManage ? 10 : 5}>
                        <div className="empty-state">
                          <div className="empty-state-icon">
                            <UsersIcon style={{ width: 48, height: 48 }} />
                          </div>
                          <h3>No employees found</h3>
                        </div>
                      </td>
                    </tr>
                  )}
                  {employees.map((emp) => (
                    <tr key={emp.id}>
                      {canManage ? (
                        <>
                          <td className="td-muted">{emp.employee_id}</td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              {emp.photo_url ? (
                                <img src={emp.photo_url} alt={emp.name} style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover' }} />
                              ) : (
                                <div style={{ width: 32, height: 32, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: 12 }}>
                                  {emp.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                                </div>
                              )}
                              <span
                                style={{ fontWeight: 600, cursor: 'pointer', color: 'var(--accent)' }}
                                onClick={() => {
                                  if (canManage) {
                                    handleOpenQuickProfile(emp);
                                  } else {
                                    navigate(`/employees/${emp.id}`);
                                  }
                                }}
                              >
                                {emp.name}
                              </span>
                            </div>
                          </td>
                          <td className="td-muted">{emp.email}</td>
                          <td className="td-muted">{emp.phone_number || '—'}</td>
                          <td className="td-muted">{emp.department_name || '—'}</td>
                          <td className="td-muted">{emp.rank || '—'}</td>
                          <td><Badge status={emp.is_line_manager ? 'Line Manager' : emp.role} /></td>
                          <td className="td-muted">{emp.date_of_joining || '—'}</td>
                          <td><Badge status={emp.is_active ? 'Active' : 'Inactive'} /></td>
                          <td>
                            <div className="table-actions">
                              {emp.role !== 'Admin' && (
                                <>
                                  <button className="btn btn-secondary btn-sm" onClick={() => { setEditTarget(emp); setShowForm(true); }} title="Edit"><EditIcon /></button>
                                  <button className="btn btn-ghost btn-sm" onClick={() => setShowResume(emp)} title="Upload Resume"><PaperclipIcon /></button>
                                  <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(emp)} title="Deactivate"><TrashIcon /></button>
                                </>
                              )}
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              {emp.photo_url ? (
                                <img src={emp.photo_url} alt={emp.name} style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover' }} />
                              ) : (
                                <div style={{ width: 32, height: 32, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: 12 }}>
                                  {emp.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                                </div>
                              )}
                              <span style={{ fontWeight: 600 }}>{emp.name}</span>
                            </div>
                          </td>
                          <td className="td-muted">{emp.rank || (emp.is_line_manager ? 'Line Manager' : emp.role)}</td>
                          <td className="td-muted">{emp.department_name || '—'}</td>
                          <td className="td-muted">
                            <div>{emp.email}</div>
                            {emp.phone_number && <div style={{ fontSize: '12px', marginTop: '2px' }}>{emp.phone_number}</div>}
                          </td>
                          <td>
                            <Badge
                              status={
                                emp.availability_status === 'Work From Home' ? 'WFH' :
                                emp.availability_status === 'On Leave' ? 'Leave' :
                                emp.availability_status === 'Present' ? 'Active' : 'Inactive'
                              }
                              label={emp.availability_status}
                            />
                            {emp.upcoming_leave && (
                              <div className="upcoming-leave-lbl" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                Upcoming {emp.upcoming_leave.leave_type} in {emp.upcoming_leave.days_until_start} {emp.upcoming_leave.days_until_start === 1 ? 'day' : 'days'}
                              </div>
                            )}
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pages={pages} onPageChange={setPage} />
          </>
        )}
      </div>

      {/* Add/Edit Modal */}
      <Modal
        isOpen={showForm}
        onClose={() => { setShowForm(false); setEditTarget(null); }}
        title={editTarget ? `Edit: ${editTarget.name}` : 'Add New Employee'}
        size="lg"
      >
        <EmployeeForm
          initialData={editTarget}
          departments={departments}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditTarget(null); }}
          loading={formLoading}
        />
      </Modal>

      {/* Delete Confirm Modal */}
      <Modal isOpen={!!showDelete} onClose={() => setShowDelete(null)} title="Deactivate Employee" size="sm">
        <p style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>
          Are you sure you want to deactivate <strong>{showDelete?.name}</strong>?
          This will revoke their access to the portal.
        </p>
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => setShowDelete(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete}><TrashIcon style={{ marginRight: 6 }} /> Deactivate</button>
        </div>
      </Modal>

      {/* Resume Upload Modal */}
      <Modal isOpen={!!showResume} onClose={() => { setShowResume(null); setResumeFile(null); }} title={`Upload Resume — ${showResume?.name}`} size="sm">
        <div className="form-group">
          <label className="form-label">Select File (PDF, DOC, DOCX — max 5MB)</label>
          <input className="form-control" type="file" accept=".pdf,.doc,.docx"
            onChange={(e) => setResumeFile(e.target.files[0])} />
        </div>
        {showResume?.resume_url && (
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
            Current: <a href={showResume.resume_url} target="_blank" rel="noreferrer">View existing resume</a>
          </p>
        )}
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => { setShowResume(null); setResumeFile(null); }}>Cancel</button>
          <button className="btn btn-primary" onClick={handleResumeUpload} disabled={!resumeFile}><UploadIcon style={{ marginRight: 6 }} /> Upload</button>
        </div>
      </Modal>

      {/* Quick Profile Modal */}
      <Modal
        isOpen={!!quickProfile}
        onClose={() => setQuickProfile(null)}
        title="Quick Employee Profile"
        size="lg"
        footer={
          !detailsLoading && selectedEmpDetails ? (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, width: '100%' }}>
              <button className="btn btn-secondary" onClick={() => setQuickProfile(null)}>Close</button>
              <button className="btn btn-primary" onClick={handleOpenFullProfile}>Open Full Profile</button>
            </div>
          ) : null
        }
      >
        {detailsLoading || !selectedEmpDetails ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
            <Spinner />
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Header portion inside modal */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 20, borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
              {selectedEmpDetails.profile.photo_url ? (
                <img src={selectedEmpDetails.profile.photo_url} alt={selectedEmpDetails.profile.name} style={{ width: 64, height: 64, borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--border)' }} />
              ) : (
                <div style={{ width: 64, height: 64, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 700, border: '2px solid var(--border)' }}>
                  {selectedEmpDetails.profile.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
              )}
              <div>
                <h3 style={{ margin: 0, fontWeight: 800, fontSize: 18 }}>{selectedEmpDetails.profile.name}</h3>
                <p style={{ margin: '2px 0 6px 0', color: 'var(--text-secondary)', fontSize: 13 }}>
                  {selectedEmpDetails.profile.rank || 'Designation N/A'} &middot; {selectedEmpDetails.profile.department_name || 'No Department'}
                </p>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <Badge status={selectedEmpDetails.profile.is_line_manager ? 'Line Manager' : selectedEmpDetails.profile.role} />
                  <Badge status={selectedEmpDetails.profile.is_active ? 'Active' : 'Inactive'} />
                  <Badge status={selectedEmpDetails.profile.availability_status} />
                  <span className="badge badge-apl" style={{ fontSize: 11 }}>{selectedEmpDetails.profile.employee_id}</span>
                </div>
              </div>
            </div>

            {/* About Me Card */}
            <div className="card" style={{ padding: 16 }}>
              <h4 style={{ marginTop: 0, marginBottom: 10, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>📝 About Me</h4>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.5, color: 'var(--text-primary)', fontSize: 13.5 }}>
                {selectedEmpDetails.profile.bio || 'No bio submitted yet.'}
              </p>
            </div>

            {/* Profile details and leaves */}
            <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <div className="card" style={{ padding: 16 }}>
                <h4 style={{ marginTop: 0, marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>👤 Profile Details</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13 }}>
                  <div><strong>Email:</strong> <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>{selectedEmpDetails.profile.email}</span></div>
                  <div><strong>Phone Number:</strong> <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>{selectedEmpDetails.profile.phone_number || '—'}</span></div>
                  <div><strong>Gender:</strong> <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>{selectedEmpDetails.profile.gender || 'Male'}</span></div>
                  <div><strong>Date of Joining:</strong> <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>{selectedEmpDetails.profile.date_of_joining || '—'}</span></div>
                </div>
              </div>

              <div className="card" style={{ padding: 16 }}>
                <h4 style={{ marginTop: 0, marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>📊 Leaves Summary</h4>
                {selectedEmpDetails.leave_summary.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: 0 }}>No leave balance records found.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {selectedEmpDetails.leave_summary.map(balance => {
                      const percent = balance.allocated > 0 ? Math.min(100, Math.round((balance.used / balance.allocated) * 100)) : 0;
                      return (
                        <div key={balance.id} style={{ fontSize: 12.5 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontWeight: 600 }}>
                            <span>{balance.leave_type === 'APL' ? 'Annual Privilege Leave (APL)' : 'Work From Home (WFH)'}</span>
                            <span>{balance.used} / {balance.allocated} Days</span>
                          </div>
                          <div style={{ width: '100%', height: 6, backgroundColor: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ width: `${percent}%`, height: '100%', backgroundColor: balance.leave_type === 'APL' ? '#f59e0b' : '#3b82f6', borderRadius: 3 }} />
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 11, color: 'var(--text-secondary)' }}>
                            <span>Remaining: {balance.remaining} days</span>
                            <span>{percent}% Used</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
