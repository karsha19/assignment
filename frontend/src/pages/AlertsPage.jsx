import { useEffect, useState, useCallback } from 'react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext.jsx'
import { useDashboardSocket } from '../hooks/useDashboardSocket.js'
import { useToast } from '../components/Toast.jsx'
import Badge from '../components/Badge.jsx'

export default function AlertsPage() {
  const { token } = useAuth()
  const pushToast = useToast()
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ status: '', severity: '' })
  const [selected, setSelected] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
      const resp = await api.get('/api/v1/alerts', { params: { ...params, limit: 200 } })
      setAlerts(resp.data)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  useDashboardSocket(token, (msg) => {
    if (['new_alert', 'alert_acknowledged', 'alert_resolved'].includes(msg.type)) {
      if (msg.type === 'new_alert') pushToast('New alert', `Match: ${msg.data.matched_identifier}`, 'alert')
      load()
    }
  })

  async function acknowledge(id) {
    await api.post(`/api/v1/alerts/${id}/acknowledge`)
    pushToast('Alert acknowledged', id)
    load()
  }
  async function resolve(id) {
    await api.post(`/api/v1/alerts/${id}/resolve`)
    pushToast('Alert resolved', id)
    load()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Alerts Center</h1>
          <div className="page-subtitle">Watchlist-match alerts, updated in real time.</div>
        </div>
      </div>

      <div className="toolbar">
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
        <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="grid-2">
        <div className="card">
          {loading ? (
            <div className="loading-state">Loading alerts…</div>
          ) : alerts.length === 0 ? (
            <div className="empty-state">No alerts match the current filters.</div>
          ) : (
            <table>
              <thead>
                <tr><th>Entity</th><th>Severity</th><th>Status</th><th>Detected</th><th></th></tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.id} onClick={() => setSelected(a)} style={{ cursor: 'pointer' }}>
                    <td>{a.matched_identifier}</td>
                    <td><Badge value={a.severity} /></td>
                    <td><Badge value={a.status} /></td>
                    <td>{new Date(a.detection_timestamp).toLocaleString()}</td>
                    <td style={{ display: 'flex', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                      {a.status === 'new' && <button className="btn-secondary" onClick={() => acknowledge(a.id)}>Ack</button>}
                      {a.status !== 'resolved' && <button className="btn-secondary" onClick={() => resolve(a.id)}>Resolve</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <div className="section-title">Alert Details</div>
          {!selected ? (
            <div className="empty-state">Select an alert from the list to view its details.</div>
          ) : (
            <table>
              <tbody>
                <tr><td>Alert ID</td><td>{selected.id}</td></tr>
                <tr><td>Matched Identifier</td><td>{selected.matched_identifier}</td></tr>
                <tr><td>Camera</td><td>{selected.camera_id}</td></tr>
                <tr><td>Severity</td><td><Badge value={selected.severity} /></td></tr>
                <tr><td>Status</td><td><Badge value={selected.status} /></td></tr>
                <tr><td>Confidence</td><td>{(selected.confidence * 100).toFixed(0)}%</td></tr>
                <tr><td>Detected at</td><td>{new Date(selected.detection_timestamp).toLocaleString()}</td></tr>
                <tr><td>Created at</td><td>{new Date(selected.created_at).toLocaleString()}</td></tr>
                {selected.acknowledged_at && <tr><td>Acknowledged at</td><td>{new Date(selected.acknowledged_at).toLocaleString()}</td></tr>}
                {selected.resolved_at && <tr><td>Resolved at</td><td>{new Date(selected.resolved_at).toLocaleString()}</td></tr>}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
