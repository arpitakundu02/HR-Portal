/**
 * components/layout/MainLayout.js
 * Shell that wraps Sidebar + Header + page <Outlet />.
 */
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function MainLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <Header />
        <main className="page-content fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
