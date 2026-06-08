/**
 * pages/Profile.js
 * View and edit own profile. Admin can edit all fields; Employee can edit address/emergency.
 * Also includes a change-password section and resume download link.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Spinner from '../components/common/Spinner';
import Badge from '../components/common/Badge';
import { useToast } from '../components/common/Toast';
import { getMe, updateEmployee, uploadResume } from '../services/api';
import { EditIcon, DownloadIcon, UploadIcon, SaveIcon, LockIcon } from '../components/common/Icons';

export default function Profile() {
  const { user, updateUser, isAdmin } = useAuth();
  const toast = useToast();

  const [profile,  setProfile]  = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Editable fields
  const [form, setForm] = useState({
    address: '', current_address: '', permanent_address: '', emergency_contact: '',
  });

  const [uploadingResume, setUploadingResume] = useState(false);

  const handleResumeChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('resume', file);
    setUploadingResume(true);
    try {
      await uploadResume(profile.id, fd);
      toast.success('Resume uploaded successfully.');
      const { data } = await getMe();
      setProfile(data);
      updateUser({ ...user, ...data });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed.');
    } finally {
      setUploadingResume(false);
    }
  };

  // Password change
  const [pwForm,    setPwForm]    = useState({ password: '', confirm: '' });
  const [pwSaving,  setPwSaving]  = useState(false);
  const [pwVisible, setPwVisible] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getMe();
        setProfile(data);
        setForm({
          address:           data.address           || '',
          current_address:   data.current_address   || '',
          permanent_address: data.permanent_address || '',
          emergency_contact: data.emergency_contact || '',
        });
      } catch { toast.error('Failed to load profile.'); }
      finally { setLoading(false); }
    })();
    // eslint-disable-next-line
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateEmployee(profile.id, form);
      const { data } = await getMe();
      setProfile(data);
      updateUser({ ...user, ...data });
      toast.success('Profile updated successfully.');
      setEditMode(false);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Update failed.');
    } finally { setSaving(false); }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (pwForm.password !== pwForm.confirm) {
      toast.error('Passwords do not match.');
      return;
    }
    if (pwForm.password.length < 6) {
      toast.error('Password must be at least 6 characters.');
      return;
    }
    setPwSaving(true);
    try {
      await updateEmployee(profile.id, { password: pwForm.password });
      toast.success('Password changed successfully.');
      setPwForm({ password: '', confirm: '' });
      setPwVisible(false);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Password change failed.');
    } finally { setPwSaving(false); }
  };

  if (loading) return <Spinner />;
  if (!profile) return null;

  const initials = profile.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase();

  const InfoRow = ({ label, value }) => (
    <div className="info-item">
      <div className="info-label">{label}</div>
      <div className="info-value">{value || '—'}</div>
    </div>
  );

  return (
    <div className="fade-in">
      {/* Profile Header */}
      <div className="profile-header">
        <div className="profile-avatar">{initials}</div>
        <div className="profile-meta">
          <h2>{profile.name}</h2>
          <p>{profile.rank || profile.role} · {profile.department_name || 'No Department'}</p>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <Badge status={profile.role} />
            <Badge status={profile.is_active ? 'Active' : 'Inactive'} />
            <span className="badge badge-apl">{profile.employee_id}</span>
          </div>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          {!editMode && (
            <button className="btn btn-primary" onClick={() => setEditMode(true)}><EditIcon style={{ marginRight: 6 }} /> Edit Profile</button>
          )}
        </div>
      </div>

      <div className="grid-2" style={{ gap: 24 }}>
        {/* Personal Information */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">👤 Personal Information</div>
          </div>
          <div className="info-grid">
            <InfoRow label="Full Name"      value={profile.name} />
            <InfoRow label="Father's Name"  value={profile.fathers_name} />
            <InfoRow label="Date of Birth"  value={profile.dob} />
            <InfoRow label="Blood Group"    value={profile.blood_group} />
            <InfoRow label="Email"          value={profile.email} />
            <InfoRow label="Emergency Contact" value={profile.emergency_contact} />
          </div>
        </div>

        {/* Employment Information */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🏢 Employment Details</div>
          </div>
          <div className="info-grid">
            <InfoRow label="Employee ID"   value={profile.employee_id} />
            <InfoRow label="Department"    value={profile.department_name} />
            <InfoRow label="Designation"   value={profile.rank} />
            <InfoRow label="Date of Joining" value={profile.date_of_joining} />
            {isAdmin && <InfoRow label="Salary"  value={profile.salary ? `₹${Number(profile.salary).toLocaleString()}` : '—'} />}
            {isAdmin && <InfoRow label="Aadhar"  value={profile.aadhar_number} />}
          </div>
          <div style={{ padding: '14px 16px', borderTop: '1px solid var(--border)' }}>
            {profile.resume_url ? (
              <div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>
                  📄 Resume: {profile.resume_url.split('/').pop().replace(/^resume_\d+_/, '')}
                </p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <a href={profile.resume_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">
                    <DownloadIcon style={{ marginRight: 6 }} /> Download Resume
                  </a>
                  <label className="btn btn-ghost btn-sm" style={{ cursor: 'pointer', display: 'inline-block', margin: 0 }}>
                    {uploadingResume ? 'Replacing...' : <><UploadIcon style={{ marginRight: 6 }} /> Replace Resume</>}
                    <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeChange} style={{ display: 'none' }} disabled={uploadingResume} />
                  </label>
                </div>
              </div>
            ) : (
              <div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>No resume uploaded</p>
                <label className="btn btn-secondary btn-sm" style={{ cursor: 'pointer', display: 'inline-block', margin: 0 }}>
                  {uploadingResume ? 'Uploading...' : <><UploadIcon style={{ marginRight: 6 }} /> Upload Resume</>}
                  <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeChange} style={{ display: 'none' }} disabled={uploadingResume} />
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Address Information (Editable) */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">📍 Address Information</div>
          </div>
          {editMode ? (
            <div>
              {[
                { key: 'address',           label: 'Address' },
                { key: 'permanent_address', label: 'Permanent Address' },
                { key: 'current_address',   label: 'Current Address' },
                { key: 'emergency_contact', label: 'Emergency Contact' },
              ].map(({ key, label }) => (
                <div key={key} className="form-group">
                  <label className="form-label">{label}</label>
                  {key === 'emergency_contact' ? (
                    <input className="form-control" value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                  ) : (
                    <textarea className="form-control" rows={2} value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                  )}
                </div>
              ))}
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
                <button className="btn btn-secondary" onClick={() => setEditMode(false)} disabled={saving}>Cancel</button>
                <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Saving…' : <><SaveIcon style={{ marginRight: 6 }} /> Save Changes</>}
                </button>
              </div>
            </div>
          ) : (
            <div className="info-grid">
              <InfoRow label="Address"           value={profile.address} />
              <InfoRow label="Current Address"   value={profile.current_address} />
              <InfoRow label="Permanent Address" value={profile.permanent_address} />
              <InfoRow label="Emergency Contact" value={profile.emergency_contact} />
            </div>
          )}
        </div>

        {/* Change Password */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🔐 Security</div>
            <button className="btn btn-ghost btn-sm" onClick={() => setPwVisible((v) => !v)}>
              {pwVisible ? 'Hide' : 'Change Password'}
            </button>
          </div>
          {pwVisible ? (
            <form onSubmit={handlePasswordChange}>
              <div className="form-group">
                <label className="form-label">New Password <span className="form-required">*</span></label>
                <input className="form-control" type="password" value={pwForm.password} required
                  onChange={(e) => setPwForm((f) => ({ ...f, password: e.target.value }))}
                  placeholder="Minimum 6 characters" />
              </div>
              <div className="form-group">
                <label className="form-label">Confirm Password <span className="form-required">*</span></label>
                <input className="form-control" type="password" value={pwForm.confirm} required
                  onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))} />
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPwVisible(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={pwSaving}>
                  {pwSaving ? 'Updating…' : <><LockIcon style={{ marginRight: 6 }} /> Update Password</>}
                </button>
              </div>
            </form>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
              Keep your account secure by using a strong, unique password.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
