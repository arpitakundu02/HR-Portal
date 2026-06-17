/**
 * App.js
 * Root application: wraps providers and defines all routes.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './components/common/Toast';

import ProtectedRoute from './components/common/ProtectedRoute';
import RoleRoute      from './components/common/RoleRoute';
import MainLayout     from './components/layout/MainLayout';

import Login       from './pages/Login';
import Register    from './pages/Register';
import Dashboard   from './pages/Dashboard';
import Employees   from './pages/Employees';
import Departments from './pages/Departments';
import Leaves      from './pages/Leaves';
import Attendance  from './pages/Attendance';
import Tasks       from './pages/Tasks';
import Meetings    from './pages/Meetings';
import Profile     from './pages/Profile';
import Settings    from './pages/Settings';
import Holidays    from './pages/Holidays';
import WorkTransfers from './pages/WorkTransfers';
import RegistrationRequests from './pages/RegistrationRequests';
import CompOff     from './pages/CompOff';
import Approvals   from './pages/Approvals';
import Timesheets  from './pages/Timesheets';
import OrgChart    from './pages/OrgChart';
import Notifications from './pages/Notifications';
import EmployeeDetailDashboard from './pages/EmployeeDetailDashboard';
import Directory from './pages/Directory';
import Policies from './pages/Policies';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected — requires JWT */}
            <Route element={<ProtectedRoute />}>
              <Route element={<MainLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard"   element={<Dashboard />} />
                <Route path="/employees"   element={<Employees />} />
                <Route path="/employees/:id" element={<EmployeeDetailDashboard />} />
                <Route path="/departments" element={<Departments />} />
                <Route path="/leaves"      element={<Leaves />} />
                <Route path="/attendance"  element={<Attendance />} />
                <Route path="/tasks"       element={<Tasks />} />
                <Route path="/meetings"    element={<Meetings />} />
                <Route path="/profile"     element={<Profile />} />
                <Route path="/settings"    element={<Settings />} />
                <Route path="/holidays"    element={<Holidays />} />
                <Route path="/work-transfers" element={<WorkTransfers />} />
                <Route path="/comp-off"    element={<CompOff />} />
                <Route path="/approvals"   element={<Approvals />} />
                <Route path="/timesheets"  element={<Timesheets />} />
                <Route path="/org-chart"   element={<OrgChart />} />
                <Route path="/notifications" element={<Notifications />} />
                <Route path="/directory"   element={<Directory />} />
                <Route path="/policies"    element={<Policies />} />
                
                {/* Admin Only */}
                <Route path="/admin/registrations" element={
                  <RoleRoute roles={['Admin']}>
                    <RegistrationRequests />
                  </RoleRoute>
                } />
              </Route>
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
    </ThemeProvider>
  );
}
