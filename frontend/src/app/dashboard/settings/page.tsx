'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth';

type TabId = 'profile' | 'security' | 'system';

const TABS: { id: TabId; label: string }[] = [
  { id: 'profile', label: '👤 Profile' },
  { id: 'security', label: '🔒 Security' },
  { id: 'system', label: '⚙️ System' },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<TabId>('profile');

  // Profile state
  const [profile, setProfile] = useState({
    full_name: '', phone: '', department: '', avatar_url: '',
  });
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Security state
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // System state
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [aiHealth, setAiHealth] = useState<any>(null);
  const [systemLoading, setSystemLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    try {
      const data = await api.getProfile();
      setProfile({
        full_name: data.full_name || '',
        phone: data.phone || '',
        department: data.department || '',
        avatar_url: data.avatar_url || '',
      });
    } catch {
      setProfileMsg({ type: 'error', text: 'Failed to load profile' });
    }
    setProfileLoading(false);
  }, []);

  const loadSystem = useCallback(async () => {
    setSystemLoading(true);
    try {
      const [health, aiH] = await Promise.all([
        api.fetch('/health', { skipAuth: true }).catch(() => null),
        api.getAIHealth().catch(() => null),
      ]);
      setSystemInfo(health);
      setAiHealth(aiH);
    } catch {
      // Silently handle
    }
    setSystemLoading(false);
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (tab === 'system') loadSystem();
  }, [tab, loadSystem]);

  const handleProfileSave = async () => {
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      await api.updateProfile(profile);
      setProfileMsg({ type: 'success', text: 'Profile updated successfully!' });
      // Update local storage user data
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          const u = JSON.parse(storedUser);
          u.full_name = profile.full_name;
          u.department = profile.department;
          localStorage.setItem('user', JSON.stringify(u));
        } catch { /* ignore */ }
      }
    } catch (err: any) {
      setProfileMsg({ type: 'error', text: err.message || 'Failed to update profile' });
    }
    setProfileSaving(false);
  };

  const handlePasswordChange = async () => {
    setPasswordMsg(null);
    if (passwords.new_password !== passwords.confirm_password) {
      setPasswordMsg({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    if (passwords.new_password.length < 6) {
      setPasswordMsg({ type: 'error', text: 'New password must be at least 6 characters' });
      return;
    }
    setPasswordSaving(true);
    try {
      await api.changePassword(passwords.current_password, passwords.new_password);
      setPasswordMsg({ type: 'success', text: 'Password changed successfully!' });
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err: any) {
      setPasswordMsg({ type: 'error', text: err.message || 'Failed to change password' });
    }
    setPasswordSaving(false);
  };

  const initials = user?.full_name?.split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase() || 'U';

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-description">Manage your profile, security, and system preferences</p>
      </div>

      {/* Tabs */}
      <div className="tab-bar">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-item ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <div className="settings-section animate-in">
          <div className="grid-2">
            {/* Avatar & Info Card */}
            <div className="glass-card" style={{ padding: 32 }}>
              <h3 className="chart-title">📇 User Information</h3>
              <div className="settings-avatar-section">
                <div className="settings-avatar-large">{initials}</div>
                <div className="settings-avatar-info">
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-white)' }}>
                    {user?.full_name || 'User'}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {user?.email}
                  </div>
                  <span className="badge badge-info" style={{ marginTop: 8, display: 'inline-flex', textTransform: 'capitalize' }}>
                    {user?.role?.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </div>

            {/* Edit Profile Form */}
            <div className="glass-card" style={{ padding: 32 }}>
              <h3 className="chart-title">✏️ Edit Profile</h3>
              {profileLoading ? (
                <div className="loading-container" style={{ padding: '40px 20px' }}>
                  <div className="spinner" />
                  <p className="loading-text">Loading profile...</p>
                </div>
              ) : (
                <>
                  {profileMsg && (
                    <div className={`settings-toast ${profileMsg.type}`}>
                      {profileMsg.type === 'success' ? '✅' : '⚠️'} {profileMsg.text}
                    </div>
                  )}
                  <div className="form-group">
                    <label className="input-label">Full Name</label>
                    <input
                      className="input-field"
                      value={profile.full_name}
                      onChange={e => setProfile({ ...profile, full_name: e.target.value })}
                      placeholder="Your full name"
                    />
                  </div>
                  <div className="form-group">
                    <label className="input-label">Department</label>
                    <select
                      className="select-field"
                      value={profile.department}
                      onChange={e => setProfile({ ...profile, department: e.target.value })}
                    >
                      <option value="">Select Department</option>
                      <option value="Traffic Control">Traffic Control</option>
                      <option value="Emergency Services">Emergency Services</option>
                      <option value="IT Operations">IT Operations</option>
                      <option value="City Planning">City Planning</option>
                      <option value="Public Safety">Public Safety</option>
                      <option value="Analytics">Analytics</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="input-label">Phone</label>
                    <input
                      className="input-field"
                      value={profile.phone}
                      onChange={e => setProfile({ ...profile, phone: e.target.value })}
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                  <button
                    className="btn btn-primary btn-lg"
                    style={{ width: '100%', marginTop: 4 }}
                    onClick={handleProfileSave}
                    disabled={profileSaving || !profile.full_name}
                  >
                    {profileSaving ? '⏳ Saving...' : '💾 Save Changes'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {tab === 'security' && (
        <div className="settings-section animate-in">
          <div style={{ maxWidth: 560 }}>
            <div className="glass-card" style={{ padding: 32 }}>
              <h3 className="chart-title">🔐 Change Password</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
                Ensure your account is using a strong, unique password for security.
              </p>

              {passwordMsg && (
                <div className={`settings-toast ${passwordMsg.type}`}>
                  {passwordMsg.type === 'success' ? '✅' : '⚠️'} {passwordMsg.text}
                </div>
              )}

              <div className="form-group">
                <label className="input-label">Current Password</label>
                <input
                  className="input-field"
                  type="password"
                  value={passwords.current_password}
                  onChange={e => setPasswords({ ...passwords, current_password: e.target.value })}
                  placeholder="Enter current password"
                  autoComplete="current-password"
                />
              </div>
              <div className="form-group">
                <label className="input-label">New Password</label>
                <input
                  className="input-field"
                  type="password"
                  value={passwords.new_password}
                  onChange={e => setPasswords({ ...passwords, new_password: e.target.value })}
                  placeholder="Enter new password (min 6 chars)"
                  autoComplete="new-password"
                />
              </div>
              <div className="form-group">
                <label className="input-label">Confirm New Password</label>
                <input
                  className="input-field"
                  type="password"
                  value={passwords.confirm_password}
                  onChange={e => setPasswords({ ...passwords, confirm_password: e.target.value })}
                  placeholder="Confirm new password"
                  autoComplete="new-password"
                />
              </div>

              {/* Password strength indicator */}
              {passwords.new_password && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
                    {[1, 2, 3, 4].map(level => (
                      <div
                        key={level}
                        className="password-strength-bar"
                        style={{
                          background:
                            passwords.new_password.length >= level * 3
                              ? level <= 1 ? 'var(--status-danger)' : level <= 2 ? 'var(--status-warning)' : 'var(--status-success)'
                              : 'rgba(255,255,255,0.08)',
                        }}
                      />
                    ))}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {passwords.new_password.length < 6 ? 'Too short' : passwords.new_password.length < 9 ? 'Fair' : passwords.new_password.length < 12 ? 'Good' : 'Strong'}
                  </div>
                </div>
              )}

              <button
                className="btn btn-primary btn-lg"
                style={{ width: '100%' }}
                onClick={handlePasswordChange}
                disabled={passwordSaving || !passwords.current_password || !passwords.new_password || !passwords.confirm_password}
              >
                {passwordSaving ? '⏳ Changing...' : '🔑 Change Password'}
              </button>
            </div>

            {/* Security Tips */}
            <div className="glass-card" style={{ padding: 24, marginTop: 20 }}>
              <h3 className="chart-title">🛡️ Security Tips</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                {[
                  { icon: '🔤', tip: 'Use a mix of uppercase, lowercase, numbers, and symbols' },
                  { icon: '📏', tip: 'Make your password at least 12 characters long' },
                  { icon: '🔄', tip: 'Don\'t reuse passwords across different accounts' },
                  { icon: '📱', tip: 'Enable two-factor authentication when available' },
                ].map((item, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '10px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: 20 }}>{item.icon}</span>
                    <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{item.tip}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Tab */}
      {tab === 'system' && (
        <div className="settings-section animate-in">
          {systemLoading ? (
            <div className="loading-container">
              <div className="spinner" />
              <p className="loading-text">Loading system info...</p>
            </div>
          ) : (
            <>
              {/* System Status Cards */}
              <div className="grid-4" style={{ marginBottom: 24 }}>
                <div className="glass-card kpi-card">
                  <div className="kpi-icon green">💚</div>
                  <div className="kpi-content">
                    <div className="kpi-label">API Status</div>
                    <div className="kpi-value" style={{ fontSize: 20, color: systemInfo ? 'var(--status-success)' : 'var(--status-danger)' }}>
                      {systemInfo ? 'Online' : 'Offline'}
                    </div>
                  </div>
                </div>
                <div className="glass-card kpi-card">
                  <div className="kpi-icon blue">🤖</div>
                  <div className="kpi-content">
                    <div className="kpi-label">AI Engine</div>
                    <div className="kpi-value" style={{ fontSize: 20, color: aiHealth ? 'var(--status-success)' : 'var(--status-warning)' }}>
                      {aiHealth ? `${aiHealth.health_score}%` : 'N/A'}
                    </div>
                  </div>
                </div>
                <div className="glass-card kpi-card">
                  <div className="kpi-icon purple">📊</div>
                  <div className="kpi-content">
                    <div className="kpi-label">Data Points</div>
                    <div className="kpi-value" style={{ fontSize: 20 }}>
                      {aiHealth?.total_data_points?.toLocaleString() || '—'}
                    </div>
                  </div>
                </div>
                <div className="glass-card kpi-card">
                  <div className="kpi-icon amber">🎯</div>
                  <div className="kpi-content">
                    <div className="kpi-label">Model Accuracy</div>
                    <div className="kpi-value" style={{ fontSize: 20 }}>
                      {aiHealth?.metrics?.model_accuracy ? `${aiHealth.metrics.model_accuracy}%` : '—'}
                    </div>
                  </div>
                </div>
              </div>

              {/* System Details */}
              <div className="grid-2">
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 className="chart-title">🖥️ System Information</h3>
                  <div className="settings-info-list">
                    <div className="settings-info-row">
                      <span className="settings-info-label">Platform</span>
                      <span className="settings-info-value">Smart City Traffic Optimisation System</span>
                    </div>
                    <div className="settings-info-row">
                      <span className="settings-info-label">API Version</span>
                      <span className="settings-info-value">v1</span>
                    </div>
                    <div className="settings-info-row">
                      <span className="settings-info-label">Backend</span>
                      <span className="settings-info-value">FastAPI + SQLite</span>
                    </div>
                    <div className="settings-info-row">
                      <span className="settings-info-label">Frontend</span>
                      <span className="settings-info-value">Next.js 14 + React 18</span>
                    </div>
                    <div className="settings-info-row">
                      <span className="settings-info-label">AI Engine</span>
                      <span className="settings-info-value">{aiHealth?.status || 'Unknown'}</span>
                    </div>
                  </div>
                </div>

                {/* AI Capabilities */}
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 className="chart-title">🧠 AI Capabilities</h3>
                  {aiHealth?.capabilities ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                      {aiHealth.capabilities.map((cap: string, i: number) => (
                        <span key={i} className="badge badge-info" style={{ padding: '6px 14px' }}>{cap}</span>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state" style={{ padding: '40px 20px' }}>
                      <div className="empty-state-icon">🤖</div>
                      <p>AI engine status unavailable</p>
                    </div>
                  )}

                  {aiHealth?.metrics && (
                    <div style={{ marginTop: 20 }}>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>Performance Metrics</div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                        {[
                          { label: 'Accuracy', value: `${aiHealth.metrics.model_accuracy}%`, color: '#06d6a0' },
                          { label: 'Uptime', value: `${aiHealth.metrics.system_uptime}%`, color: '#0ea5e9' },
                          { label: 'Avg Response', value: `${aiHealth.metrics.avg_response_time || '—'}ms`, color: '#8b5cf6' },
                          { label: 'Optimizations', value: aiHealth.metrics.total_optimizations?.toLocaleString() || '—', color: '#f59e0b' },
                        ].map((m, i) => (
                          <div key={i} style={{ padding: 12, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: m.color }}>{m.value}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{m.label}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Account Info */}
              <div className="glass-card" style={{ padding: 24, marginTop: 20 }}>
                <h3 className="chart-title">👤 Account Details</h3>
                <div className="settings-info-list">
                  <div className="settings-info-row">
                    <span className="settings-info-label">Username</span>
                    <span className="settings-info-value">{user?.username || '—'}</span>
                  </div>
                  <div className="settings-info-row">
                    <span className="settings-info-label">Email</span>
                    <span className="settings-info-value">{user?.email || '—'}</span>
                  </div>
                  <div className="settings-info-row">
                    <span className="settings-info-label">Role</span>
                    <span className="settings-info-value" style={{ textTransform: 'capitalize' }}>{user?.role?.replace('_', ' ') || '—'}</span>
                  </div>
                  <div className="settings-info-row">
                    <span className="settings-info-label">Department</span>
                    <span className="settings-info-value">{user?.department || '—'}</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
