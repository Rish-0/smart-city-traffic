'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';

const NAV_ITEMS = [
  { label: 'Overview', icon: '📊', href: '/dashboard' },
  { label: 'Traffic', icon: '🚗', href: '/dashboard/traffic' },
  { label: 'AI Optimization', icon: '🤖', href: '/dashboard/ai-optimization' },
  { label: 'Analytics', icon: '📈', href: '/dashboard/analytics' },
  { label: 'Emergency', icon: '🚑', href: '/dashboard/emergency' },
  { label: 'Incidents', icon: '⚠️', href: '/dashboard/incidents' },
  { label: 'Notifications', icon: '🔔', href: '/dashboard/notifications' },
  { label: 'Settings', icon: '⚙️', href: '/dashboard/settings' },
];

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard Overview',
  '/dashboard/traffic': 'Traffic Monitoring',
  '/dashboard/ai-optimization': 'AI Signal Optimization',
  '/dashboard/analytics': 'Traffic Analytics',
  '/dashboard/emergency': 'Emergency Management',
  '/dashboard/incidents': 'Incident Management',
  '/dashboard/notifications': 'Notification Center',
  '/dashboard/settings': 'Settings',
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, loading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      api.getUnreadCount().then(d => setUnreadCount(d.unread_count)).catch(() => {});
    }
  }, [isAuthenticated, pathname]);

  if (loading || !isAuthenticated) {
    return (
      <div className="login-wrapper">
        <div className="loading-container">
          <div className="spinner" />
          <p className="loading-text">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const currentTitle = PAGE_TITLES[pathname] || 'Dashboard';
  const initials = user?.full_name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'U';

  return (
    <div className="dashboard-layout">
      {/* Mobile overlay */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-logo">🚦</span>
          <div className="sidebar-brand">
            <h2>Traffic Control</h2>
            <span>Smart City Platform</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Main Menu</div>
          {NAV_ITEMS.map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item ${pathname === item.href ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.label === 'Notifications' && unreadCount > 0 && (
                <span className="badge badge-danger" style={{ marginLeft: 'auto', fontSize: 11, padding: '2px 8px' }}>
                  {unreadCount}
                </span>
              )}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user" onClick={logout}>
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.full_name}</div>
              <div className="sidebar-user-role">{user?.role?.replace('_', ' ')}</div>
            </div>
            <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>🚪</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
              ☰
            </button>
            <div className="topbar-breadcrumb">
              Dashboard / <span>{currentTitle}</span>
            </div>
          </div>
          <div className="topbar-right">
            <Link href="/dashboard/notifications" className="topbar-btn" title="Notifications">
              🔔
              {unreadCount > 0 && <span className="notification-dot" />}
            </Link>
            <button className="topbar-btn" onClick={logout} title="Logout">
              🚪
            </button>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
