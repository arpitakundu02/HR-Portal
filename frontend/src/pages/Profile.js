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
import { getMe, updateEmployee, uploadResume, uploadPhoto, deletePhoto, getDepartments, deleteEmployee } from '../services/api';
import { EditIcon, DownloadIcon, UploadIcon, SaveIcon, LockIcon, EyeIcon, EyeOffIcon, CameraIcon, TrashIcon } from '../components/common/Icons';
import Modal from '../components/common/Modal';

export default function Profile() {
  const { user, updateUser, isAdmin, logout } = useAuth();
  const toast = useToast();

  const [profile,  setProfile]  = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  const [departments, setDepartments] = useState([]);

  // Self deletion states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deletingSelf, setDeletingSelf] = useState(false);

  // Editable fields
  const [form, setForm] = useState({
    address: '', current_address: '', permanent_address: '', emergency_contact: '', phone_number: '', bio: '', experience_summary: '', gender: '', fathers_name: '', dob: '', blood_group: '',
    department_id: '', rank: '', date_of_joining: '', salary: '', aadhar_number: '',
  });

  const [uploadingResume, setUploadingResume] = useState(false);

  const handleResumeChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('resume', file);
    setUploadingResume(true);
    try {
      const res = await uploadResume(profile.id, fd);
      if (res.data.status === 'Pending') {
        toast.info('Resume update submitted for approval.');
      } else {
        toast.success('Resume uploaded successfully.');
      }
      const { data } = await getMe();
      setProfile(data);
      updateUser({ ...user, ...data });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed.');
    } finally {
      setUploadingResume(false);
    }
  };

  const handlePhotoChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('photo', file);
    setUploadingPhoto(true);
    try {
      const uploadRes = await uploadPhoto(profile.id, fd);
      toast.success('Profile photo updated successfully.');
      const { data } = await getMe();
      setProfile(data);
      updateUser({ ...user, ...data, photo_url: uploadRes.data.photo_url });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Photo upload failed.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleDeletePhoto = async () => {
    if (!window.confirm("Are you sure you want to delete your profile photo?")) return;
    try {
      await deletePhoto(profile.id);
      toast.success('Profile photo deleted.');
      const { data } = await getMe();
      setProfile(data);
      updateUser({ ...user, ...data, photo_url: null });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Delete photo failed.');
    }
  };

  // Password change
  const [pwForm,    setPwForm]    = useState({ password: '', confirm: '' });
  const [pwSaving,  setPwSaving]  = useState(false);
  const [pwVisible, setPwVisible] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      getDepartments().then((r) => setDepartments(r.data)).catch(() => {});
    }
    (async () => {
      try {
        const { data } = await getMe();
        setProfile(data);
        setForm({
          address:           data.address           || '',
          current_address:   data.current_address   || '',
          permanent_address: data.permanent_address || '',
          emergency_contact: data.emergency_contact || '',
          phone_number:      data.phone_number      || '',
          bio:               data.bio               || '',
          experience_summary:data.experience_summary|| '',
          gender:            data.gender            || 'Male',
          fathers_name:      data.fathers_name      || '',
          dob:               data.dob               || '',
          blood_group:       data.blood_group       || '',
          department_id:     data.department_id     || '',
          rank:              data.rank              || '',
          date_of_joining:   data.date_of_joining   || '',
          salary:            data.salary            || '',
          aadhar_number:     data.aadhar_number     || '',
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

  const handleDeleteSelf = async () => {
    if (deleteConfirmText !== 'DELETE MY ACCOUNT') {
      toast.error('Please type DELETE MY ACCOUNT to confirm.');
      return;
    }
    setDeletingSelf(true);
    try {
      await deleteEmployee(profile.id);
      toast.success('Your account has been deleted. Logging out...');
      logout();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete account.');
    } finally {
      setDeletingSelf(false);
      setShowDeleteModal(false);
    }
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
      <div className="profile-header" style={{ display: 'flex', alignItems: 'center', gap: 24, padding: '24px 30px' }}>
        <div style={{ position: 'relative' }}>
          {profile.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.name}
              style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover', border: '3px solid var(--border)' }}
            />
          ) : (
            <div style={{ width: 80, height: 80, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 700, border: '3px solid var(--border)' }}>
              {initials}
            </div>
          )}
          {profile.photo_url && (
            <button
              onClick={handleDeletePhoto}
              title="Delete photo"
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                backgroundColor: '#ef4444',
                color: '#fff',
                width: 26,
                height: 26,
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
              <TrashIcon style={{ width: 12, height: 12 }} />
            </button>
          )}
          <label style={{ position: 'absolute', bottom: 0, right: 0, backgroundColor: 'var(--accent)', color: '#fff', width: 26, height: 26, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 5px rgba(0,0,0,0.2)', margin: 0 }}>
            {uploadingPhoto ? '...' : <CameraIcon style={{ width: 12, height: 12 }} />}
            <input type="file" accept="image/*" onChange={handlePhotoChange} style={{ display: 'none' }} disabled={uploadingPhoto} />
          </label>
        </div>
        <div className="profile-meta">
          <h2>{profile.name}</h2>
          <p>{profile.rank || (profile.is_line_manager ? 'Line Manager' : profile.role)} · {profile.department_name || 'No Department'}</p>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <Badge status={profile.is_line_manager ? 'Line Manager' : profile.role} />
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

      {/* About Me Card */}
      <div className="card" style={{ marginTop: 24, padding: 20 }}>
        <div className="card-header" style={{ padding: '0 0 16px 0', borderBottom: '1px solid var(--border)' }}>
          <div className="card-title" style={{ margin: 0 }}>📝 About Me</div>
        </div>
        {editMode ? (
          <div className="form-group" style={{ marginTop: 16 }}>
            <textarea
              className="form-control"
              rows={4}
              value={form.bio}
              placeholder="Tell us about yourself..."
              onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
            />
            <small className="form-text text-muted" style={{ display: 'block', marginTop: 4 }}>
              Recommendation: A bio of 50+ words is suggested for a complete profile. Current word count: {form.bio ? form.bio.trim().split(/\s+/).filter(Boolean).length : 0}
            </small>
          </div>
        ) : (
          <div style={{ paddingTop: 16 }}>
            <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-primary)', fontSize: 14 }}>
              {profile.bio || 'No bio submitted yet.'}
            </p>
          </div>
        )}
      </div>

      <div className="grid-2" style={{ gap: 24, marginTop: 24 }}>
        {/* Personal Information */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">👤 Personal Information</div>
          </div>
          {editMode && isAdmin ? (
            <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Father's Name</label>
                <input className="form-control" name="fathers_name" value={form.fathers_name} onChange={(e) => setForm(f => ({ ...f, fathers_name: e.target.value }))} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Date of Birth</label>
                <input className="form-control" type="date" name="dob" value={form.dob} onChange={(e) => setForm(f => ({ ...f, dob: e.target.value }))} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Blood Group</label>
                <select className="form-control" name="blood_group" value={form.blood_group} onChange={(e) => setForm(f => ({ ...f, blood_group: e.target.value }))}>
                  <option value="">Select</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((bg) => <option key={bg} value={bg}>{bg}</option>)}
                </select>
              </div>
              <div className="info-grid" style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
                <InfoRow label="Full Name"      value={profile.name} />
                <InfoRow label="Email"          value={profile.email} />
                <InfoRow label="Phone Number"   value={profile.phone_number} />
                <InfoRow label="Emergency Contact" value={profile.emergency_contact} />
                <InfoRow label="Gender"          value={profile.gender} />
              </div>
            </div>
          ) : (
            <div className="info-grid">
              <InfoRow label="Full Name"      value={profile.name} />
              <InfoRow label="Father's Name"  value={profile.fathers_name} />
              <InfoRow label="Date of Birth"  value={profile.dob} />
              <InfoRow label="Blood Group"    value={profile.blood_group} />
              <InfoRow label="Email"          value={profile.email} />
              <InfoRow label="Phone Number"   value={profile.phone_number} />
              <InfoRow label="Emergency Contact" value={profile.emergency_contact} />
              <InfoRow label="Gender"          value={profile.gender} />
            </div>
          )}
        </div>

        {/* Employment Information */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🏢 Employment Details</div>
          </div>
          {editMode && isAdmin ? (
            <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Employee ID</label>
                <input className="form-control" value={profile.employee_id} readOnly disabled />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Department</label>
                <select className="form-control" name="department_id" value={form.department_id} onChange={(e) => setForm(f => ({ ...f, department_id: e.target.value }))}>
                  <option value="">Select Department</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Designation / Rank</label>
                <input className="form-control" name="rank" value={form.rank} onChange={(e) => setForm(f => ({ ...f, rank: e.target.value }))} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Date of Joining</label>
                <input className="form-control" type="date" name="date_of_joining" value={form.date_of_joining} onChange={(e) => setForm(f => ({ ...f, date_of_joining: e.target.value }))} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Salary (₹)</label>
                <input className="form-control" type="number" name="salary" value={form.salary} onChange={(e) => setForm(f => ({ ...f, salary: e.target.value }))} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontSize: 12, fontWeight: 600 }}>Aadhar Number</label>
                <input className="form-control" name="aadhar_number" value={form.aadhar_number} onChange={(e) => setForm(f => ({ ...f, aadhar_number: e.target.value }))} />
              </div>
            </div>
          ) : (
            <div className="info-grid">
              <InfoRow label="Employee ID"   value={profile.employee_id} />
              <InfoRow label="Department"    value={profile.department_name} />
              <InfoRow label="Designation"   value={profile.rank} />
              <InfoRow label="Date of Joining" value={profile.date_of_joining} />
              {isAdmin && <InfoRow label="Salary"  value={profile.salary ? `₹${Number(profile.salary).toLocaleString()}` : '—'} />}
              {isAdmin && <InfoRow label="Aadhar"  value={profile.aadhar_number} />}
            </div>
          )}
          <div style={{ padding: '14px 16px', borderTop: '1px solid var(--border)' }}>
            {profile.resume_url ? (
              <div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>
                  📄 Resume: {profile.resume_url.split('/').pop().replace(/^resume_\d+_/, '')}
                </p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <a href={`${profile.resume_url}?auth_token=${sessionStorage.getItem('hr_token')}`} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">
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
                { key: 'phone_number',      label: 'Phone Number' },
                { key: 'emergency_contact', label: 'Emergency Contact' },
              ].map(({ key, label }) => (
                <div key={key} className="form-group">
                  <label className="form-label">{label}</label>
                  {key === 'emergency_contact' || key === 'phone_number' ? (
                    <input className="form-control" value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                  ) : (
                    <textarea className="form-control" rows={2} value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                  )}
                </div>
              ))}
              <div className="form-group">
                <label className="form-label">Gender <span className="form-required">*</span></label>
                <select className="form-control" name="gender" value={form.gender} onChange={(e) => setForm((f) => ({ ...f, gender: e.target.value }))} required>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
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
              <InfoRow label="Phone Number"      value={profile.phone_number} />
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
                <div className="password-input-wrapper">
                  <input className="form-control" type={showNewPassword ? "text" : "password"} value={pwForm.password} required
                    onChange={(e) => setPwForm((f) => ({ ...f, password: e.target.value }))}
                    placeholder="Minimum 6 characters" />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowNewPassword(p => !p)}
                    title={showNewPassword ? "Hide password" : "Show password"}
                  >
                    {showNewPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Confirm Password <span className="form-required">*</span></label>
                <div className="password-input-wrapper">
                  <input className="form-control" type={showConfirmPassword ? "text" : "password"} value={pwForm.confirm} required
                    onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))} />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(p => !p)}
                    title={showConfirmPassword ? "Hide password" : "Show password"}
                  >
                    {showConfirmPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
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

        {isAdmin && (
          <div className="card" style={{ border: '1px solid var(--danger-border, #fecaca)' }}>
            <div className="card-header">
              <div className="card-title" style={{ color: 'var(--danger, #dc2626)', display: 'flex', alignItems: 'center', gap: 6 }}>
                ⚠️ Danger Zone
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, marginBottom: 16 }}>
              Deleting your account is permanent. You will immediately lose access to the system.
            </p>
            <button
              className="btn btn-danger"
              onClick={() => {
                setDeleteConfirmText('');
                setShowDeleteModal(true);
              }}
            >
              Delete My Account
            </button>
          </div>
        )}

        {/* Professional Profile Card */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <div className="card-title">💼 Professional Profile</div>
          </div>
          {editMode ? (
            <div>
              <div className="form-group">
                <label className="form-label">Experience Summary</label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={form.experience_summary}
                  placeholder="Summarize your professional experience..."
                  onChange={(e) => setForm((f) => ({ ...f, experience_summary: e.target.value }))}
                />
                <small className="form-text text-muted" style={{ display: 'block', marginTop: 4 }}>
                  Maximum 5000 characters. Current length: {form.experience_summary ? form.experience_summary.length : 0} / 5000
                </small>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '8px 4px' }}>
              <div>
                <strong style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Experience Summary</strong>
                <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-primary)', fontSize: 14 }}>
                  {profile.experience_summary || 'No experience summary submitted yet.'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Self-Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Your Account?"
        size="sm"
      >
        <p style={{ color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.5 }}>
          Are you sure you want to delete your administrator account? 
          <strong> You will immediately lose access to the HR Portal</strong> and will be logged out. 
          Historical records will remain preserved.
        </p>
        <div className="form-group" style={{ marginBottom: 20 }}>
          <label className="form-label" style={{ fontWeight: 600 }}>
            Type <span style={{ color: 'var(--danger, #dc2626)' }}>DELETE MY ACCOUNT</span> to confirm
          </label>
          <input
            className="form-control"
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            placeholder="DELETE MY ACCOUNT"
          />
        </div>
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => setShowDeleteModal(false)} disabled={deletingSelf}>
            Cancel
          </button>
          <button
            className="btn btn-danger"
            onClick={handleDeleteSelf}
            disabled={deleteConfirmText !== 'DELETE MY ACCOUNT' || deletingSelf}
          >
            {deletingSelf ? 'Deleting Account...' : 'Delete My Account'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
