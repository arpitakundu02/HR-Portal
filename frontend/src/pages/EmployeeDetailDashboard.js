/**
 * pages/EmployeeDetailDashboard.js
 * Dedicated Employee Detail Dashboard for Admin and Line Managers.
 */
import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import { getEmployeeDashboardDetails, uploadPhoto, deletePhoto } from '../services/api';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import {
  ArrowLeftIcon, CameraIcon, CalendarIcon, CheckIcon, CloseIcon,
  DocumentTextIcon, UsersIcon, ClockIcon, EditIcon, TrashIcon, DownloadIcon
} from '../components/common/Icons';

export default function EmployeeDetailDashboard() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { isAdmin, user } = useAuth();
  const isManager = user?.is_line_manager === true;
  const currentUserId = user?.id;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  const loadDetails = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getEmployeeDashboardDetails(id);
      setData(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to load employee details.');
      navigate('/employees');
    } finally {
      setLoading(false);
    }
  }, [id, toast, navigate]);

  useEffect(() => {
    loadDetails();
  }, [loadDetails]);

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('photo', file);
    setUploadingPhoto(true);
    try {
      const uploadRes = await uploadPhoto(id, fd);
      toast.success('Profile photo updated successfully.');
      setData(prev => ({
        ...prev,
        profile: {
          ...prev.profile,
          photo_url: uploadRes.data.photo_url
        }
      }));
    } catch (err) {
      toast.error(err.response?.data?.error || 'Photo upload failed.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleDeletePhoto = async () => {
    if (!window.confirm("Are you sure you want to delete this profile photo?")) return;
    try {
      await deletePhoto(id);
      toast.success('Profile photo deleted.');
      setData(prev => ({
        ...prev,
        profile: {
          ...prev.profile,
          photo_url: null
        }
      }));
    } catch (err) {
      toast.error(err.response?.data?.error || 'Delete photo failed.');
    }
  };

  if (loading) return <Spinner />;
  if (!data) return <p style={{ textAlign: 'center', padding: 24 }}>No employee data loaded.</p>;

  const { profile, attendance_history, task_history, timesheet_history, leave_summary } = data;

  const initials = profile.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase();

  // Recharts: Attendance Stats
  const totalDays = 15;
  const presentCount = attendance_history.filter(a => a.check_in && a.working_hours > 0).length;
  const absentCount = Math.max(0, totalDays - presentCount);
  const workingHoursData = attendance_history
    .slice(0, 10)
    .reverse()
    .map(a => ({
      date: new Date(a.date).toLocaleDateString([], { month: 'short', day: 'numeric' }),
      hours: a.working_hours || 0
    }));

  const attendancePieData = [
    { name: 'Present Days', value: presentCount, color: '#10b981' },
    { name: 'Absent/Leave Days', value: absentCount, color: '#f43f5e' }
  ].filter(d => d.value > 0);

  return (
    <div className="fade-in" style={{ paddingBottom: 40 }}>
      {/* Header Back Link */}
      <div style={{ marginBottom: 20 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
          <ArrowLeftIcon style={{ marginRight: 6 }} /> Back
        </button>
      </div>

      {/* Employee Top Profile Widget */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 24, padding: '24px 30px', marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative' }}>
          {profile.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.name}
              style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', border: '3px solid var(--border)' }}
            />
          ) : (
            <div style={{ width: 100, height: 100, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, fontWeight: 700, border: '3px solid var(--border)' }}>
              {initials}
            </div>
          )}
          {(isAdmin || currentUserId === profile.id) && profile.photo_url && (
            <button
              onClick={handleDeletePhoto}
              title="Delete photo"
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                backgroundColor: '#ef4444',
                color: '#fff',
                width: 32,
                height: 32,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                padding: 0
              }}
            >
              <TrashIcon style={{ width: 16, height: 16 }} />
            </button>
          )}
          {(isAdmin || currentUserId === profile.id) && (
            <label style={{ position: 'absolute', bottom: 0, right: 0, backgroundColor: 'var(--accent)', color: '#fff', width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 5px rgba(0,0,0,0.2)', margin: 0 }}>
              {uploadingPhoto ? '...' : <CameraIcon style={{ width: 16, height: 16 }} />}
              <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: 'none' }} disabled={uploadingPhoto} />
            </label>
          )}
        </div>

        <div>
          <h2 style={{ margin: 0, fontWeight: 800, fontSize: 24 }}>{profile.name}</h2>
          <p style={{ margin: '4px 0 12px 0', color: 'var(--text-secondary)', fontSize: 15 }}>
            {profile.rank || 'Designation N/A'} &middot; {profile.department_name || 'No Department'}
          </p>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Badge status={profile.is_line_manager ? 'Line Manager' : profile.role} />
            <Badge status={profile.is_active ? 'Active' : 'Inactive'} />
            <Badge status={profile.availability_status} />
            <span className="badge badge-apl">{profile.employee_id}</span>
            {profile.manager_name && (
              <span className="badge" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                Manager: {profile.manager_name}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid var(--border)', marginBottom: 24, paddingBottom: 8 }}>
        {[
          { id: 'overview', label: '👤 Profile & Leaves' },
          { id: 'attendance', label: '📅 Attendance History' },
          { id: 'tasks', label: '📋 Task Log' },
          { id: 'timesheets', label: '⏱️ Timesheets' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 20px',
              fontWeight: 600,
              fontSize: 14,
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              background: activeTab === tab.id ? 'var(--accent)' : 'transparent',
              color: activeTab === tab.id ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.2s ease'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* About Me Card */}
          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ marginTop: 0, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>📝 About Me</h3>
            <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-primary)', fontSize: 14 }}>
              {profile.bio || 'No bio submitted yet.'}
            </p>
          </div>

          <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            {/* Profile details */}
            <div className="card" style={{ padding: 20 }}>
              <h3 style={{ marginTop: 0, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>Profile Details</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div><strong>Email:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.email}</span></div>
                <div><strong>Phone Number:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.phone_number || '—'}</span></div>
                <div><strong>Status:</strong> <span style={{ marginLeft: 6 }}><Badge status={profile.availability_status} /></span></div>
                <div><strong>Father's Name:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.fathers_name || '—'}</span></div>
                <div><strong>Date of Birth:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.dob || '—'}</span></div>
                <div><strong>Blood Group:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.blood_group || '—'}</span></div>
                <div><strong>Gender:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.gender || 'Male'}</span></div>
                <div><strong>Aadhar Number:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.aadhar_number || '—'}</span></div>
                <div><strong>Date of Joining:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.date_of_joining || '—'}</span></div>
                <div><strong>Emergency Contact:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.emergency_contact || '—'}</span></div>
                <div><strong>Current Address:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.current_address || '—'}</span></div>
                <div><strong>Permanent Address:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.permanent_address || '—'}</span></div>
                <div><strong>Resume:</strong> <span style={{ color: 'var(--text-secondary)' }}>{profile.resume_url ? <a href={`${profile.resume_url}?auth_token=${sessionStorage.getItem('hr_token')}`} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', padding: '2px 8px', fontSize: 12, marginLeft: 6 }}><DownloadIcon style={{ width: 12, height: 12, marginRight: 4 }} /> Download Resume</a> : 'No approved resume uploaded'}</span></div>
              </div>
            </div>

            {/* Leaves Details */}
            <div className="card" style={{ padding: 20 }}>
              <h3 style={{ marginTop: 0, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>Leaves Summary</h3>
              {leave_summary.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No leave balance records found.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  {leave_summary.map(balance => {
                    const percent = balance.allocated > 0 ? Math.min(100, Math.round((balance.used / balance.allocated) * 100)) : 0;
                    return (
                      <div key={balance.id} className="card" style={{ padding: 16, backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontWeight: 700 }}>
                          <span>{balance.leave_type === 'APL' ? 'Annual Privilege Leave (APL)' : 'Work From Home (WFH)'}</span>
                          <span>{balance.used} / {balance.allocated} Days Taken</span>
                        </div>
                        <div style={{ width: '100%', height: 10, backgroundColor: 'var(--border)', borderRadius: 5, overflow: 'hidden' }}>
                          <div style={{ width: `${percent}%`, height: '100%', backgroundColor: balance.leave_type === 'APL' ? '#f59e0b' : '#3b82f6', borderRadius: 5 }} />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
                          <span>Remaining: {balance.remaining} days</span>
                          <span>{percent}% Used</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Professional Profile Card */}
            <div className="card" style={{ padding: 20, gridColumn: 'span 2' }}>
              <h3 style={{ marginTop: 0, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>Professional Profile</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <strong style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Experience Summary</strong>
                  <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-primary)', fontSize: 14 }}>
                    {profile.experience_summary || 'No experience summary submitted yet.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'attendance' && (
        <div className="grid-2" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 24 }}>
          {/* Attendance Log */}
          <div className="card" style={{ padding: 0 }}>
            <div className="card-header" style={{ padding: 20, borderBottom: '1px solid var(--border)' }}><h3 className="card-title" style={{ margin: 0 }}>Attendance Log</h3></div>
            <div className="table-wrapper">
              <table style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Check In</th>
                    <th>Check Out</th>
                    <th>Hours</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attendance_history.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>No attendance records found.</td>
                    </tr>
                  ) : (
                    attendance_history.map(att => (
                      <tr key={att.id}>
                        <td>{att.date}</td>
                        <td>{att.check_in ? new Date(att.check_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                        <td>{att.check_out ? new Date(att.check_out).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                        <td>{att.working_hours || 0} hrs</td>
                        <td>
                          <Badge status={att.attendance_status} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Attendance Charts */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="card" style={{ padding: 20 }}>
              <h3 style={{ marginTop: 0, marginBottom: 12 }}>Attendance Breakdown</h3>
              <div style={{ height: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                {attendancePieData.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', textAlign: 'center', paddingTop: 40 }}>No breakdown data.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={attendancePieData} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value" nameKey="name">
                        {attendancePieData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="card" style={{ padding: 20 }}>
              <h3 style={{ marginTop: 0, marginBottom: 12 }}>Working Hours (Last 10 Days)</h3>
              <div style={{ height: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                {workingHoursData.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', textAlign: 'center', paddingTop: 40 }}>No working hours data.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={workingHoursData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="hours" fill="#6366f1" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ marginTop: 0, marginBottom: 16 }}>Task History</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {task_history.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No tasks assigned to this employee.</p>
            ) : (
              task_history.map(task => (
                <div key={task.id} className="card" style={{ padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{task.title}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{task.description || 'No description provided.'}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                      Due: {task.due_date || 'No due date'} &middot; Assigned by: {task.assigned_by_name || 'System'}
                    </div>
                  </div>
                  <div>
                    <Badge status={task.status === 'Completed' ? 'Approved' : task.status === 'In Progress' ? 'Pending' : 'Inactive'} label={task.status} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'timesheets' && (
        <div className="card" style={{ padding: 0 }}>
          <div className="card-header" style={{ padding: 20, borderBottom: '1px solid var(--border)' }}><h3 className="card-title" style={{ margin: 0 }}>Timesheet Logs</h3></div>
          <div className="table-wrapper">
            <table style={{ width: '100%' }}>
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
                {timesheet_history.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>No timesheets logged.</td>
                  </tr>
                ) : (
                  timesheet_history.map(ts => (
                    <tr key={ts.id}>
                      <td>{ts.date}</td>
                      <td style={{ fontWeight: 600 }}>{ts.task_name}</td>
                      <td>{ts.hours_spent} hrs</td>
                      <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ts.description || '—'}</td>
                      <td>
                        <Badge status={ts.status} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
