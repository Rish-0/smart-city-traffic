'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

const SEV_BADGE: Record<string, string> = { low: 'badge-success', medium: 'badge-warning', high: 'badge-danger', critical: 'badge-critical' };
const STATUS_BADGE: Record<string, string> = { reported: 'badge-info', investigating: 'badge-warning', resolved: 'badge-success' };

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    type: 'accident', title: '', description: '', location: '',
    intersection_id: '', severity: 'medium', priority: 3,
  });

  const loadIncidents = () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (filterStatus) params.set('status', filterStatus);
    if (filterSeverity) params.set('severity', filterSeverity);
    api.getIncidents(params.toString()).then(data => {
      setIncidents(data?.incidents || []);
      setTotal(data?.total || 0);
      setLoading(false);
    }).catch((err) => {
      setError(err.message || 'Failed to load incidents');
      setLoading(false);
    });
  };

  useEffect(() => { loadIncidents(); }, [filterStatus, filterSeverity]);

  const handleCreate = async () => {
    try {
      await api.createIncident(createForm);
      setShowCreateModal(false);
      setCreateForm({ type: 'accident', title: '', description: '', location: '', intersection_id: '', severity: 'medium', priority: 3 });
      loadIncidents();
    } catch (err: any) {
      alert(err.message || 'Failed to create incident');
    }
  };

  const handleUpdateStatus = async (id: number, status: string) => {
    try {
      await api.updateIncident(id, { status });
      loadIncidents();
    } catch (err: any) {
      alert(err.message || 'Failed to update incident');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this incident?')) return;
    try {
      await api.deleteIncident(id);
      loadIncidents();
    } catch (err: any) {
      alert(err.message || 'Failed to delete incident');
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="page-title">Incident Management</h1>
            <p className="page-description">{total} total incidents tracked</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            ➕ Report Incident
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <select className="select-field" style={{ width: 150 }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="reported">Reported</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
        </select>
        <select className="select-field" style={{ width: 150 }} value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}>
          <option value="">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        {(filterStatus || filterSeverity) && (
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => { setFilterStatus(''); setFilterSeverity(''); }}
          >
            ✕ Clear Filters
          </button>
        )}
      </div>

      {/* Incidents List */}
      {loading ? (
        <div className="loading-container"><div className="spinner" /><p className="loading-text">Loading incidents...</p></div>
      ) : error ? (
        <div className="error-state">
          <div className="error-state-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={loadIncidents}>🔄 Retry</button>
        </div>
      ) : incidents.length === 0 ? (
        <div className="glass-card-static empty-state">
          <div className="empty-state-icon">🎉</div>
          <p>{filterStatus || filterSeverity ? 'No incidents match the current filters' : 'No incidents found'}</p>
        </div>
      ) : (
        <div className="glass-card-static" style={{ overflow: 'hidden' }}>
          {incidents.map(inc => (
            <div key={inc.id} className="incident-row">
              <div className={`severity-dot ${inc.severity || 'low'}`} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                  <strong style={{ color: 'var(--text-white)', fontSize: 15 }}>{inc.title || 'Untitled'}</strong>
                  <span className={`badge ${SEV_BADGE[inc.severity] || 'badge-info'}`}>{inc.severity || 'unknown'}</span>
                  <span className={`badge ${STATUS_BADGE[inc.status] || 'badge-info'}`}>{inc.status || 'unknown'}</span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 2 }}>
                  📍 {inc.location || 'Unknown location'} {inc.intersection_id ? `(${inc.intersection_id})` : ''}
                </div>
                {inc.description && (
                  <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{inc.description}</div>
                )}
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  {(inc.type || 'unknown').replace('_', ' ')} • Priority {inc.priority ?? '—'} • Reported {inc.created_at ? new Date(inc.created_at).toLocaleString() : '—'}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                {inc.status !== 'resolved' && (
                  <>
                    {inc.status === 'reported' && (
                      <button className="btn btn-sm btn-secondary" onClick={() => handleUpdateStatus(inc.id, 'investigating')}>
                        🔍 Investigate
                      </button>
                    )}
                    <button className="btn btn-sm btn-primary" onClick={() => handleUpdateStatus(inc.id, 'resolved')}>
                      ✅ Resolve
                    </button>
                  </>
                )}
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(inc.id)}>🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content glass-card-static" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Report Incident</h2>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <div className="form-group">
              <label className="input-label">Type</label>
              <select className="select-field" value={createForm.type} onChange={e => setCreateForm({ ...createForm, type: e.target.value })}>
                <option value="accident">Accident</option>
                <option value="construction">Construction</option>
                <option value="weather_hazard">Weather Hazard</option>
                <option value="signal_failure">Signal Failure</option>
                <option value="road_closure">Road Closure</option>
              </select>
            </div>
            <div className="form-group">
              <label className="input-label">Title</label>
              <input className="input-field" placeholder="Brief incident title" value={createForm.title} onChange={e => setCreateForm({ ...createForm, title: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="input-label">Location</label>
              <input className="input-field" placeholder="e.g. I-94 near J3" value={createForm.location} onChange={e => setCreateForm({ ...createForm, location: e.target.value })} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="input-label">Intersection</label>
                <select className="select-field" value={createForm.intersection_id} onChange={e => setCreateForm({ ...createForm, intersection_id: e.target.value })}>
                  <option value="">None</option>
                  {Array.from({ length: 25 }, (_, i) => <option key={i} value={`J${i + 1}`}>J{i + 1}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="input-label">Severity</label>
                <select className="select-field" value={createForm.severity} onChange={e => setCreateForm({ ...createForm, severity: e.target.value })}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="input-label">Description</label>
              <textarea className="input-field" rows={3} placeholder="Additional details..." value={createForm.description} onChange={e => setCreateForm({ ...createForm, description: e.target.value })} style={{ resize: 'vertical' }} />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleCreate} disabled={!createForm.title || !createForm.location}>
                ➕ Create Incident
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
