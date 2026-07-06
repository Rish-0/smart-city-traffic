'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  available: 'badge-success', dispatched: 'badge-warning', en_route: 'badge-info',
  on_scene: 'badge-danger', returning: 'badge-purple'
};

const TYPE_ICONS: Record<string, string> = {
  ambulance: '🚑', police: '🚔', fire_truck: '🚒'
};

const TYPE_BG: Record<string, string> = {
  ambulance: 'rgba(239,68,68,0.12)', police: 'rgba(14,165,233,0.12)', fire_truck: 'rgba(245,158,11,0.12)'
};

export default function EmergencyPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getEmergencyDashboard().catch(() => null),
      api.getEmergencyVehicles().catch(() => null),
    ]).then(([dash, vehs]) => {
      if (!dash && !vehs) {
        setError('Unable to load emergency data. Make sure the backend is running.');
      }
      setDashboard(dash);
      setVehicles(vehs?.vehicles || []);
      setLoading(false);
    });
  };

  useEffect(() => { loadData(); }, []);

  const handleTogglePriority = async (vehicleId: number, currentPriority: number) => {
    try {
      await api.togglePriority(vehicleId, currentPriority === 0);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to toggle priority');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading emergency data...</p></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">Emergency Management</h1>
        </div>
        <div className="error-state">
          <div className="error-state-icon">🚑</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={loadData}>🔄 Retry</button>
        </div>
      </div>
    );
  }

  const filtered = vehicles.filter(v => {
    if (filterType && v.type !== filterType) return false;
    if (filterStatus && v.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="page-title">Emergency Management</h1>
            <p className="page-description">Emergency vehicle tracking and priority signal control</p>
          </div>
          <button className="btn btn-secondary" onClick={loadData}>🔄 Refresh</button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="glass-card kpi-card">
          <div className="kpi-icon blue">🚐</div>
          <div className="kpi-content">
            <div className="kpi-label">Total Vehicles</div>
            <div className="kpi-value">{dashboard?.total_vehicles ?? 0}</div>
          </div>
        </div>
        <div className="glass-card kpi-card">
          <div className="kpi-icon green">✅</div>
          <div className="kpi-content">
            <div className="kpi-label">Available</div>
            <div className="kpi-value">{vehicles.filter(v => v.status === 'available').length}</div>
          </div>
        </div>
        <div className="glass-card kpi-card">
          <div className="kpi-icon red">🚨</div>
          <div className="kpi-content">
            <div className="kpi-label">Active Calls</div>
            <div className="kpi-value">{dashboard?.active_count ?? 0}</div>
          </div>
        </div>
        <div className="glass-card kpi-card">
          <div className="kpi-icon amber">🚦</div>
          <div className="kpi-content">
            <div className="kpi-label">Priority Signals</div>
            <div className="kpi-value">{dashboard?.priority_signals_active ?? 0}</div>
          </div>
        </div>
      </div>

      {/* Active Emergencies */}
      {dashboard?.active_emergencies && dashboard.active_emergencies.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 className="section-title" style={{ marginBottom: 16 }}>🚨 Active Emergencies</h3>
          <div className="grid-3">
            {dashboard.active_emergencies.map((v: any) => (
              <div key={v.id} className="glass-card emergency-card pulse-active">
                <div className="emergency-icon-wrapper" style={{ background: TYPE_BG[v.type] || 'rgba(255,255,255,0.06)' }}>
                  {TYPE_ICONS[v.type] || '🚐'}
                </div>
                <div className="emergency-details">
                  <div className="emergency-callsign">{v.call_sign || 'Unknown'}</div>
                  <div className="emergency-info">{v.destination || 'En route'}</div>
                  <div className="emergency-info">
                    Near {v.nearest_junction || '—'} {v.eta_minutes ? `• ETA ${v.eta_minutes} min` : ''}
                  </div>
                  <span className={`badge ${STATUS_COLORS[v.status] || 'badge-info'}`} style={{ marginTop: 6, display: 'inline-flex' }}>
                    {(v.status || 'unknown').replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fleet by Type */}
      {dashboard?.by_type && Object.keys(dashboard.by_type).length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 className="section-title" style={{ marginBottom: 16 }}>📊 Fleet Overview</h3>
          <div className="grid-3">
            {Object.entries(dashboard.by_type).map(([type, data]: [string, any]) => (
              <div key={type} className="glass-card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <span style={{ fontSize: 28 }}>{TYPE_ICONS[type] || '🚐'}</span>
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-white)', fontSize: 16, textTransform: 'capitalize' }}>{type.replace('_', ' ')}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{data?.total ?? 0} units</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  <div style={{ flex: 1, textAlign: 'center', padding: 10, background: 'rgba(6,214,160,0.08)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--status-success)' }}>{data?.available ?? 0}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Available</div>
                  </div>
                  <div style={{ flex: 1, textAlign: 'center', padding: 10, background: 'rgba(239,68,68,0.08)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--status-danger)' }}>{data?.active ?? 0}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Active</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Vehicles Table */}
      <div className="glass-card-static" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="section-title" style={{ margin: 0 }}>🚐 All Vehicles</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <select className="select-field" style={{ width: 140 }} value={filterType} onChange={e => setFilterType(e.target.value)}>
              <option value="">All Types</option>
              <option value="ambulance">Ambulance</option>
              <option value="police">Police</option>
              <option value="fire_truck">Fire Truck</option>
            </select>
            <select className="select-field" style={{ width: 140 }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
              <option value="">All Statuses</option>
              <option value="available">Available</option>
              <option value="dispatched">Dispatched</option>
              <option value="en_route">En Route</option>
              <option value="on_scene">On Scene</option>
              <option value="returning">Returning</option>
            </select>
          </div>
        </div>
        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🚐</div>
            <p>No vehicles match the current filters</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Call Sign</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Destination</th>
                  <th>Near</th>
                  <th>ETA</th>
                  <th>Priority</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((v: any) => (
                  <tr key={v.id}>
                    <td><strong style={{ color: 'var(--text-white)' }}>{v.call_sign || '—'}</strong></td>
                    <td>{TYPE_ICONS[v.type] || '🚐'} <span style={{ textTransform: 'capitalize' }}>{(v.type || 'unknown').replace('_', ' ')}</span></td>
                    <td><span className={`badge ${STATUS_COLORS[v.status] || 'badge-info'}`}>{(v.status || 'unknown').replace('_', ' ')}</span></td>
                    <td>{v.destination_name || '—'}</td>
                    <td>{v.nearest_junction || '—'}</td>
                    <td>{v.eta_minutes ? `${v.eta_minutes} min` : '—'}</td>
                    <td>
                      {v.priority_active ? (
                        <span className="badge badge-danger">🔴 Active</span>
                      ) : (
                        <span className="badge badge-success">🟢 Off</span>
                      )}
                    </td>
                    <td>
                      <button
                        className={`btn btn-sm ${v.priority_active ? 'btn-danger' : 'btn-primary'}`}
                        onClick={() => handleTogglePriority(v.id, v.priority_active ? 1 : 0)}
                      >
                        {v.priority_active ? '⏹️ Deactivate' : '🚨 Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
