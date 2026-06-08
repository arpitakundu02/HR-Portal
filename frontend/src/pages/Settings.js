/**
 * pages/Settings.js
 * Admin Settings panel: Manage office latitude, longitude, and allowed radius.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getOfficeSettings, updateOfficeSettings } from '../services/api';
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

export default function Settings() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    latitude: '',
    longitude: '',
    radius_meters: ''
  });
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
      const { data } = await getOfficeSettings();
      setForm({
        latitude: data.latitude.toString(),
        longitude: data.longitude.toString(),
        radius_meters: data.radius_meters.toString()
      });
      setMeta({
        updated_by: data.updated_by,
        updated_at: data.updated_at
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
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (errors[e.target.name]) {
      setErrors(prev => ({ ...prev, [e.target.name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    const lat = parseFloat(form.latitude);
    const lon = parseFloat(form.longitude);
    const rad = parseFloat(form.radius_meters);

    if (isNaN(lat) || lat < -90 || lat > 90) {
      newErrors.latitude = 'Latitude must be a valid number between -90 and 90.';
    }
    if (isNaN(lon) || lon < -180 || lon > 180) {
      newErrors.longitude = 'Longitude must be a valid number between -180 and 180.';
    }
    if (isNaN(rad) || rad < 200) {
      newErrors.radius_meters = 'Radius must be a positive number greater than or equal to 200 meters.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
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
          latitude: pos.coords.latitude.toFixed(7),
          longitude: pos.coords.longitude.toFixed(7)
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

        const officeLat = parseFloat(form.latitude) || 0;
        const officeLon = parseFloat(form.longitude) || 0;
        const radius = parseFloat(form.radius_meters) || 200;

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
      latitude: testResults.adminLat.toFixed(7),
      longitude: testResults.adminLon.toFixed(7)
    }));
    toast.success('📍 Applied test location to office settings fields. Click Save Settings to persist.');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    try {
      const { data } = await updateOfficeSettings({
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        radius_meters: parseFloat(form.radius_meters)
      });
      setMeta({
        updated_by: data.updated_by,
        updated_at: data.updated_at
      });
      toast.success('🎉 Settings saved successfully!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spinner />;

  // Office Location variables for Map rendering
  const officeCoords = [parseFloat(form.latitude) || 0, parseFloat(form.longitude) || 0];
  const testOfficeCoords = testResults ? [testResults.officeLat, testResults.officeLon] : officeCoords;
  const adminCoords = testResults ? [testResults.adminLat, testResults.adminLon] : null;

  return (
    <div className="fade-in" style={{ maxWidth: 680, margin: '0 auto' }}>
      <div className="page-header">
        <div className="page-header-left">
          <h2>Admin Settings</h2>
          <p>Configure company policies, dynamic parameters, and office locations</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16, marginBottom: 20 }}>
          <div>
            <div className="card-title">📍 Office Geofencing Configuration</div>
            <div className="card-subtitle">Define the physical office center and allowed attendance check-in radius</div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Office Latitude <span className="form-required">*</span></label>
              <input
                type="text"
                name="latitude"
                className="form-control"
                required
                value={form.latitude}
                onChange={handleChange}
                placeholder="e.g. 28.6139"
              />
              {errors.latitude && <div className="form-error">{errors.latitude}</div>}
            </div>

            <div className="form-group">
              <label className="form-label">Office Longitude <span className="form-required">*</span></label>
              <input
                type="text"
                name="longitude"
                className="form-control"
                required
                value={form.longitude}
                onChange={handleChange}
                placeholder="e.g. 77.2090"
              />
              {errors.longitude && <div className="form-error">{errors.longitude}</div>}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Allowed Check-In Radius (Meters) <span className="form-required">*</span></label>
            <input
              type="text"
              name="radius_meters"
              className="form-control"
              required
              value={form.radius_meters}
              onChange={handleChange}
              placeholder="e.g. 200"
            />
            {errors.radius_meters && <div className="form-error">{errors.radius_meters}</div>}
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 8, marginBottom: 24 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleUseCurrentLocation}
            >
              📍 Grab My Location Coordinates
            </button>
          </div>

          {/* Audit trail metadata info */}
          <div style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            padding: '12px 16px',
            fontSize: 12,
            color: 'var(--text-muted)',
            marginBottom: 24,
            display: 'flex',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 8
          }}>
            <div>⚙️ <strong>Last Updated By:</strong> {meta.updated_by || 'System Default'}</div>
            <div>⏰ <strong>Timestamp:</strong> {meta.updated_at ? new Date(meta.updated_at).toLocaleString() : '—'}</div>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Saving Config…' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>

      {/* Office Location Test Section */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16, marginBottom: 20 }}>
          <div>
            <div className="card-title">🔍 Office Location Test</div>
            <div className="card-subtitle">Verify your current location against the office coordinates and check if you are within the allowed geofence.</div>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleRunLocationTest}
            disabled={testing}
          >
            {testing ? 'Testing Location...' : 'Run Location Test'}
          </button>
        </div>

        {testResults && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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

            <div style={{ height: 320, width: '100%', borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--border)', position: 'relative', zIndex: 1 }}>
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

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleApplyTestLocation}
              >
                📍 Use Current Location as Office Location
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

