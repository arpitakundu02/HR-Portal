import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDirectory, getDepartments } from '../services/api';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { useToast } from '../components/common/Toast';
import { SearchIcon, DownloadIcon, UserGroupIcon } from '../components/common/Icons';

export default function Directory() {
  const navigate = useNavigate();
  const toast = useToast();

  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');

  useEffect(() => {
    // Fetch departments for dropdown
    getDepartments()
      .then(res => setDepartments(res.data))
      .catch(() => toast.error('Failed to load departments.'));
  }, [toast]);

  useEffect(() => {
    setLoading(true);
    const params = {};
    if (search.trim()) params.search = search.trim();
    if (deptFilter) params.department_id = deptFilter;

    getDirectory(params)
      .then(res => {
        setEmployees(res.data.employees);
      })
      .catch(() => toast.error('Failed to load contact directory.'))
      .finally(() => setLoading(false));
  }, [search, deptFilter, toast]);

  const handleExport = () => {
    const params = new URLSearchParams();
    if (search.trim()) params.append('search', search.trim());
    if (deptFilter) params.append('department_id', deptFilter);

    const token = sessionStorage.getItem('hr_token');

    fetch(`/api/exports/directory?${params.toString()}`, {
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
        tempLink.setAttribute('download', `Contact_Directory_${new Date().toISOString().slice(0, 10)}.xlsx`);
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
      })
      .catch(() => toast.error('Failed to export contact directory.'));
  };

  return (
    <div className="fade-in" style={{ paddingBottom: 40 }}>
      {/* Title Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 24, fontWeight: 800 }}>
            <UserGroupIcon style={{ width: 28, height: 28 }} /> Contact Directory
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Find and connect with your colleagues.</p>
        </div>
        <button className="btn btn-primary" onClick={handleExport}>
          <DownloadIcon style={{ marginRight: 6 }} /> Export Directory
        </button>
      </div>

      {/* Filter Row */}
      <div className="card" style={{ padding: 16, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div className="search-input-wrapper" style={{ flex: 1, minWidth: 260, position: 'relative' }}>
            <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              <SearchIcon style={{ width: 16, height: 16 }} />
            </span>
            <input
              type="text"
              className="form-control"
              placeholder="Search by name, ID, phone, or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 36, width: '100%' }}
            />
          </div>
          <select
            className="form-control"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            style={{ width: 220 }}
          >
            <option value="">All Departments</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Directory Grid */}
      {loading ? (
        <Spinner />
      ) : employees.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
          No employees found matching the filters.
        </div>
      ) : (
        <div className="directory-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 20 }}>
          {employees.map(emp => {
            const initials = emp.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
            return (
              <div
                key={emp.id}
                className="card directory-card"
                onClick={() => navigate(`/employees/${emp.id}`)}
                style={{
                  padding: 20,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                  border: '1px solid var(--border)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {/* Photo or Initials */}
                <div style={{ position: 'relative', marginBottom: 12 }}>
                  {emp.photo_url ? (
                    <img
                      src={emp.photo_url}
                      alt={emp.name}
                      style={{ width: 72, height: 72, borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--border)' }}
                    />
                  ) : (
                    <div style={{ width: 72, height: 72, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, fontWeight: 700, border: '2px solid var(--border)' }}>
                      {initials}
                    </div>
                  )}
                </div>

                <h3 style={{ margin: '0 0 4px 0', fontSize: 16, fontWeight: 700 }}>{emp.name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 12, margin: '0 0 4px 0' }}>
                  <strong>{emp.employee_id}</strong>
                </p>
                <p style={{ color: 'var(--text-secondary)', fontSize: 12, margin: '0 0 12px 0' }}>
                  {emp.rank || 'Designation N/A'} &middot; {emp.department_name || 'No Dept'}
                </p>

                <div style={{ width: '100%', borderTop: '1px solid var(--border)', paddingTop: 12, display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-start', fontSize: 12 }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Email:</span>{' '}
                    <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{emp.email}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Phone:</span>{' '}
                    <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{emp.phone_number || '—'}</span>
                  </div>
                  <div style={{ marginTop: 6, alignSelf: 'center' }}>
                    <Badge status={emp.availability_status} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
