import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api, resolveMediaUrl } from '../services/api'
import { useAuth } from '../context/AuthContext.jsx'
import { useDashboardSocket } from '../hooks/useDashboardSocket.js'
import { useToast } from '../components/Toast.jsx'
import Badge from '../components/Badge.jsx'

export default function DashboardPage() {
  const { token } = useAuth()
  const pushToast = useToast()
  const [cameras, setCameras] = useState([])
  const [alerts, setAlerts] = useState([])
  const [events, setEvents] = useState([])
  const [activity, setActivity] = useState([])
  const [loading, setLoading] = useState(true)

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [camerasRes, alertsRes, eventsRes] = await Promise.all([
        api.get('/api/v1/cameras'),
        api.get('/api/v1/alerts', { params: { limit: 50 } }),
        api.get('/api/v1/analytics/events', { params: { limit: 30 } }),
      ])
      setCameras(camerasRes.data)
      setAlerts(alertsRes.data)
      setEvents(eventsRes.data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadAll() }, [loadAll])

  const pushActivity = useCallback((line) => {
    setActivity((prev) => [{ id: `${Date.now()}-${Math.random()}`, ts: new Date(), line }, ...prev].slice(0, 30))
  }, [])

  useDashboardSocket(token, (msg) => {
    if (msg.type === 'new_alert') {
      pushToast('New alert', `Match: ${msg.data.matched_identifier} — severity ${msg.data.severity}`, 'alert')
      pushActivity(`New ${msg.data.severity} alert for ${msg.data.matched_identifier}`)
      loadAll()
    } else if (msg.type === 'analytics_event') {
      pushActivity(`Detection: ${msg.data.entity_identifier || msg.data.event_type} on camera ${msg.data.camera_id}`)
      loadAll()
    } else if (msg.type === 'camera_health_changed') {
      pushActivity(`Camera health changed → ${msg.data.status}`)
      loadAll()
    } else if (msg.type === 'alert_acknowledged') {
      pushActivity(`Alert acknowledged by ${msg.data.acknowledged_by}`)
      loadAll()
    } else if (msg.type === 'alert_resolved') {
      pushActivity(`Alert resolved by ${msg.data.resolved_by}`)
      loadAll()
    } else if (msg.type === 'camera_created' || msg.type === 'camera_updated') {
      loadAll()
    }
  })

  const online = cameras.filter((c) => c.status === 'online').length
  const offline = cameras.filter((c) => c.status === 'offline').length
  const degraded = cameras.filter((c) => c.status === 'degraded').length
  const activeAlerts = alerts.filter((a) => a.status !== 'resolved').length
  const unresolvedAlerts = alerts.filter((a) => a.status === 'new').length
  const watchlistMatches = alerts.length

  async function acknowledgeAlert(id) {
    await api.post(`/api/v1/alerts/${id}/acknowledge`)
    loadAll()
  }
  async function resolveAlert(id) {
    await api.post(`/api/v1/alerts/${id}/resolve`)
    loadAll()
  }

  if (loading) return <div className="loading-state">Loading dashboard…</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Operational Dashboard</h1>
          <div className="page-subtitle">Live system health, detections and alerts. Updates in real time via WebSocket.</div>
        </div>
      </div>

      <div className="stat-grid">
        <Stat label="Total Cameras" value={cameras.length} />
        <Stat label="Online" value={online} />
        <Stat label="Offline" value={offline} />
        <Stat label="Degraded" value={degraded} />
        <Stat label="Active Alerts" value={activeAlerts} />
        <Stat label="Unresolved (New)" value={unresolvedAlerts} />
        <Stat label="Total Detections" value={events.length} />
        <Stat label="Watchlist Matches" value={watchlistMatches} />
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="section-title">Camera Grid</div>
          {cameras.length === 0 ? (
            <div className="empty-state">No cameras onboarded yet. <Link to="/cameras">Add one</Link>.</div>
          ) : (
            <div className="camera-grid">
              {cameras.map((cam) => (
                <Link to={`/cameras/${cam.id}`} key={cam.id} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="camera-card">
                    <div className="camera-card-video">
                      {cam.playback_url ? (
                        <video src={resolveMediaUrl(cam.playback_url)} muted loop autoPlay playsInline />
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>No preview available</span>
                      )}
                    </div>
                    <div className="camera-card-body">
                      <div className="camera-card-title">
                        {cam.name}
                        <Badge value={cam.status} />
                      </div>
                      <div className="camera-card-meta">{cam.camera_code} · {cam.zone || '—'}</div>
                      <div className="camera-card-meta">
                        <span className="source-label">{cam.source_protocol}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="section-title">Active Alerts</div>
          {alerts.filter(a => a.status !== 'resolved').length === 0 ? (
            <div className="empty-state">No active alerts.</div>
          ) : (
            <table>
              <thead>
                <tr><th>Entity</th><th>Severity</th><th>Status</th><th>Time</th><th></th></tr>
              </thead>
              <tbody>
                {alerts.filter(a => a.status !== 'resolved').slice(0, 10).map((a) => (
                  <tr key={a.id}>
                    <td>{a.matched_identifier}</td>
                    <td><Badge value={a.severity} /></td>
                    <td><Badge value={a.status} /></td>
                    <td>{new Date(a.detection_timestamp).toLocaleTimeString()}</td>
                    <td style={{ display: 'flex', gap: 6 }}>
                      {a.status === 'new' && (
                        <button className="btn-secondary" onClick={() => acknowledgeAlert(a.id)}>Ack</button>
                      )}
                      {a.status !== 'resolved' && (
                        <button className="btn-secondary" onClick={() => resolveAlert(a.id)}>Resolve</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="section-title" style={{ marginTop: 24 }}>Recent Activity</div>
          {activity.length === 0 ? (
            <div className="empty-state">No real-time activity yet in this session. Submit an analytics event to see it appear here instantly.</div>
          ) : (
            <div className="timeline">
              {activity.map((a) => (
                <div className="timeline-item" key={a.id}>
                  <div className="timeline-time">{a.ts.toLocaleTimeString()}</div>
                  <div className="timeline-title">{a.line}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
