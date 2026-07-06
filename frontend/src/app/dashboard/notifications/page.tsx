'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

const SEV_ICONS: Record<string, string> = { critical: '🚨', warning: '⚠️', info: 'ℹ️', success: '✅' };
const SEV_BG: Record<string, string> = { critical: 'rgba(239,68,68,0.12)', warning: 'rgba(245,158,11,0.12)', info: 'rgba(14,165,233,0.12)', success: 'rgba(6,214,160,0.12)' };
const TYPE_LABELS: Record<string, string> = {
  congestion: '🚗 Congestion', weather: '🌤️ Weather', emergency: '🚑 Emergency',
  ai_recommendation: '🤖 AI', system: '⚙️ System', signal_failure: '🚦 Signal'
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const loadNotifications = () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (filterType) params.set('notification_type', filterType);
    if (filterSeverity) params.set('severity', filterSeverity);
    if (showUnreadOnly) params.set('is_read', 'false');
    Promise.all([
      api.getNotifications(params.toString()),
      api.getUnreadCount(),
    ]).then(([data, count]) => {
      setNotifications(data?.notifications || []);
      setTotal(data?.total || 0);
      setUnreadCount(count?.unread_count || 0);
      setLoading(false);
    }).catch((err) => {
      setError(err.message || 'Failed to load notifications');
      setLoading(false);
    });
  };

  useEffect(() => { loadNotifications(); }, [filterType, filterSeverity, showUnreadOnly]);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markRead(id);
      loadNotifications();
    } catch (err: any) { alert(err.message || 'Failed to mark as read'); }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllRead();
      loadNotifications();
    } catch (err: any) { alert(err.message || 'Failed to mark all as read'); }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteNotification(id);
      loadNotifications();
    } catch (err: any) { alert(err.message || 'Failed to delete notification'); }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="page-title">Notification Center</h1>
            <p className="page-description">
              {total} total • {unreadCount} unread
            </p>
          </div>
          {unreadCount > 0 && (
            <button className="btn btn-primary" onClick={handleMarkAllRead}>
              ✅ Mark All Read
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <button
          className={`filter-chip ${showUnreadOnly ? 'active' : ''}`}
          onClick={() => setShowUnreadOnly(!showUnreadOnly)}
        >
          📬 Unread Only
        </button>
        <select className="select-field" style={{ width: 150 }} value={filterType} onChange={e => setFilterType(e.target.value)}>
          <option value="">All Types</option>
          <option value="congestion">Congestion</option>
          <option value="weather">Weather</option>
          <option value="emergency">Emergency</option>
          <option value="ai_recommendation">AI</option>
          <option value="system">System</option>
          <option value="signal_failure">Signal</option>
        </select>
        <select className="select-field" style={{ width: 150 }} value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
          <option value="success">Success</option>
        </select>
        {(filterType || filterSeverity || showUnreadOnly) && (
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => { setFilterType(''); setFilterSeverity(''); setShowUnreadOnly(false); }}
          >
            ✕ Clear Filters
          </button>
        )}
      </div>

      {/* Notification List */}
      {loading ? (
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading notifications...</p></div>
      ) : error ? (
        <div className="error-state">
          <div className="error-state-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={loadNotifications}>🔄 Retry</button>
        </div>
      ) : notifications.length === 0 ? (
        <div className="glass-card-static empty-state">
          <div className="empty-state-icon">🔕</div>
          <p>{showUnreadOnly ? 'No unread notifications' : 'No notifications found'}</p>
        </div>
      ) : (
        <div className="glass-card-static" style={{ overflow: 'hidden' }}>
          {notifications.map(n => (
            <div key={n.id} className={`notification-item ${!n.is_read ? 'unread' : ''}`}>
              <div className="notification-icon-wrapper" style={{ background: SEV_BG[n.severity] || SEV_BG.info }}>
                {SEV_ICONS[n.severity] || 'ℹ️'}
              </div>
              <div className="notification-body" style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                  <div className="notification-title">{n.title || 'Notification'}</div>
                  <span className={`badge ${n.severity === 'critical' ? 'badge-critical' : n.severity === 'warning' ? 'badge-warning' : n.severity === 'success' ? 'badge-success' : 'badge-info'}`} style={{ fontSize: 10 }}>
                    {n.severity || 'info'}
                  </span>
                  {TYPE_LABELS[n.type] && (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{TYPE_LABELS[n.type]}</span>
                  )}
                </div>
                <div className="notification-message">{n.message || ''}</div>
                <div className="notification-time">{n.created_at ? new Date(n.created_at).toLocaleString() : '—'}</div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexShrink: 0, alignItems: 'center' }}>
                {!n.is_read && (
                  <button className="btn btn-sm btn-secondary" onClick={() => handleMarkRead(n.id)} title="Mark as read">
                    ✓
                  </button>
                )}
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(n.id)} title="Delete">
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
