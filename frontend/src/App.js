/**
 * App.js
 * Root application: wraps providers and defines all routes.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './components/common/Toast';

import ProtectedRoute from './components/common/ProtectedRoute';
import MainLayout     from './components/layout/MainLayout';

import Login       from './pages/Login';
import Dashboard   from './pages/Dashboard';
import Employees   from './pages/Employees';
import Departments from './pages/Departments';
import Leaves      from './pages/Leaves';
import Attendance  from './pages/Attendance';
import Tasks       from './pages/Tasks';
import Meetings    from './pages/Meetings';
import Profile     from './pages/Profile';
import Settings    from './pages/Settings';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />

            {/* Protected — requires JWT */}
            <Route element={<ProtectedRoute />}>
              <Route element={<MainLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard"   element={<Dashboard />} />
                <Route path="/employees"   element={<Employees />} />
                <Route path="/departments" element={<Departments />} />
                <Route path="/leaves"      element={<Leaves />} />
                <Route path="/attendance"  element={<Attendance />} />
                <Route path="/tasks"       element={<Tasks />} />
                <Route path="/meetings"    element={<Meetings />} />
                <Route path="/profile"     element={<Profile />} />
                <Route path="/settings"    element={<Settings />} />
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
