/**
 * pages/Attendance.js
 * Check-in / Check-out panel with geolocation + monthly history table + embedded Leaflet Map.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Spinner from '../components/common/Spinner';
import Pagination from '../components/common/Pagination';
import { useToast } from '../components/common/Toast';
import {
  getTodayStatus,
  checkIn,
  checkOut,
  getAttendanceHistory,
  getEmployees,
  getOfficeSettings
} from '../services/api';
import { MapContainer, TileLayer, Marker, Circle, useMap, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { ClockIcon, MapPinIcon, SignalIcon, RulerIcon, ShieldCheckIcon, FlagIcon, RefreshIcon, InboxIcon } from '../components/common/Icons';

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

export default function Attendance() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [status,   setStatus]   = useState(null);
  const [history,  setHistory]  = useState([]);
  const [total,    setTotal]    = useState(0);
  const [page,     setPage]     = useState(1);
  const [pages,    setPages]    = useState(1);
  const [month,    setMonth]    = useState(new Date().toISOString().slice(0, 7));
  const [empFilter, setEmpFilter] = useState('');
  const [employees, setEmployees] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [geoError, setGeoError] = useState('');
  const [debugInfo, setDebugInfo] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [timer,    setTimer]    = useState(null); // live working hours

  // Live Telemetry states
  const [officeSettings, setOfficeSettings] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [locationTimestamp, setLocationTimestamp] = useState(null);
  const [locationError, setLocationError] = useState('');
  const [distance, setDistance] = useState(null);
  const [isInside, setIsInside] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleString());

  const fetchOfficeAndTrack = useCallback(async () => {
    try {
      const { data } = await getOfficeSettings();
      setOfficeSettings(data);
      trackUserLocation(data);
    } catch (err) {
      console.error('Failed to load office settings', err);
    }
    // eslint-disable-next-line
  }, []);

  const trackUserLocation = (office = officeSettings) => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const acc = pos.coords.accuracy;
        const time = new Date().toLocaleString();

        setUserLocation({ latitude: lat, longitude: lon, accuracy: acc });
        setLocationTimestamp(time);
        setLocationError('');

        if (office) {
          const dist = haversineDistance(lat, lon, office.latitude, office.longitude);
          setDistance(dist);
          setIsInside(dist <= office.radius_meters);
        }
      },
      (err) => {
        setLocationError('Location access required for check-in');
        console.warn('Geolocation failed:', err.message);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  useEffect(() => {
    loadStatus();
    fetchOfficeAndTrack();
    if (isAdmin) getEmployees({ per_page: 200 }).then((r) => setEmployees(r.data.employees || []));
    // eslint-disable-next-line
  }, [isAdmin]);

  useEffect(() => { loadHistory(); }, [page, month, empFilter]); // eslint-disable-line

  // Live clock timer update (every 1 second)
  useEffect(() => {
    const clockId = setInterval(() => {
      setCurrentTime(new Date().toLocaleString());
    }, 1000);
    return () => clearInterval(clockId);
  }, []);

  // 15 second tracking refresh
  useEffect(() => {
    const trackingId = setInterval(() => {
      if (officeSettings) {
        trackUserLocation(officeSettings);
      } else {
        fetchOfficeAndTrack();
      }
    }, 15000);
    return () => clearInterval(trackingId);
    // eslint-disable-next-line
  }, [officeSettings]);

  // Live working hours timer when checked in
  useEffect(() => {
    if (status?.check_in && !status?.check_out) {
      const id = setInterval(() => setTimer(Date.now()), 1000);
      return () => clearInterval(id);
    }
  }, [status]);

  const loadStatus = async () => {
    try { const { data } = await getTodayStatus(); setStatus(data); }
    catch {}
  };

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 20 };
      if (month) params.month = month;
      if (isAdmin && empFilter) params.employee_id = empFilter;
      const { data } = await getAttendanceHistory(params);
      setHistory(data.records);
      setTotal(data.total);
      setPages(data.pages);
    } catch { toast.error('Failed to load attendance history.'); }
    finally { setLoading(false); }
    // eslint-disable-next-line
  }, [page, month, empFilter, isAdmin]);

  const handleCheckIn = () => {
    setGeoError('');
    setDebugInfo(null);
    setCheckingIn(true);
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by your browser.');
      setCheckingIn(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          await checkIn({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
          toast.success('✅ Checked in successfully!');
          await loadStatus();
          loadHistory();
          // Force tracking refresh immediately after check-in
          trackUserLocation(officeSettings);
        } catch (err) {
          const msg = err.response?.data?.error || 'Check-in failed.';
          setGeoError(msg);
          if (err.response?.data?.debug_info) {
            setDebugInfo(err.response.data.debug_info);
          }
          toast.error(msg);
        } finally { setCheckingIn(false); }
      },
      (err) => {
        const msg = err.code === 1
          ? 'Location permission denied. Please allow location access and try again.'
          : 'Could not determine your location. Please try again.';
        setGeoError(msg);
        toast.error(msg);
        setCheckingIn(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleCheckOut = async () => {
    setCheckingIn(true);
    try {
      const { data } = await checkOut();
      toast.success(`✅ Checked out. Working hours: ${data.working_hours?.toFixed(2)}h`);
      await loadStatus();
      loadHistory();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Check-out failed.');
    } finally { setCheckingIn(false); }
  };

  const parseUTCDate = (dateStr) => {
    if (!dateStr) return null;
    const isoStr = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
    return new Date(isoStr);
  };

  const getLiveHours = () => {
    if (!status?.check_in || status?.check_out) return null;
    const parsed = parseUTCDate(status.check_in);
    if (!parsed) return null;
    const diff = (Date.now() - parsed.getTime()) / 1000;
    const h = Math.floor(diff / 3600);
    const m = Math.floor((diff % 3600) / 60);
    const s = Math.floor(diff % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const isCheckedIn = status?.check_in && !status?.check_out;
  const isCheckedOut = status?.check_in && status?.check_out;

  const dotClass =
    isCheckedIn  ? 'checked-in'  :
    isCheckedOut ? 'checked-out' : 'not-checked';

  const dotEmoji =
    isCheckedIn  ? '✅' :
    isCheckedOut ? '🏁' : '⏰';

  // Format utility using browser's local timezone
  const formatLocalDateTime = (dateStr) => {
    const date = parseUTCDate(dateStr);
    if (!date) return '—';
    return date.toLocaleString();
  };

  // Default coordinate center values (fallback to New Delhi)
  const defaultOfficeCoords = [28.6139, 77.2090];
  const officeCoords = officeSettings
    ? [officeSettings.latitude, officeSettings.longitude]
    : defaultOfficeCoords;
  const userCoords = userLocation
    ? [userLocation.latitude, userLocation.longitude]
    : null;

  return (
    <div className="fade-in">
      <style>{`
        .attendance-map-wrapper {
          height: 350px;
        }
        @media (max-width: 768px) {
          .attendance-map-wrapper {
            height: 250px;
          }
        }
      `}</style>

      <div className="page-header">
        <div className="page-header-left">
          <h2>Attendance</h2>
          <p>{new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
      </div>

      {/* Check-in Panel (All users) */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="checkin-panel">
          <div className={`checkin-status-dot ${dotClass}`}>{dotEmoji}</div>

          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
              {isCheckedIn  ? 'You are checked in' :
               isCheckedOut ? 'Work day complete'  : 'Not checked in yet'}
            </h3>
            {status?.check_in && (
              <p style={{ color: 'var(--text-muted)', marginTop: 6 }}>
                Check-in: {formatLocalDateTime(status.check_in)}
                {status.check_out && ` · Check-out: ${formatLocalDateTime(status.check_out)}`}
              </p>
            )}
            {isCheckedOut && (
              <div className="alert alert-info" style={{ marginTop: 10, marginBottom: 10, padding: '8px 12px', fontSize: 13, display: 'inline-flex' }}>
                ℹ️ You have already checked in for today.
              </div>
            )}
            {isCheckedIn && getLiveHours() && (
              <div style={{
                fontSize: 38, fontWeight: 800, color: 'var(--success)',
                fontFamily: 'monospace', marginTop: 8,
              }}>
                {getLiveHours()}
              </div>
            )}
            {status?.working_hours > 0 && isCheckedOut && (
              <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--info)', marginTop: 8 }}>
                {status.working_hours.toFixed(2)}h total
              </div>
            )}
          </div>

          {geoError && (
            <div className="alert alert-error" style={{ width: '100%', maxWidth: 420 }}>{geoError}</div>
          )}

          {debugInfo && (
            <div className="card" style={{ width: '100%', maxWidth: 420, padding: 16, marginTop: 12, fontSize: 13, textAlign: 'left', background: 'var(--bg-elevated)', border: '1px dashed var(--border)' }}>
              <strong style={{ color: 'var(--warning)', display: 'block', marginBottom: 8 }}>📍 Geofencing Debug Info:</strong>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div><strong>Your Latitude:</strong> {debugInfo.user_latitude}</div>
                <div><strong>Your Longitude:</strong> {debugInfo.user_longitude}</div>
                <div><strong>Office Latitude:</strong> {debugInfo.office_latitude}</div>
                <div><strong>Office Longitude:</strong> {debugInfo.office_longitude}</div>
                <div><strong>Distance:</strong> {debugInfo.distance_meters?.toFixed(2)} meters</div>
              </div>
            </div>
          )}

          {locationError && (
            <div className="alert alert-error" style={{ width: '100%', maxWidth: 600, margin: '10px 0' }}>
              ⚠️ {locationError}
            </div>
          )}

          {/* Telemetry Status Panel */}
          <div style={{ width: '100%', maxWidth: 700, margin: '0 auto 16px auto' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12 }}>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ClockIcon style={{ width: 14, height: 14 }} /> CURRENT LOCAL TIME
                </div>
                <div style={{ fontWeight: 600, fontSize: 12, marginTop: 4 }}>{currentTime}</div>
              </div>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <MapPinIcon style={{ width: 14, height: 14 }} /> LAST GPS UPDATE
                </div>
                <div style={{ fontWeight: 600, fontSize: 12, marginTop: 4 }}>{locationTimestamp || 'Waiting...'}</div>
              </div>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <SignalIcon style={{ width: 14, height: 14 }} /> GPS ACCURACY
                </div>
                <div style={{ fontWeight: 600, fontSize: 12, marginTop: 4 }}>
                  {userLocation ? `±${userLocation.accuracy.toFixed(1)}m` : 'N/A'}
                </div>
              </div>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <RulerIcon style={{ width: 14, height: 14 }} /> DISTANCE TO OFFICE
                </div>
                <div style={{ fontWeight: 600, fontSize: 12, marginTop: 4 }}>
                  {distance !== null ? `${distance.toFixed(1)} meters` : 'N/A'}
                </div>
              </div>
              <div style={{ background: 'var(--bg-elevated)', padding: 12, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheckIcon style={{ width: 14, height: 14 }} /> GEOFENCE STATUS
                </div>
                <div style={{ marginTop: 4 }}>
                  {locationError ? (
                    <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--danger)' }}></span>
                      Outside Geofence
                    </span>
                  ) : userLocation ? (
                    isInside ? (
                      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--success)' }}></span>
                        Within Geofence
                      </span>
                    ) : (
                      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--danger)' }}></span>
                        Outside Geofence
                      </span>
                    )
                  ) : (
                    <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--warning)' }}></span>
                      Detecting...
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Embedded Map Panel */}
          <div className="attendance-map-wrapper" style={{ width: '100%', maxWidth: 700, borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--border)', position: 'relative', zIndex: 1, marginBottom: 20 }}>
            <MapContainer center={officeCoords} zoom={15} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={officeCoords} icon={redIcon}>
                <Popup>
                  <strong>Office Location</strong><br/>
                  Coords: {officeCoords[0].toFixed(6)}, {officeCoords[1].toFixed(6)}<br/>
                  Radius: {officeSettings ? officeSettings.radius_meters : 200}m<br/>
                  Last Updated: {officeSettings ? new Date(officeSettings.updated_at).toLocaleString() : 'System Default'}
                </Popup>
              </Marker>
              {userCoords && (
                <Marker position={userCoords} icon={blueIcon}>
                  <Popup>
                    <strong>Your Location</strong><br/>
                    Coords: {userCoords[0].toFixed(6)}, {userCoords[1].toFixed(6)}<br/>
                    Accuracy: ±{userLocation.accuracy.toFixed(1)}m<br/>
                    Timestamp: {locationTimestamp}
                  </Popup>
                </Marker>
              )}
              <Circle
                center={officeCoords}
                radius={officeSettings ? officeSettings.radius_meters : 200}
                pathOptions={{ color: 'green', fillColor: 'green', fillOpacity: 0.15 }}
              />
              <MapRecenter currentLoc={userCoords} officeLoc={officeCoords} />
            </MapContainer>
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
            {!status?.check_in && (
              <button className="btn btn-success btn-lg" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }} onClick={handleCheckIn} disabled={checkingIn}>
                <MapPinIcon /> {checkingIn ? 'Getting location…' : 'Check In'}
              </button>
            )}
            {isCheckedIn && (
              <button className="btn btn-danger btn-lg" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }} onClick={handleCheckOut} disabled={checkingIn}>
                <FlagIcon /> {checkingIn ? 'Processing…' : 'Check Out'}
              </button>
            )}
            <button className="btn btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }} onClick={() => trackUserLocation(officeSettings)}>
              <RefreshIcon /> Refresh Location
            </button>
          </div>

          <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', maxWidth: 320, marginTop: 12 }}>
            📍 Check-in requires you to be within the allowed office radius.
            Make sure location permissions are enabled in your browser.
          </p>
        </div>
      </div>

      {/* History */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">📅 Attendance History</div>
        </div>

        <div className="search-filter-row" style={{ marginBottom: 16 }}>
          <div className="form-group" style={{ margin: 0 }}>
            <input type="month" className="form-control" value={month} onChange={(e) => { setMonth(e.target.value); setPage(1); }} />
          </div>
          {isAdmin && (
            <select className="form-control filter-select" value={empFilter} onChange={(e) => { setEmpFilter(e.target.value); setPage(1); }}>
              <option value="">All Employees</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
          )}
        </div>

        {loading ? <Spinner /> : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    {isAdmin && <th>Employee</th>}
                    <th>Date</th>
                    <th>Check In</th>
                    <th>Check Out</th>
                    <th>Working Hours</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.length === 0 && (
                    <tr><td colSpan={isAdmin ? 6 : 5}>
                      <div className="empty-state">
                        <div className="empty-state-icon"><InboxIcon style={{ width: 48, height: 48 }} /></div>
                        <h3>No records for this period</h3>
                      </div>
                    </td></tr>
                  )}
                  {history.map((r) => {
                    const hours = r.working_hours || 0;
                    return (
                      <tr key={r.id}>
                        {isAdmin && <td style={{ fontWeight: 600 }}>{r.employee_name}</td>}
                        <td style={{ fontWeight: 600 }}>{r.date}</td>
                        <td className="td-muted">{formatLocalDateTime(r.check_in)}</td>
                        <td className="td-muted">{formatLocalDateTime(r.check_out)}</td>
                        <td style={{
                          fontWeight: 700,
                          color: hours >= 8 ? 'var(--success)' : hours >= 4 ? 'var(--warning)' : hours > 0 ? 'var(--danger)' : 'var(--text-muted)',
                        }}>
                          {hours > 0 ? `${hours.toFixed(2)}h` : '—'}
                        </td>
                        <td>
                          <span className={`badge ${r.check_out ? 'badge-approved' : r.check_in ? 'badge-in-progress' : 'badge-pending'}`}>
                            {r.check_out ? 'Complete' : r.check_in ? 'In Progress' : 'Absent'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pages={pages} onPageChange={setPage} />
            {total > 0 && <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>{total} record{total !== 1 ? 's' : ''}</p>}
          </>
        )}
      </div>
    </div>
  );
}
