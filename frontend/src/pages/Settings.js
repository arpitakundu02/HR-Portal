/**
 * pages/Settings.js
 * Admin Settings panel: Manage Company, Leave, Attendance (with Map), Security, and Notifications settings.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getSystemSettings, updateSystemSettings } from '../services/api';
import Spinner from '../components/common/Spinner';
import { useToast } from '../components/common/Toast';
import { MapContainer, TileLayer, Marker, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix custom icon classes to display properly on the interactive map
const blueIcon = L.divIcon({
  className: 'custom-blue-marker',
  html: `<div style="background-color: #3b82f6; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.4);"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

const redIcon = L.divIcon({
  className: 'custom-red-marker',
  html: `<div style="background-color: #ef4444; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.4);"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

// Map recentering component
function MapRecenter({ currentLoc, officeLoc }) {
  const map = useMap();
  useEffect(() => {
    if (currentLoc && officeLoc) {
      const bounds = L.latLngBounds([currentLoc, officeLoc]);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    } else if (officeLoc) {
      map.setView(officeLoc, 15);
    }
  }, [currentLoc, officeLoc, map]);
  return null;
}

const haversineDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371e3; // metres
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
    Math.cos(phi1) *
      Math.cos(phi2) *
      Math.sin(deltaLambda / 2) *
      Math.sin(deltaLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c; // in metres
};

// Default settings dictionary for reset action
const DEFAULTS = {
  company_name: "HR Portal Inc.",
  company_email: "info@hrportal.com",
  company_phone: "+1 555-0199",
  company_address: "123 Tech Avenue, Silicon Valley, CA",
  apl_allocation: "20",
  wfh_limit_male: "4",
  wfh_limit_female: "5",
  office_latitude: "28.6139",
  office_longitude: "77.2090",
  office_radius_meters: "200",
  standard_working_hours: "9",
  min_password_length: "8",
  session_timeout: "30",
  enable_self_registration: "true",
  enable_email_notifications: "true",
  enable_attendance_reminders: "true",
  enable_leave_approval_emails: "true"
};

export default function Settings() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [savingSection, setSavingSection] = useState({});
  const [form, setForm] = useState({ ...DEFAULTS });
  const [meta, setMeta] = useState({
    updated_by: '',
    updated_at: ''
  });
  const [errors, setErrors] = useState({});

  // Location Test States
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);

  useEffect(() => {
    if (isAdmin) {
      loadSettings();
    }
    // eslint-disable-next-line
  }, [isAdmin]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const { data } = await getSystemSettings();
      setForm(prev => ({
        ...prev,
        ...data
      }));
      setMeta({
        updated_by: data.office_updated_by_name || 'System Default',
        updated_at: data.office_updated_at || ''
      });
    } catch {
      toast.error('Failed to load settings.');
    } finally {
      setLoading(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="fade-in" style={{ padding: 24, textAlign: 'center' }}>
        <div className="alert alert-error" style={{ display: 'inline-flex' }}>
          🛑 Access Denied: This page is restricted to Admin users.
        </div>
      </div>
    );
  }

  const handleChange = (e) => {
    const val = e.target.type === 'checkbox' ? (e.target.checked ? 'true' : 'false') : e.target.value;
    setForm(prev => ({ ...prev, [e.target.name]: val }));
    if (errors[e.target.name]) {
      setErrors(prev => ({ ...prev, [e.target.name]: '' }));
    }
  };

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm(prev => ({
          ...prev,
          office_latitude: pos.coords.latitude.toFixed(7),
          office_longitude: pos.coords.longitude.toFixed(7)
        }));
        toast.success('📍 Successfully grabbed your current location coordinates!');
      },
      () => {
        toast.error('Could not retrieve your location. Please check browser permissions.');
      },
      { enableHighAccuracy: true }
    );
  };

  const handleRunLocationTest = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser.');
      return;
    }
    setTesting(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const userLat = pos.coords.latitude;
        const userLon = pos.coords.longitude;
        const accuracy = pos.coords.accuracy || 0;

        const officeLat = parseFloat(form.office_latitude) || 0;
        const officeLon = parseFloat(form.office_longitude) || 0;
        const radius = parseFloat(form.office_radius_meters) || 200;

        const distance = haversineDistance(userLat, userLon, officeLat, officeLon);
        const isInside = distance <= radius;

        setTestResults({
          adminLat: userLat,
          adminLon: userLon,
          accuracy,
          officeLat,
          officeLon,
          distance,
          radius,
          isInside
        });
        setTesting(false);
        toast.success('🎉 Location test completed successfully!');
      },
      (err) => {
        setTesting(false);
        toast.error(`Could not retrieve location: ${err.message}`);
      },
      { enableHighAccuracy: true }
    );
  };

  const handleApplyTestLocation = () => {
    if (!testResults) return;
    setForm(prev => ({
      ...prev,
      office_latitude: testResults.adminLat.toFixed(7),
      office_longitude: testResults.adminLon.toFixed(7)
    }));
    toast.success('📍 Applied test location to office settings fields. Click Save Changes in Attendance Card to persist.');
  };

  // Section Save Wrappers
  const saveSection = async (sectionName, keys) => {
    // Local validation
    const localErrors = {};
    if (sectionName === 'company') {
      if (!form.company_name.trim()) localErrors.company_name = 'Company Name is required.';
      if (!form.company_email.trim() || !form.company_email.includes('@')) localErrors.company_email = 'Valid Company Email is required.';
      if (!form.company_phone.trim()) localErrors.company_phone = 'Phone Number is required.';
    } else if (sectionName === 'leave') {
      const apl = parseInt(form.apl_allocation);
      const wm = parseInt(form.wfh_limit_male);
      const wf = parseInt(form.wfh_limit_female);
      if (isNaN(apl) || apl < 0) localErrors.apl_allocation = 'APL allocation must be 0 or greater.';
      if (isNaN(wm) || wm < 0) localErrors.wfh_limit_male = 'WFH male limit must be 0 or greater.';
      if (isNaN(wf) || wf < 0) localErrors.wfh_limit_female = 'WFH female limit must be 0 or greater.';
    } else if (sectionName === 'attendance') {
      const lat = parseFloat(form.office_latitude);
      const lon = parseFloat(form.office_longitude);
      const rad = parseFloat(form.office_radius_meters);
      const hrs = parseFloat(form.standard_working_hours);
      if (isNaN(lat) || lat < -90 || lat > 90) localErrors.office_latitude = 'Latitude must be between -90 and 90.';
      if (isNaN(lon) || lon < -180 || lon > 180) localErrors.office_longitude = 'Longitude must be between -180 and 180.';
      if (isNaN(rad) || rad <= 0) localErrors.office_radius_meters = 'Radius must be a positive number greater than 0.';
      if (isNaN(hrs) || hrs < 1 || hrs > 24) localErrors.standard_working_hours = 'Standard working hours must be between 1 and 24.';
    } else if (sectionName === 'security') {
      const minPwd = parseInt(form.min_password_length);
      const timeout = parseInt(form.session_timeout);
      if (isNaN(minPwd) || minPwd < 6) localErrors.min_password_length = 'Password length must be at least 6.';
      if (isNaN(timeout) || timeout <= 0) localErrors.session_timeout = 'Timeout must be greater than 0.';
    }

    if (Object.keys(localErrors).length > 0) {
      setErrors(prev => ({ ...prev, ...localErrors }));
      toast.error('Validation failed. Please check the inputs.');
      return;
    }

    setSavingSection(prev => ({ ...prev, [sectionName]: true }));
    try {
      const payload = {};
      keys.forEach(k => { payload[k] = form[k]; });
      
      const { data } = await updateSystemSettings(payload);
      
      // Update global settings
      setForm(prev => ({ ...prev, ...data }));
      if (data.office_updated_by_name) {
        setMeta({
          updated_by: data.office_updated_by_name,
          updated_at: data.office_updated_at
        });
      }
      toast.success(`🎉 ${sectionName.toUpperCase()} settings saved successfully!`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save settings.');
    } finally {
      setSavingSection(prev => ({ ...prev, [sectionName]: false }));
    }
  };

  const resetSection = async (sectionName, keys) => {
    const confirm = window.confirm(`Are you sure you want to reset ${sectionName} settings to default values?`);
    if (!confirm) return;

    const resetData = {};
    keys.forEach(k => { resetData[k] = DEFAULTS[k]; });

    setSavingSection(prev => ({ ...prev, [sectionName]: true }));
    try {
      const { data } = await updateSystemSettings(resetData);
      setForm(prev => ({ ...prev, ...data }));
      toast.success(`🔄 Reset ${sectionName} settings to defaults.`);
    } catch (err) {
      toast.error('Failed to reset settings.');
    } finally {
      setSavingSection(prev => ({ ...prev, [sectionName]: false }));
    }
  };

  if (loading) return <Spinner />;

  // Office Location variables for Map rendering
  const officeCoords = [parseFloat(form.office_latitude) || 28.6139, parseFloat(form.office_longitude) || 77.2090];
  const testOfficeCoords = testResults ? [testResults.officeLat, testResults.officeLon] : officeCoords;
  const adminCoords = testResults ? [testResults.adminLat, testResults.adminLon] : null;

  return (
    <div className="fade-in" style={{ maxWidth: 800, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="page-header">
        <div className="page-header-left">
          <h2>System Configuration</h2>
          <p>Configure company parameters, policies, and parameters dynamically</p>
        </div>
      </div>

      {/* 1. Company Settings */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
          <div className="card-title">🏢 Company Settings</div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Company Name <span className="form-required">*</span></label>
            <input className="form-control" name="company_name" value={form.company_name} onChange={handleChange} />
            {errors.company_name && <div className="form-error">{errors.company_name}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Company Email <span className="form-required">*</span></label>
            <input className="form-control" type="email" name="company_email" value={form.company_email} onChange={handleChange} />
            {errors.company_email && <div className="form-error">{errors.company_email}</div>}
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Company Phone <span className="form-required">*</span></label>
            <input className="form-control" name="company_phone" value={form.company_phone} onChange={handleChange} />
            {errors.company_phone && <div className="form-error">{errors.company_phone}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Company Address</label>
            <input className="form-control" name="company_address" value={form.company_address} onChange={handleChange} />
          </div>
        </div>
        <div className="form-actions" style={{ marginTop: 12 }}>
          <button className="btn btn-secondary" onClick={() => resetSection('company', ['company_name', 'company_email', 'company_phone', 'company_address'])}>
            Reset to Default
          </button>
          <button className="btn btn-primary" onClick={() => saveSection('company', ['company_name', 'company_email', 'company_phone', 'company_address'])} disabled={savingSection.company}>
            {savingSection.company ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* 2. Leave Settings */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
          <div className="card-title">📊 Leave Settings</div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Annual Privilege Leave (APL) Allocation <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="apl_allocation" value={form.apl_allocation} onChange={handleChange} />
            {errors.apl_allocation && <div className="form-error">{errors.apl_allocation}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Male WFH Monthly Limit <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="wfh_limit_male" value={form.wfh_limit_male} onChange={handleChange} />
            {errors.wfh_limit_male && <div className="form-error">{errors.wfh_limit_male}</div>}
          </div>
        </div>
        <div className="form-row">
          <div className="form-group" style={{ maxWidth: '50%' }}>
            <label className="form-label">Female WFH Monthly Limit <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="wfh_limit_female" value={form.wfh_limit_female} onChange={handleChange} />
            {errors.wfh_limit_female && <div className="form-error">{errors.wfh_limit_female}</div>}
          </div>
        </div>
        <div className="form-actions" style={{ marginTop: 12 }}>
          <button className="btn btn-secondary" onClick={() => resetSection('leave', ['apl_allocation', 'wfh_limit_male', 'wfh_limit_female'])}>
            Reset to Default
          </button>
          <button className="btn btn-primary" onClick={() => saveSection('leave', ['apl_allocation', 'wfh_limit_male', 'wfh_limit_female'])} disabled={savingSection.leave}>
            {savingSection.leave ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* 3. Attendance Settings */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
          <div className="card-title">📍 Attendance Settings & Geofencing</div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Office Latitude <span className="form-required">*</span></label>
            <input className="form-control" name="office_latitude" value={form.office_latitude} onChange={handleChange} />
            {errors.office_latitude && <div className="form-error">{errors.office_latitude}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Office Longitude <span className="form-required">*</span></label>
            <input className="form-control" name="office_longitude" value={form.office_longitude} onChange={handleChange} />
            {errors.office_longitude && <div className="form-error">{errors.office_longitude}</div>}
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Geofence Radius (Meters) <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="office_radius_meters" value={form.office_radius_meters} onChange={handleChange} />
            {errors.office_radius_meters && <div className="form-error">{errors.office_radius_meters}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Standard Working Hours <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="standard_working_hours" value={form.standard_working_hours} onChange={handleChange} step="0.5" />
            {errors.standard_working_hours && <div className="form-error">{errors.standard_working_hours}</div>}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <button type="button" className="btn btn-secondary" onClick={handleUseCurrentLocation}>
            📍 Grab My Location Coordinates
          </button>
          <button type="button" className="btn btn-secondary" onClick={handleRunLocationTest} disabled={testing}>
            {testing ? 'Testing...' : '🔍 Run Location Test'}
          </button>
        </div>

        {testResults && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>YOUR GPS COORDINATES</div>
                <div style={{ fontWeight: 600, fontSize: 13, marginTop: 4 }}>
                  {testResults.adminLat.toFixed(7)}, {testResults.adminLon.toFixed(7)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Accuracy: ±{testResults.accuracy.toFixed(1)} meters
                </div>
              </div>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>OFFICE GEOLOCATION</div>
                <div style={{ fontWeight: 600, fontSize: 13, marginTop: 4 }}>
                  {testResults.officeLat.toFixed(7)}, {testResults.officeLon.toFixed(7)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Configured Radius: {testResults.radius} meters
                </div>
              </div>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>DISTANCE / STATUS</div>
                <div style={{ fontWeight: 600, fontSize: 13, marginTop: 4 }}>
                  {testResults.distance.toFixed(1)} meters
                </div>
                <div style={{ fontSize: 12, fontWeight: 700, marginTop: 4 }}>
                  {testResults.isInside ? '✅ Inside Geofence' : '❌ Outside Geofence'}
                </div>
              </div>
            </div>

            <div style={{ height: 300, width: '100%', borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--border)', position: 'relative', zIndex: 1 }}>
              <MapContainer center={testOfficeCoords} zoom={15} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Marker position={testOfficeCoords} icon={redIcon} />
                {adminCoords && <Marker position={adminCoords} icon={blueIcon} />}
                <Circle center={testOfficeCoords} radius={testResults.radius} pathOptions={{ color: 'green', fillColor: 'green', fillOpacity: 0.15 }} />
                <MapRecenter currentLoc={adminCoords} officeLoc={testOfficeCoords} />
              </MapContainer>
            </div>

            <div>
              <button type="button" className="btn btn-secondary" onClick={handleApplyTestLocation}>
                📍 Use Test Location coordinates
              </button>
            </div>
          </div>
        )}

        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '12px 16px',
          fontSize: 12,
          color: 'var(--text-muted)',
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 8
        }}>
          <div>⚙️ <strong>Last Updated By:</strong> {meta.updated_by}</div>
          <div>⏰ <strong>Timestamp:</strong> {meta.updated_at ? new Date(meta.updated_at).toLocaleString() : '—'}</div>
        </div>

        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => resetSection('attendance', ['office_latitude', 'office_longitude', 'office_radius_meters', 'standard_working_hours'])}>
            Reset to Default
          </button>
          <button className="btn btn-primary" onClick={() => saveSection('attendance', ['office_latitude', 'office_longitude', 'office_radius_meters', 'standard_working_hours'])} disabled={savingSection.attendance}>
            {savingSection.attendance ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* 4. Security Settings */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
          <div className="card-title">🔐 Security Settings</div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Minimum Password Length <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="min_password_length" value={form.min_password_length} onChange={handleChange} min={6} />
            {errors.min_password_length && <div className="form-error">{errors.min_password_length}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Session Timeout (Minutes) <span className="form-required">*</span></label>
            <input className="form-control" type="number" name="session_timeout" value={form.session_timeout} onChange={handleChange} min={5} />
            {errors.session_timeout && <div className="form-error">{errors.session_timeout}</div>}
          </div>
        </div>
        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
          <input
            type="checkbox"
            id="enable_self_registration"
            name="enable_self_registration"
            checked={form.enable_self_registration === 'true'}
            onChange={handleChange}
            style={{ width: 18, height: 18, cursor: 'pointer' }}
          />
          <label htmlFor="enable_self_registration" style={{ fontSize: 14, fontWeight: 500, cursor: 'pointer' }}>
            Allow Employee Self-Registration requests
          </label>
        </div>
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => resetSection('security', ['min_password_length', 'session_timeout', 'enable_self_registration'])}>
            Reset to Default
          </button>
          <button className="btn btn-primary" onClick={() => saveSection('security', ['min_password_length', 'session_timeout', 'enable_self_registration'])} disabled={savingSection.security}>
            {savingSection.security ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* 5. Notification Settings */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
          <div className="card-title">🔔 Notification Settings</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <input
              type="checkbox"
              id="enable_email_notifications"
              name="enable_email_notifications"
              checked={form.enable_email_notifications === 'true'}
              onChange={handleChange}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
            <label htmlFor="enable_email_notifications" style={{ fontSize: 14, fontWeight: 500, cursor: 'pointer' }}>
              Enable Email Notifications (General)
            </label>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <input
              type="checkbox"
              id="enable_attendance_reminders"
              name="enable_attendance_reminders"
              checked={form.enable_attendance_reminders === 'true'}
              onChange={handleChange}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
            <label htmlFor="enable_attendance_reminders" style={{ fontSize: 14, fontWeight: 500, cursor: 'pointer' }}>
              Enable Daily Attendance Reminders
            </label>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <input
              type="checkbox"
              id="enable_leave_approval_emails"
              name="enable_leave_approval_emails"
              checked={form.enable_leave_approval_emails === 'true'}
              onChange={handleChange}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
            <label htmlFor="enable_leave_approval_emails" style={{ fontSize: 14, fontWeight: 500, cursor: 'pointer' }}>
              Send emails when Leaves are submitted or actioned
            </label>
          </div>
        </div>
        <div className="form-actions" style={{ marginTop: 20 }}>
          <button className="btn btn-secondary" onClick={() => resetSection('notification', ['enable_email_notifications', 'enable_attendance_reminders', 'enable_leave_approval_emails'])}>
            Reset to Default
          </button>
          <button className="btn btn-primary" onClick={() => saveSection('notification', ['enable_email_notifications', 'enable_attendance_reminders', 'enable_leave_approval_emails'])} disabled={savingSection.notification}>
            {savingSection.notification ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
