'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

const CHART_COLORS = ['#06d6a0', '#0ea5e9', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];

export default function AnalyticsPage() {
  const [tab, setTab] = useState('hourly');
  const [source, setSource] = useState('metro');
  const [hourly, setHourly] = useState<any[]>([]);
  const [weekday, setWeekday] = useState<any[]>([]);
  const [monthly, setMonthly] = useState<any[]>([]);
  const [weather, setWeather] = useState<any[]>([]);
  const [distribution, setDistribution] = useState<any>(null);
  const [peakHours, setPeakHours] = useState<any>(null);
  const [scatter, setScatter] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (s: string) => {
    setLoading(true);
    setError(null);
    try {
      const [h, w, m, wt, d, ph, sc] = await Promise.all([
        api.getHourlyAnalytics(s).catch(() => ({ data: [] })),
        api.getWeekdayAnalytics(s).catch(() => ({ data: [] })),
        api.getMonthlyAnalytics(s).catch(() => ({ data: [] })),
        api.getWeatherImpact(s).catch(() => ({ data: [] })),
        api.getDistribution(s).catch(() => ({ bins: [], stats: {} })),
        api.getPeakHours(s).catch(() => ({ data: [], peak_hours: [] })),
        api.getScatterData().catch(() => ({ data: [] })),
      ]);
      setHourly(h?.data || []); setWeekday(w?.data || []); setMonthly(m?.data || []);
      setWeather(wt?.data || []); setDistribution(d); setPeakHours(ph);
      setScatter(sc?.data || []);
      // Check if all data is empty
      if (!(h?.data?.length || w?.data?.length || m?.data?.length)) {
        setError('No analytics data available. The backend may not have data loaded yet.');
      }
    } catch {
      setError('Failed to load analytics data.');
    }
    setLoading(false);
  };

  useEffect(() => { loadData(source); }, [source]);

  const tabs = [
    { id: 'hourly', label: '⏰ Hourly' },
    { id: 'weekday', label: '📅 Weekly' },
    { id: 'monthly', label: '📆 Monthly' },
    { id: 'weather', label: '🌤️ Weather' },
    { id: 'distribution', label: '📊 Distribution' },
    { id: 'scatter', label: '🔬 Scatter' },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="page-title">Traffic Analytics</h1>
            <p className="page-description">Comprehensive traffic pattern analysis and visualizations</p>
          </div>
          <select className="select-field" style={{ width: 180 }} value={source} onChange={e => setSource(e.target.value)}>
            <option value="metro">Metro Dataset</option>
            <option value="simulation">Simulation</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="tab-bar">
        {tabs.map(t => (
          <button key={t.id} className={`tab-item ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading analytics...</p></div>
      ) : error && !hourly.length && !weekday.length ? (
        <div className="error-state">
          <div className="error-state-icon">📊</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={() => loadData(source)}>🔄 Retry</button>
        </div>
      ) : (
        <>
          {/* Hourly */}
          {tab === 'hourly' && (
            <div className="grid-2">
              <div className="glass-card chart-container">
                <h3 className="chart-title">Average Traffic Volume by Hour</h3>
                {hourly.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={hourly}>
                      <defs>
                        <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06d6a0" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#06d6a0" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="label" tick={{ fill: '#8892a8', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                      <Area type="monotone" dataKey="avg_volume" stroke="#06d6a0" strokeWidth={2} fill="url(#colorVolume)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">📈</div>
                    <p>No hourly data available</p>
                  </div>
                )}
              </div>
              {peakHours && peakHours.peak_hours && peakHours.peak_hours.length > 0 ? (
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 className="chart-title">🔥 Peak Hours</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
                    {peakHours.peak_hours.map((p: any, i: number) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: i === 0 ? 'rgba(239,68,68,0.15)' : i === 1 ? 'rgba(245,158,11,0.15)' : 'rgba(14,165,233,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 800, color: i === 0 ? '#ef4444' : i === 1 ? '#f59e0b' : '#0ea5e9' }}>
                          #{i + 1}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-white)' }}>{p.label || `Hour ${p.hour ?? i}`}</div>
                          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Avg: {p.avg_volume ?? '—'} | Max: {p.max_volume ?? '—'}</div>
                        </div>
                        {p.is_peak && <span className="badge badge-danger">Rush Hour</span>}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 className="chart-title">🔥 Peak Hours</h3>
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">⏰</div>
                    <p>No peak hour data available</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Weekday */}
          {tab === 'weekday' && (
            <div className="glass-card chart-container">
              <h3 className="chart-title">Average Traffic Volume by Day of Week</h3>
              {weekday.length > 0 ? (
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={weekday}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" tick={{ fill: '#8892a8', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                    <Bar dataKey="avg_volume" radius={[6, 6, 0, 0]}>
                      {weekday.map((_, idx) => (
                        <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state" style={{ padding: '40px 20px' }}>
                  <div className="empty-state-icon">📅</div>
                  <p>No weekly data available</p>
                </div>
              )}
            </div>
          )}

          {/* Monthly */}
          {tab === 'monthly' && (
            <div className="glass-card chart-container">
              <h3 className="chart-title">Average Traffic Volume by Month</h3>
              {monthly.length > 0 ? (
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={monthly}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" tick={{ fill: '#8892a8', fontSize: 11 }} angle={-30} textAnchor="end" height={60} />
                    <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                    <Bar dataKey="avg_volume" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state" style={{ padding: '40px 20px' }}>
                  <div className="empty-state-icon">📆</div>
                  <p>No monthly data available</p>
                </div>
              )}
            </div>
          )}

          {/* Weather */}
          {tab === 'weather' && (
            <div className="grid-2">
              <div className="glass-card chart-container">
                <h3 className="chart-title">Traffic Volume by Weather Condition</h3>
                {weather.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={weather} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis type="number" tick={{ fill: '#8892a8', fontSize: 11 }} />
                      <YAxis dataKey="weather" type="category" tick={{ fill: '#8892a8', fontSize: 12 }} width={100} />
                      <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                      <Bar dataKey="avg_volume" radius={[0, 6, 6, 0]}>
                        {weather.map((_, idx) => (
                          <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">🌤️</div>
                    <p>No weather data available</p>
                  </div>
                )}
              </div>
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 className="chart-title">Weather Impact Summary</h3>
                {weather.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                    {weather.map((w, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ fontSize: 24 }}>
                          {w.weather === 'Clear' ? '☀️' : w.weather === 'Rain' ? '🌧️' : w.weather === 'Snow' ? '❄️' : w.weather === 'Clouds' ? '☁️' : w.weather === 'Fog' ? '🌫️' : w.weather === 'Mist' ? '🌁' : '🌤️'}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: 'var(--text-white)' }}>{w.weather || 'Unknown'}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{w.occurrences ?? 0} data points</div>
                        </div>
                        <div style={{ fontWeight: 700, fontSize: 16, color: CHART_COLORS[i % CHART_COLORS.length] }}>
                          {(w.avg_volume ?? 0).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">🌤️</div>
                    <p>No weather impact data</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Distribution */}
          {tab === 'distribution' && (
            <div className="grid-2">
              <div className="glass-card chart-container">
                <h3 className="chart-title">Traffic Volume Distribution</h3>
                {distribution?.bins && distribution.bins.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={distribution.bins}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="bin" tick={{ fill: '#8892a8', fontSize: 9 }} angle={-45} textAnchor="end" height={80} />
                      <YAxis tick={{ fill: '#8892a8', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }} />
                      <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">📊</div>
                    <p>No distribution data available</p>
                  </div>
                )}
              </div>
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 className="chart-title">📊 Statistics</h3>
                {distribution?.stats ? (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
                    {[
                      { label: 'Mean', value: distribution.stats.mean?.toLocaleString() ?? '—', color: '#06d6a0' },
                      { label: 'Median', value: distribution.stats.median?.toLocaleString() ?? '—', color: '#0ea5e9' },
                      { label: 'Std Dev', value: distribution.stats.std_dev?.toLocaleString() ?? '—', color: '#8b5cf6' },
                      { label: 'Min', value: distribution.stats.min?.toLocaleString() ?? '—', color: '#f59e0b' },
                      { label: 'Max', value: distribution.stats.max?.toLocaleString() ?? '—', color: '#ef4444' },
                      { label: 'Total', value: distribution.stats.total?.toLocaleString() ?? '—', color: '#14b8a6' },
                    ].map((s, i) => (
                      <div key={i} style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                        <div style={{ fontSize: 24, fontWeight: 800, color: s.color }}>{s.value}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{s.label}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state" style={{ padding: '40px 20px' }}>
                    <div className="empty-state-icon">📊</div>
                    <p>No statistics available</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Scatter */}
          {tab === 'scatter' && (
            <div className="glass-card chart-container">
              <h3 className="chart-title">Volume vs Speed (Simulation Data)</h3>
              {scatter.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="x" name="Volume" tick={{ fill: '#8892a8', fontSize: 11 }} label={{ value: 'Traffic Volume', position: 'insideBottom', offset: -5, fill: '#8892a8' }} />
                    <YAxis dataKey="y" name="Speed" tick={{ fill: '#8892a8', fontSize: 11 }} label={{ value: 'Avg Speed (km/h)', angle: -90, position: 'insideLeft', fill: '#8892a8' }} />
                    <Tooltip
                      contentStyle={{ background: '#0f1629', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8ecf4' }}
                      formatter={(val: any, name: string) => [val, name === 'x' ? 'Volume' : 'Speed']}
                    />
                    <Scatter data={scatter} fill="#06d6a0" fillOpacity={0.6} />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state" style={{ padding: '40px 20px' }}>
                  <div className="empty-state-icon">🔬</div>
                  <p>No scatter data available</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
