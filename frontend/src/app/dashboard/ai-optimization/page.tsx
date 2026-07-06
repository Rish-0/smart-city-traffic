'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';

const CONGESTION_COLORS: Record<string, string> = {
  Low: '#06d6a0', Moderate: '#f59e0b', High: '#f97316', Critical: '#ef4444'
};

export default function AIOptimizationPage() {
  const [form, setForm] = useState({
    intersection_id: 'J1', traffic_volume: 3000, weather: 'Clear',
    hour: 12, emergency_vehicles: 0, zone: 'Commercial', queue_length: 20,
  });
  const [result, setResult] = useState<any>(null);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getPredictions(12).catch(() => null),
      api.getAIHealth().catch(() => null),
    ]).then(([pred, h]) => {
      if (!pred && !h) {
        setError('Unable to connect to AI engine. Make sure the backend is running.');
      }
      setPredictions(pred?.predictions || []);
      setHealth(h);
      setLoading(false);
    });
  }, []);

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await api.optimizeSignal(form);
      setResult(res);
    } catch (err: any) {
      alert(err.message || 'Optimization failed');
    }
    setOptimizing(false);
  };

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
          <h1 className="page-title">AI Signal Optimization</h1>
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
        <h1 className="page-title">AI Signal Optimization</h1>
        <p className="page-description">AI-powered traffic signal timing recommendations and predictions</p>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Optimizer Form */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 className="chart-title">🤖 Signal Optimizer</h3>
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
            {optimizing ? '⏳ Optimizing...' : '🧠 Run Optimization'}
          </button>
        </div>

        {/* Result */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h3 className="chart-title">📋 Recommendation</h3>
          {result?.recommendation ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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
              <p>Run the optimizer to see AI recommendations</p>
            </div>
          )}
        </div>
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
