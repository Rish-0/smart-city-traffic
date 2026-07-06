'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import dynamic from 'next/dynamic';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const MapComponent = dynamic(() => import('./MapComponent'), { ssr: false });

const COLORS = ['#06d6a0', '#f59e0b', '#f97316', '#ef4444'];
const CONGESTION_COLORS: Record<string, string> = {
  Low: '#06d6a0', Moderate: '#f59e0b', High: '#f97316', Critical: '#ef4444'
};

export default function DashboardOverview() {
  const [summary, setSummary] = useState<any>(null);
  const [currentTraffic, setCurrentTraffic] = useState<any>(null);
  const [intersections, setIntersections] = useState<any[]>([]);
  const [hourly, setHourly] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getAnalyticsSummary().catch(() => null),
      api.getCurrentTraffic().catch(() => null),
      api.getIntersections().catch(() => null),
      api.getHourlyAnalytics().catch(() => null),
      api.getNotifications('limit=5').catch(() => null),
    ]).then(([sum, traffic, ints, hourlyData, notifs]) => {
      if (!sum && !traffic && !ints) {
        setError('Unable to connect to the backend server. Make sure the API is running on port 8000.');
      }
      setSummary(sum);
      setCurrentTraffic(traffic);
      setIntersections(ints?.intersections || []);
      setHourly(hourlyData?.data || []);
      setNotifications(notifs?.notifications || []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading dashboard...</p></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-state">
          <div className="error-state-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>🔄 Retry</button>
        </div>
      </div>
    );
  }

  const congestionData = summary?.congestion_distribution
    ? Object.entries(summary.congestion_distribution).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Dashboard Overview</h1>
        <p className="page-description">Real-time traffic monitoring and system health at a glance</p>
      </div>

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="glass-card kpi-card animate-in">
          <div className="kpi-icon green">🚗</div>
          <div className="kpi-content">
            <div className="kpi-label">Total Volume</div>
            <div className="kpi-value">{(summary?.avg_volume || 0).toLocaleString()}</div>
            <div className="kpi-subtitle">avg vehicles/interval</div>
          </div>
        </div>
        <div className="glass-card kpi-card animate-in" style={{ animationDelay: '0.1s' }}>
          <div className="kpi-icon blue">🏎️</div>
          <div className="kpi-content">
            <div className="kpi-label">Avg Speed</div>
            <div className="kpi-value">{summary?.avg_speed || 0} <span style={{ fontSize: 14, fontWeight: 400 }}>km/h</span></div>
            <div className="kpi-subtitle">across all intersections</div>
          </div>
        </div>
        <div className="glass-card kpi-card animate-in" style={{ animationDelay: '0.2s' }}>
          <div className="kpi-icon amber">⏱️</div>
          <div className="kpi-content">
            <div className="kpi-label">Avg Wait Time</div>
            <div className="kpi-value">{summary?.avg_wait_time || 0} <span style={{ fontSize: 14, fontWeight: 400 }}>min</span></div>
            <div className="kpi-subtitle">signal delay</div>
          </div>
        </div>
        <div className="glass-card kpi-card animate-in" style={{ animationDelay: '0.3s' }}>
          <div className="kpi-icon red">📊</div>
          <div className="kpi-content">
            <div className="kpi-label">Data Records</div>
            <div className="kpi-value">{(summary?.total_records || 0).toLocaleString()}</div>
            <div className="kpi-subtitle">metro + simulation</div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Hourly Traffic Chart */}
        <div className="glass-card chart-container animate-in" style={{ animationDelay: '0.4s' }}>
          <h3 className="chart-title">📈 Hourly Traffic Pattern</h3>
          {hourly.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={hourly}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="label" tick={{ fill: '#8892a8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} />
                <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} />
                <Tooltip
                  contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }}
                  labelStyle={{ color: '#8892a8' }}
                />
                <Bar dataKey="avg_volume" fill="#06d6a0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-state-icon">📊</div>
              <p>No hourly data available</p>
            </div>
          )}
        </div>

        {/* Congestion Distribution */}
        <div className="glass-card chart-container animate-in" style={{ animationDelay: '0.5s' }}>
          <h3 className="chart-title">🎯 Congestion Distribution</h3>
          {congestionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={congestionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {congestionData.map((entry: any, idx: number) => (
                    <Cell key={idx} fill={CONGESTION_COLORS[entry.name] || COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                <Legend wrapperStyle={{ color: '#8892a8', fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-state-icon">🎯</div>
              <p>No congestion data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Map + Recent Alerts */}
      <div className="grid-2">
        {/* Intersection Map */}
        <div className="glass-card animate-in" style={{ animationDelay: '0.6s', overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px 12px' }}>
            <h3 className="chart-title" style={{ marginBottom: 0 }}>🗺️ Intersection Map</h3>
          </div>
          <MapComponent intersections={intersections} />
        </div>

        {/* Recent Notifications */}
        <div className="glass-card animate-in" style={{ animationDelay: '0.7s' }}>
          <div style={{ padding: '20px 24px 12px' }}>
            <h3 className="chart-title" style={{ marginBottom: 0 }}>🔔 Recent Alerts</h3>
          </div>
          <div>
            {notifications.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔕</div>
                <p>No recent notifications</p>
              </div>
            ) : (
              notifications.map((n: any) => {
                const sevColors: Record<string, string> = { critical: 'rgba(239,68,68,0.12)', warning: 'rgba(245,158,11,0.12)', info: 'rgba(14,165,233,0.12)', success: 'rgba(6,214,160,0.12)' };
                const sevIcons: Record<string, string> = { critical: '🚨', warning: '⚠️', info: 'ℹ️', success: '✅' };
                return (
                  <div key={n.id} className={`notification-item ${!n.is_read ? 'unread' : ''}`}>
                    <div className="notification-icon-wrapper" style={{ background: sevColors[n.severity] || sevColors.info }}>
                      {sevIcons[n.severity] || 'ℹ️'}
                    </div>
                    <div className="notification-body">
                      <div className="notification-title">{n.title}</div>
                      <div className="notification-message">{n.message}</div>
                      <div className="notification-time">{new Date(n.created_at).toLocaleString()}</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
