import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import AdminDashboard from './AdminDashboard';
import EmployeeDashboard from './EmployeeDashboard';

export default function Dashboard() {
  const { isAdmin } = useAuth();
  const [viewMode, setViewMode] = useState('admin');

  if (!isAdmin) {
    return <EmployeeDashboard />;
  }

  return (
    <div className="fade-in">
      <div className="dashboard-view-switcher" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16, gap: 8 }}>
        <button 
          className={`btn ${viewMode === 'admin' ? 'btn-primary' : 'btn-secondary'}`} 
          onClick={() => setViewMode('admin')}
        >
          💼 Admin Dashboard
        </button>
        <button 
          className={`btn ${viewMode === 'employee' ? 'btn-primary' : 'btn-secondary'}`} 
          onClick={() => setViewMode('employee')}
        >
          👤 My Employee View
        </button>
      </div>
      {viewMode === 'admin' ? <AdminDashboard /> : <EmployeeDashboard />}
    </div>
  );
}
