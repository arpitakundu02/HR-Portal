/**
 * components/common/RoleRoute.js
 * Renders children only if user's role is in the allowed roles array.
 * Otherwise shows a 403 access-denied card.
 *
 * Usage: <RoleRoute roles={['Admin']}><AdminPage /></RoleRoute>
 */
import { useAuth } from '../../context/AuthContext';

export default function RoleRoute({ roles, children }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🚫</div>
        <h2 style={{ color: 'var(--danger)', marginBottom: 8 }}>Access Denied</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          You don't have permission to view this page.
        </p>
      </div>
    );
  }
  return children;
}
