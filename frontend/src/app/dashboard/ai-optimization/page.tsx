'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';

const CONGESTION_COLORS: Record<string, string> = {
  Low: '#06d6a0', Moderate: '#f59e0b', High: '#f97316', Critical: '#ef4444'
};

const STATUS_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  applied: { bg: 'rgba(6,214,160,0.15)', color: '#06d6a0', label: '✅ Applied' },
  skipped: { bg: 'rgba(136,146,168,0.15)', color: '#8892a8', label: '⏭️ Skipped' },
  reverted: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: '↩️ Reverted' },
};

const TRIGGER_LABELS: Record<string, string> = {
  manual: '👤 Manual',
  auto: '🤖 Auto',
  bulk: '📦 Bulk',
};

export default function AIOptimizationPage() {
  const [form, setForm] = useState({
    intersection_id: 'J1', traffic_volume: 3000, weather: 'Clear',
    hour: 12, emergency_vehicles: 0, zone: 'Commercial', queue_length: 20,
  });
  const [result, setResult] = useState<any>(null);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [autoStatus, setAutoStatus] = useState<any>(null);
  const [actionLogs, setActionLogs] = useState<any[]>([]);
  const [logTotal, setLogTotal] = useState(0);
  const [optimizing, setOptimizing] = useState(false);
  const [bulkOptimizing, setBulkOptimizing] = useState(false);
  const [bulkResult, setBulkResult] = useState<any>(null);
  const [reverting, setReverting] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logFilter, setLogFilter] = useState({ status: '', triggered_by: '' });

  const loadData = useCallback(() => {
    Promise.all([
      api.getPredictions(12).catch(() => null),
      api.getAIHealth().catch(() => null),
      api.getAutoOptimizeStatus().catch(() => null),
      api.getAIActionLog('limit=20').catch(() => null),
    ]).then(([pred, h, status, logs]) => {
      if (!pred && !h) {
        setError('Unable to connect to AI engine. Make sure the backend is running.');
      }
      setPredictions(pred?.predictions || []);
      setHealth(h);
      setAutoStatus(status);
      setActionLogs(logs?.logs || []);
      setLogTotal(logs?.total || 0);
      setLoading(false);
    });
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await api.optimizeSignal(form);
      setResult(res);
      // Refresh action logs and status after applying
      const [logs, status] = await Promise.all([
        api.getAIActionLog('limit=20').catch(() => null),
        api.getAutoOptimizeStatus().catch(() => null),
      ]);
      setActionLogs(logs?.logs || []);
      setLogTotal(logs?.total || 0);
      setAutoStatus(status);
    } catch (err: any) {
      alert(err.message || 'Optimization failed');
    }
    setOptimizing(false);
  };

  const handleBulkOptimize = async () => {
    if (!confirm('Run AI optimization on ALL intersections? This will auto-apply signal changes.')) return;
    setBulkOptimizing(true);
    setBulkResult(null);
    try {
      const res = await api.autoOptimizeAll();
      setBulkResult(res);
      // Refresh
      const [logs, status] = await Promise.all([
        api.getAIActionLog('limit=20').catch(() => null),
        api.getAutoOptimizeStatus().catch(() => null),
      ]);
      setActionLogs(logs?.logs || []);
      setLogTotal(logs?.total || 0);
      setAutoStatus(status);
    } catch (err: any) {
      alert(err.message || 'Bulk optimization failed');
    }
    setBulkOptimizing(false);
  };

  const handleRevert = async (logId: number) => {
    if (!confirm('Revert this AI action? Signal timings will be restored to previous values.')) return;
    setReverting(logId);
    try {
      await api.revertAIAction(logId);
      // Refresh logs
      const [logs, status] = await Promise.all([
        api.getAIActionLog('limit=20').catch(() => null),
        api.getAutoOptimizeStatus().catch(() => null),
      ]);
      setActionLogs(logs?.logs || []);
      setLogTotal(logs?.total || 0);
      setAutoStatus(status);
    } catch (err: any) {
      alert(err.message || 'Revert failed');
    }
    setReverting(null);
  };

  const refreshLogs = async () => {
    const params = new URLSearchParams();
    params.set('limit', '20');
    if (logFilter.status) params.set('status', logFilter.status);
    if (logFilter.triggered_by) params.set('triggered_by', logFilter.triggered_by);
    const logs = await api.getAIActionLog(params.toString()).catch(() => null);
    setActionLogs(logs?.logs || []);
    setLogTotal(logs?.total || 0);
  };

  useEffect(() => { if (!loading) refreshLogs(); }, [logFilter]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading AI engine...</p></div>
      </div>
    );
  }

  if (error && !health && predictions.length === 0) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">AI Autonomous Control</h1>
        </div>
        <div className="error-state">
          <div className="error-state-icon">🤖</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>🔄 Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">AI Autonomous Control</h1>
        <p className="page-description">AI automatically optimizes and applies signal timing changes in real-time</p>
      </div>

      {/* Auto-Optimization Status Banner */}
      {autoStatus && (
        <div className="glass-card animate-in" style={{ padding: 20, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 12, height: 12, borderRadius: '50%',
                background: autoStatus.auto_optimization_enabled ? '#06d6a0' : '#ef4444',
                boxShadow: autoStatus.auto_optimization_enabled ? '0 0 12px rgba(6,214,160,0.6)' : '0 0 12px rgba(239,68,68,0.6)',
                animation: autoStatus.auto_optimization_enabled ? 'pulse 2s ease-in-out infinite' : 'none',
              }} />
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-white)' }}>
                  Auto-Optimization {autoStatus.auto_optimization_enabled ? 'Active' : 'Disabled'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Background scan every {autoStatus.interval_minutes} min • Applies changes for High/Critical congestion
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-primary)' }}>{autoStatus.today_applied}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Applied Today</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-secondary)' }}>{autoStatus.today_auto}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Auto Actions</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: '#06d6a0' }}>{autoStatus.avg_improvement_today}%</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Avg Improvement</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>{autoStatus.total_actions_all_time}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>All-Time Actions</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Optimize Button + Result */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          className="btn btn-primary btn-lg"
          onClick={handleBulkOptimize}
          disabled={bulkOptimizing}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          {bulkOptimizing ? (
            <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Optimizing All...</>
          ) : (
            <>⚡ Optimize All Intersections</>
          )}
        </button>
        {bulkResult && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span className="badge badge-success">✅ {bulkResult.applied} Applied</span>
            <span className="badge badge-info">⏭️ {bulkResult.skipped} Skipped</span>
            {bulkResult.errors > 0 && <span className="badge badge-danger">❌ {bulkResult.errors} Errors</span>}
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              out of {bulkResult.total_intersections} intersections
            </span>
          </div>
        )}
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Optimizer Form */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 className="chart-title">🤖 Signal Optimizer & Auto-Apply</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group">
              <label className="input-label">Intersection</label>
              <select className="select-field" value={form.intersection_id} onChange={e => setForm({ ...form, intersection_id: e.target.value })}>
                {Array.from({ length: 25 }, (_, i) => <option key={i} value={`J${i + 1}`}>J{i + 1}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="input-label">Traffic Volume</label>
              <input className="input-field" type="number" value={form.traffic_volume} onChange={e => setForm({ ...form, traffic_volume: parseInt(e.target.value) || 0 })} />
            </div>
            <div className="form-group">
              <label className="input-label">Weather</label>
              <select className="select-field" value={form.weather} onChange={e => setForm({ ...form, weather: e.target.value })}>
                {['Clear', 'Clouds', 'Rain', 'Drizzle', 'Snow', 'Fog', 'Thunderstorm'].map(w => <option key={w} value={w}>{w}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="input-label">Hour (0-23)</label>
              <input className="input-field" type="number" min={0} max={23} value={form.hour} onChange={e => setForm({ ...form, hour: parseInt(e.target.value) || 0 })} />
            </div>
            <div className="form-group">
              <label className="input-label">Zone</label>
              <select className="select-field" value={form.zone} onChange={e => setForm({ ...form, zone: e.target.value })}>
                {['Commercial', 'Residential', 'School', 'Industrial', 'Hospital'].map(z => <option key={z} value={z}>{z}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="input-label">Emergency Vehicles</label>
              <input className="input-field" type="number" min={0} value={form.emergency_vehicles} onChange={e => setForm({ ...form, emergency_vehicles: parseInt(e.target.value) || 0 })} />
            </div>
            <div className="form-group">
              <label className="input-label">Queue Length</label>
              <input className="input-field" type="number" min={0} value={form.queue_length} onChange={e => setForm({ ...form, queue_length: parseInt(e.target.value) || 0 })} />
            </div>
          </div>
          <button
            className="btn btn-primary btn-lg"
            onClick={handleOptimize}
            disabled={optimizing}
            style={{ width: '100%', marginTop: 8 }}
          >
            {optimizing ? '⏳ Optimizing & Applying...' : '🧠 Optimize & Apply'}
          </button>
        </div>

        {/* Result */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 className="chart-title">📋 Applied Result</h3>
          {result?.recommendation ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Applied status banner */}
              {result.applied && (
                <div style={{
                  padding: 12, borderRadius: 'var(--radius-md)',
                  background: result.applied.status === 'applied'
                    ? 'rgba(6,214,160,0.12)' : 'rgba(136,146,168,0.12)',
                  border: `1px solid ${result.applied.status === 'applied' ? 'rgba(6,214,160,0.3)' : 'rgba(136,146,168,0.3)'}`,
                  display: 'flex', alignItems: 'center', gap: 10,
                }}>
                  <span style={{ fontSize: 20 }}>{result.applied.status === 'applied' ? '✅' : '⏭️'}</span>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: result.applied.status === 'applied' ? '#06d6a0' : '#8892a8' }}>
                      {result.applied.status === 'applied' ? 'Signal Updated Successfully' : 'No Change Needed'}
                    </div>
                    {result.applied.status === 'applied' && (
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                        Green: {result.applied.previous_green}s → {result.applied.new_green}s • Red: {result.applied.previous_red}s → {result.applied.new_red}s
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>CONGESTION</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: CONGESTION_COLORS[result.recommendation.congestion_level] || '#fff' }}>
                    {result.recommendation.congestion_level || '—'}
                  </div>
                </div>
                <div style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>CONFIDENCE</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-secondary)' }}>
                    {result.recommendation.confidence_score != null ? `${(result.recommendation.confidence_score * 100).toFixed(0)}%` : '—'}
                  </div>
                </div>
                <div style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>GREEN SIGNAL</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--status-success)' }}>
                    {result.recommendation.suggested_green ?? '—'}s
                  </div>
                </div>
                <div style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>RED SIGNAL</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--status-danger)' }}>
                    {result.recommendation.suggested_red ?? '—'}s
                  </div>
                </div>
              </div>
              <div style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>EXPECTED IMPROVEMENT</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent-primary)' }}>
                  ↗ {result.recommendation.expected_improvement ?? '—'}%
                </div>
              </div>
              {result.recommendation.reasoning && (
                <div style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>AI REASONING</div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                    {result.recommendation.reasoning}
                  </div>
                </div>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                <span className={`badge ${result.recommendation.priority === 'critical' ? 'badge-critical' : result.recommendation.priority === 'high' ? 'badge-danger' : result.recommendation.priority === 'medium' ? 'badge-warning' : 'badge-success'}`}>
                  Priority: {result.recommendation.priority || 'normal'}
                </span>
                <span className="badge badge-info">
                  Action: {(result.recommendation.action || 'optimize')?.replace('_', ' ')}
                </span>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">🤖</div>
              <p>Run the optimizer to auto-apply AI changes</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Action Log */}
      <div className="glass-card-static animate-in" style={{ marginBottom: 24, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h3 className="chart-title" style={{ marginBottom: 4 }}>📜 AI Action Log</h3>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{logTotal} total actions recorded</div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <select
              className="select-field"
              style={{ width: 130, fontSize: 12 }}
              value={logFilter.status}
              onChange={e => setLogFilter({ ...logFilter, status: e.target.value })}
            >
              <option value="">All Status</option>
              <option value="applied">Applied</option>
              <option value="skipped">Skipped</option>
              <option value="reverted">Reverted</option>
            </select>
            <select
              className="select-field"
              style={{ width: 130, fontSize: 12 }}
              value={logFilter.triggered_by}
              onChange={e => setLogFilter({ ...logFilter, triggered_by: e.target.value })}
            >
              <option value="">All Triggers</option>
              <option value="manual">Manual</option>
              <option value="auto">Auto</option>
              <option value="bulk">Bulk</option>
            </select>
            <button className="btn btn-secondary" style={{ fontSize: 12, padding: '6px 12px' }} onClick={refreshLogs}>
              🔄
            </button>
          </div>
        </div>
        {actionLogs.length === 0 ? (
          <div className="empty-state" style={{ padding: '40px 20px' }}>
            <div className="empty-state-icon">📜</div>
            <p>No AI actions recorded yet</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Intersection</th>
                  <th>Trigger</th>
                  <th>Congestion</th>
                  <th>Previous</th>
                  <th>New Timing</th>
                  <th>Improvement</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {actionLogs.map((log: any) => {
                  const st = STATUS_STYLES[log.status] || STATUS_STYLES.applied;
                  return (
                    <tr key={log.id}>
                      <td style={{ whiteSpace: 'nowrap', fontSize: 12 }}>
                        {log.applied_at ? new Date(log.applied_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </td>
                      <td><strong style={{ color: 'var(--text-white)' }}>{log.intersection_id}</strong></td>
                      <td>
                        <span style={{ fontSize: 12 }}>{TRIGGER_LABELS[log.triggered_by] || log.triggered_by}</span>
                      </td>
                      <td>
                        <span className={`badge ${log.congestion_level === 'Critical' ? 'badge-critical' : log.congestion_level === 'High' ? 'badge-danger' : log.congestion_level === 'Moderate' ? 'badge-warning' : 'badge-success'}`}>
                          {log.congestion_level}
                        </span>
                      </td>
                      <td style={{ fontSize: 12 }}>
                        <span style={{ color: 'var(--status-success)' }}>{log.previous_green}s</span>
                        {' / '}
                        <span style={{ color: 'var(--status-danger)' }}>{log.previous_red}s</span>
                      </td>
                      <td style={{ fontSize: 12 }}>
                        {log.status !== 'skipped' ? (
                          <>
                            <span style={{ color: 'var(--status-success)', fontWeight: 700 }}>{log.new_green}s</span>
                            {' / '}
                            <span style={{ color: 'var(--status-danger)', fontWeight: 700 }}>{log.new_red}s</span>
                          </>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>
                      <td>
                        {log.expected_improvement > 0 ? (
                          <span style={{ color: '#06d6a0', fontWeight: 600 }}>↗ {log.expected_improvement}%</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>
                      <td>
                        <span style={{ color: log.confidence_score >= 0.8 ? '#06d6a0' : log.confidence_score >= 0.7 ? '#f59e0b' : '#ef4444', fontWeight: 600 }}>
                          {(log.confidence_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td>
                        <span style={{
                          fontSize: 11, padding: '3px 8px', borderRadius: 6,
                          background: st.bg, color: st.color, fontWeight: 600,
                        }}>
                          {st.label}
                        </span>
                      </td>
                      <td>
                        {log.status === 'applied' && (
                          <button
                            className="btn btn-secondary"
                            style={{ fontSize: 11, padding: '4px 10px' }}
                            onClick={() => handleRevert(log.id)}
                            disabled={reverting === log.id}
                          >
                            {reverting === log.id ? '...' : '↩️ Revert'}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Predictions Chart */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="glass-card chart-container">
          <h3 className="chart-title">📈 Traffic Volume Predictions (Next 12h)</h3>
          {predictions.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={predictions}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="label" tick={{ fill: '#8892a8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                <Line type="monotone" dataKey="predicted_volume" stroke="#06d6a0" strokeWidth={2} dot={{ fill: '#06d6a0', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-state-icon">📈</div>
              <p>No prediction data available</p>
            </div>
          )}
        </div>

        <div className="glass-card chart-container">
          <h3 className="chart-title">🎯 Predicted Congestion Levels</h3>
          {predictions.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={predictions}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="label" tick={{ fill: '#8892a8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                <Bar dataKey="predicted_volume" radius={[4, 4, 0, 0]}>
                  {predictions.map((entry, idx) => (
                    <Cell key={idx} fill={CONGESTION_COLORS[entry.congestion_level] || '#8892a8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div className="empty-state-icon">🎯</div>
              <p>No congestion predictions available</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Health */}
      {health && (
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 className="chart-title">💚 AI Engine Health</h3>
          <div className="grid-4">
            <div style={{ textAlign: 'center', padding: 16 }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: (health.health_score ?? 0) >= 80 ? 'var(--status-success)' : (health.health_score ?? 0) >= 60 ? 'var(--status-warning)' : 'var(--status-danger)' }}>
                {health.health_score ?? '—'}%
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>Health Score</div>
            </div>
            <div style={{ textAlign: 'center', padding: 16 }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--accent-secondary)' }}>
                {health.total_data_points?.toLocaleString() ?? '—'}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>Data Points</div>
            </div>
            <div style={{ textAlign: 'center', padding: 16 }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--accent-tertiary)' }}>
                {health.metrics?.model_accuracy ?? '—'}%
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>Model Accuracy</div>
            </div>
            <div style={{ textAlign: 'center', padding: 16 }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--status-success)' }}>
                {health.metrics?.system_uptime ?? '—'}%
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>System Uptime</div>
            </div>
          </div>
          {health.capabilities && health.capabilities.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>CAPABILITIES</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {health.capabilities.map((cap: string, i: number) => (
                  <span key={i} className="badge badge-info">{cap}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
