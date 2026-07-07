'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

const CONGESTION_BADGE: Record<string, string> = {
  Low: 'badge-success', Moderate: 'badge-warning', High: 'badge-danger', Critical: 'badge-critical'
};

export default function TrafficPage() {
  const [currentTraffic, setCurrentTraffic] = useState<any>(null);
  const [intersections, setIntersections] = useState<any[]>([]);
  const [filterZone, setFilterZone] = useState('');
  const [filterCongestion, setFilterCongestion] = useState('');
  const [dataSource, setDataSource] = useState('simulation');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getCurrentTraffic(dataSource).catch(() => null),
      api.getIntersections(dataSource).catch(() => null),
    ]).then(([traffic, ints]) => {
      if (!traffic && !ints) {
        setError('Unable to load traffic data. Make sure the backend is running.');
      }
      setCurrentTraffic(traffic);
      setIntersections(ints?.intersections || []);
      setLoading(false);
    });
  };

  useEffect(() => { loadData(); }, [dataSource]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading traffic data...</p></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">Traffic Monitoring</h1>
        </div>
        <div className="error-state">
          <div className="error-state-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={loadData}>🔄 Retry</button>
        </div>
      </div>
    );
  }

  const filteredIntersections = intersections.filter(i => {
    if (filterZone && i.zone !== filterZone) return false;
    if (filterCongestion && i.congestion_level !== filterCongestion) return false;
    return true;
  });

  const zones = [...new Set(intersections.map(i => i.zone))].sort();

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="page-title">Traffic Monitoring</h1>
            <p className="page-description">Real-time intersection data and signal status</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '8px', display: 'flex', border: '1px solid rgba(255,255,255,0.1)' }}>
              <button 
                className={`btn ${dataSource === 'simulation' ? 'btn-primary' : ''}`}
                style={{ background: dataSource === 'simulation' ? '' : 'transparent', border: 'none', padding: '6px 12px' }}
                onClick={() => setDataSource('simulation')}
              >
                🎮 Simulation
              </button>
              <button 
                className={`btn ${dataSource === 'tomtom_live' ? 'btn-primary' : ''}`}
                style={{ background: dataSource === 'tomtom_live' ? '' : 'transparent', border: 'none', padding: '6px 12px' }}
                onClick={() => setDataSource('tomtom_live')}
              >
                📡 Live (TomTom)
              </button>
            </div>
            <button className="btn btn-secondary" onClick={loadData}>🔄 Refresh</button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {currentTraffic?.summary && (
        <div className="grid-4" style={{ marginBottom: 24 }}>
          <div className="glass-card kpi-card">
            <div className="kpi-icon green">🏙️</div>
            <div className="kpi-content">
              <div className="kpi-label">Intersections</div>
              <div className="kpi-value">{currentTraffic.summary.total_intersections ?? 0}</div>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon blue">🚗</div>
            <div className="kpi-content">
              <div className="kpi-label">Total Volume</div>
              <div className="kpi-value">{(currentTraffic.summary.total_volume ?? 0).toLocaleString()}</div>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon amber">🏎️</div>
            <div className="kpi-content">
              <div className="kpi-label">Avg Speed</div>
              <div className="kpi-value">{currentTraffic.summary.avg_speed ?? 0} <span style={{ fontSize: 14, fontWeight: 400 }}>km/h</span></div>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon red">⚠️</div>
            <div className="kpi-content">
              <div className="kpi-label">High Congestion</div>
              <div className="kpi-value">{currentTraffic.summary.high_congestion_count ?? 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filters-bar">
        <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>Filters:</span>
        <select className="select-field" style={{ width: 160 }} value={filterZone} onChange={e => setFilterZone(e.target.value)}>
          <option value="">All Zones</option>
          {zones.map(z => <option key={z} value={z}>{z}</option>)}
        </select>
        <select className="select-field" style={{ width: 160 }} value={filterCongestion} onChange={e => setFilterCongestion(e.target.value)}>
          <option value="">All Levels</option>
          <option value="Low">Low</option>
          <option value="Moderate">Moderate</option>
          <option value="High">High</option>
          <option value="Critical">Critical</option>
        </select>
        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Showing {filteredIntersections.length} of {intersections.length}
        </span>
      </div>

      {/* Intersections Table */}
      <div className="glass-card-static" style={{ overflow: 'hidden' }}>
        {filteredIntersections.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🚦</div>
            <p>No intersections match the current filters</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Zone</th>
                  <th>Volume</th>
                  <th>Speed</th>
                  <th>Congestion</th>
                  <th>Green</th>
                  <th>Red</th>
                  <th>Mode</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredIntersections.map(i => (
                  <tr key={i.intersection_id}>
                    <td><strong style={{ color: 'var(--text-white)' }}>{i.intersection_id}</strong></td>
                    <td>{i.zone || '—'}</td>
                    <td>{(i.current_volume ?? 0).toLocaleString()}</td>
                    <td>{i.avg_speed ?? 0} km/h</td>
                    <td><span className={`badge ${CONGESTION_BADGE[i.congestion_level] || 'badge-info'}`}>{i.congestion_level || 'Unknown'}</span></td>
                    <td style={{ color: 'var(--status-success)' }}>{i.green_duration ?? '—'}s</td>
                    <td style={{ color: 'var(--status-danger)' }}>{i.red_duration ?? '—'}s</td>
                    <td><span className="badge badge-info" style={{ textTransform: 'capitalize' }}>{i.mode || 'auto'}</span></td>
                    <td><span className="badge badge-success" style={{ textTransform: 'capitalize' }}>{i.status || 'active'}</span></td>
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
