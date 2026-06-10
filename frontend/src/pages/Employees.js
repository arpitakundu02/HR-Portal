/**
 * pages/Employees.js
 * Employee directory with search, department filter, and pagination.
 * Admin: Full CRUD + resume upload. Employee: Read-only directory.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import Pagination from '../components/common/Pagination';
import EmployeeForm from '../components/forms/EmployeeForm';
import { useToast } from '../components/common/Toast';
import {
  getEmployees, createEmployee, updateEmployee, deleteEmployee,
  getDepartments, uploadResume,
} from '../services/api';
import { EditIcon, TrashIcon, PaperclipIcon, PlusIcon, UploadIcon, UsersIcon } from '../components/common/Icons';

export default function Employees() {
  const { isAdmin } = useAuth();
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
          <h2>{isAdmin ? 'Employee Directory' : 'Team Directory'}</h2>
          <p>{total} {isAdmin ? 'employee' : 'team member'}{total !== 1 ? 's' : ''} found</p>
        </div>
        {isAdmin && (
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
            placeholder={isAdmin ? "Search by name, ID or email…" : "Search by name or email…"}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {isAdmin && (
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
                  {isAdmin ? (
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Email</th>
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
                      <td colSpan={isAdmin ? 9 : 5}>
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
                      {isAdmin ? (
                        <>
                          <td className="td-muted">{emp.employee_id}</td>
                          <td style={{ fontWeight: 600 }}>{emp.name}</td>
                          <td className="td-muted">{emp.email}</td>
                          <td className="td-muted">{emp.department_name || '—'}</td>
                          <td className="td-muted">{emp.rank || '—'}</td>
                          <td><Badge status={emp.role} /></td>
                          <td className="td-muted">{emp.date_of_joining || '—'}</td>
                          <td><Badge status={emp.is_active ? 'Active' : 'Inactive'} /></td>
                          <td>
                            <div className="table-actions">
                              <button className="btn btn-secondary btn-sm" onClick={() => { setEditTarget(emp); setShowForm(true); }} title="Edit"><EditIcon /></button>
                              <button className="btn btn-ghost btn-sm" onClick={() => setShowResume(emp)} title="Upload Resume"><PaperclipIcon /></button>
                              <button className="btn btn-danger btn-sm" onClick={() => setShowDelete(emp)} title="Deactivate"><TrashIcon /></button>
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          <td style={{ fontWeight: 600 }}>{emp.name}</td>
                          <td className="td-muted">{emp.rank || emp.role}</td>
                          <td className="td-muted">{emp.department_name || '—'}</td>
                          <td className="td-muted">{emp.email}</td>
                          <td>
                            <Badge
                              status={
                                emp.availability_status === 'Work From Home' ? 'WFH' :
                                emp.availability_status === 'On Leave' ? 'Leave' :
                                emp.availability_status === 'Present' ? 'Active' : 'Inactive'
                              }
                              label={emp.availability_status}
                            />
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
    </div>
  );
}
