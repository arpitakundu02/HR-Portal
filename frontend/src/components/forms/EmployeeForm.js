/**
 * components/forms/EmployeeForm.js
 * Shared form for Add and Edit employee operations.
 * Receives initialData (null = add mode), departments list, onSubmit, onCancel.
 */
import { useState, useEffect } from 'react';
import { EyeIcon, EyeOffIcon } from '../common/Icons';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

const EMPTY = {
  employee_id: '', name: '', fathers_name: '', email: '', password: '',
  dob: '', blood_group: '', department_id: '', rank: '', role: 'Employee',
  date_of_joining: '', salary: '', aadhar_number: '',
  address: '', permanent_address: '', current_address: '', emergency_contact: '',
};

export default function EmployeeForm({ initialData, departments, onSubmit, onCancel, loading }) {
  const isEdit = !!initialData;
  const [form, setForm] = useState(EMPTY);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (initialData) {
      setForm({
        ...EMPTY,
        ...initialData,
        password: '',          // Never pre-fill password
        dob: initialData.dob || '',
        date_of_joining: initialData.date_of_joining || '',
        salary: initialData.salary || '',
        department_id: initialData.department_id || '',
      });
    } else {
      setForm(EMPTY);
    }
  }, [initialData]);

  const change = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = { ...form };
    // Don't send empty password on edit (backend treats it as no-change)
    if (isEdit && !payload.password) delete payload.password;
    if (!payload.department_id) delete payload.department_id;
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Identity */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Employee ID</label>
          <input className="form-control" name="employee_id" value={form.employee_id}
            onChange={change} placeholder="Auto-generated if blank" />
        </div>
        <div className="form-group">
          <label className="form-label">Role <span className="form-required">*</span></label>
          <select className="form-control" name="role" value={form.role} onChange={change} required>
            <option value="Employee">Employee</option>
            <option value="Admin">Admin</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Full Name <span className="form-required">*</span></label>
          <input className="form-control" name="name" value={form.name}
            onChange={change} required placeholder="e.g. Rajesh Kumar" />
        </div>
        <div className="form-group">
          <label className="form-label">Father's Name</label>
          <input className="form-control" name="fathers_name" value={form.fathers_name} onChange={change} />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Email <span className="form-required">*</span></label>
          <input className="form-control" type="email" name="email" value={form.email}
            onChange={change} required placeholder="employee@company.com" />
        </div>
        <div className="form-group">
          <label className="form-label">{isEdit ? 'New Password (leave blank to keep)' : 'Password *'}</label>
          <div className="password-input-wrapper">
            <input className="form-control" type={showPassword ? "text" : "password"} name="password" value={form.password}
              onChange={change} required={!isEdit} placeholder={isEdit ? 'Leave blank to keep current' : 'Min 6 characters'} />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword(p => !p)}
              title={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOffIcon /> : <EyeIcon />}
            </button>
          </div>
        </div>
      </div>

      {/* Personal */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Date of Birth</label>
          <input className="form-control" type="date" name="dob" value={form.dob} onChange={change} />
        </div>
        <div className="form-group">
          <label className="form-label">Blood Group</label>
          <select className="form-control" name="blood_group" value={form.blood_group} onChange={change}>
            <option value="">Select</option>
            {BLOOD_GROUPS.map((bg) => <option key={bg} value={bg}>{bg}</option>)}
          </select>
        </div>
      </div>

      {/* Employment */}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Department</label>
          <select className="form-control" name="department_id" value={form.department_id} onChange={change}>
            <option value="">Select Department</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Rank / Designation</label>
          <input className="form-control" name="rank" value={form.rank} onChange={change} placeholder="e.g. Senior Analyst" />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Date of Joining</label>
          <input className="form-control" type="date" name="date_of_joining" value={form.date_of_joining} onChange={change} />
        </div>
        <div className="form-group">
          <label className="form-label">Salary (₹)</label>
          <input className="form-control" type="number" name="salary" value={form.salary} onChange={change} placeholder="e.g. 50000" />
        </div>
      </div>

      {/* Documents */}
      <div className="form-group">
        <label className="form-label">Aadhar Number</label>
        <input className="form-control" name="aadhar_number" value={form.aadhar_number} onChange={change} placeholder="12-digit Aadhar" />
      </div>

      {/* Address */}
      <div className="form-group">
        <label className="form-label">Address</label>
        <textarea className="form-control" name="address" value={form.address} onChange={change} rows={2} />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Permanent Address</label>
          <textarea className="form-control" name="permanent_address" value={form.permanent_address} onChange={change} rows={2} />
        </div>
        <div className="form-group">
          <label className="form-label">Current Address</label>
          <textarea className="form-control" name="current_address" value={form.current_address} onChange={change} rows={2} />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Emergency Contact</label>
        <input className="form-control" name="emergency_contact" value={form.emergency_contact} onChange={change} placeholder="+91 98765 43210" />
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving…' : isEdit ? '💾 Update Employee' : '➕ Create Employee'}
        </button>
      </div>
    </form>
  );
}
