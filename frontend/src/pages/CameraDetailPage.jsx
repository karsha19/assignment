import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, resolveMediaUrl } from '../services/api'
import Badge from '../components/Badge.jsx'

export default function CameraDetailPage() {
  const { cameraId } = useParams()
  const [camera, setCamera] = useState(null)
  const [health, setHealth] = useState(null)
  const [events, setEvents] = useState([])
  const [videoError, setVideoError] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const [camRes, healthRes, eventsRes] = await Promise.all([
          api.get(`/api/v1/cameras/${cameraId}`),
          api.get(`/api/v1/cameras/${cameraId}/health`),
          api.get(`/api/v1/cameras/${cameraId}/events`, { params: { limit: 20 } }),
        ])
        if (!cancelled) {
          setCamera(camRes.data)
          setHealth(healthRes.data)
          setEvents(eventsRes.data)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [cameraId])

  if (loading) return <div className="loading-state">Loading camera…</div>
  if (!camera) return <div className="empty-state">Camera not found.</div>

  const isFutureProtocol = ['rtsp', 'onvif', 'vendor_api'].includes(camera.source_protocol)

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{camera.name}</h1>
          <div className="page-subtitle">{camera.camera_code} · {camera.department || '—'} / {camera.zone || '—'}</div>
        </div>
        <Link to="/cameras" className="btn-secondary">← Back to registry</Link>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="section-title">Video</div>
          {isFutureProtocol ? (
            <div className="limitation-note">
              This camera is configured with source protocol "{camera.source_protocol}", which is a documented
              future integration point. No real RTSP/ONVIF/vendor connection is implemented in this prototype —
              only the adapter interface exists so a real integration can be plugged in later.
            </div>
          ) : (
            <div className="limitation-note">
              This feed is {camera.source_protocol === 'recorded' ? 'recorded sample footage played back locally' : 'a simulated source with no real video'},
              not a live or low-latency stream. It demonstrates the playback pipeline only.
            </div>
          )}
          <div className="camera-card-video" style={{ borderRadius: 10 }}>
            {camera.playback_url && !videoError ? (
              <video src={resolveMediaUrl(camera.playback_url)} controls style={{ width: '100%', height: '100%' }} onError={() => setVideoError(true)} />
            ) : (
              <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>
                {videoError ? 'Playback failed — sample video file not found at the configured path.' : 'No video source configured for this camera.'}
              </span>
            )}
          </div>
        </div>

        <div className="card">
          <div className="section-title">Status</div>
          <table>
            <tbody>
              <tr><td>Health</td><td><Badge value={camera.status} /></td></tr>
              <tr><td>Source type</td><td>{camera.source_protocol}</td></tr>
              <tr><td>Last heartbeat</td><td>{camera.last_heartbeat ? new Date(camera.last_heartbeat).toLocaleString() : '—'}</td></tr>
              <tr><td>Enabled</td><td>{camera.is_enabled ? 'Yes' : 'No'}</td></tr>
              <tr><td>Location</td><td>{camera.latitude.toFixed(4)}, {camera.longitude.toFixed(4)}</td></tr>
            </tbody>
          </table>

          <div className="section-title" style={{ marginTop: 20 }}>Health History</div>
          {health?.history?.length ? (
            <div className="timeline">
              {health.history.map((h, i) => (
                <div className="timeline-item" key={i}>
                  <div className="timeline-time">{new Date(h.at).toLocaleString()}</div>
                  <div className="timeline-title"><Badge value={h.status} /></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">No recorded health transitions yet.</div>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div className="section-title">Recent Detections on this Camera</div>
        {events.length === 0 ? (
          <div className="empty-state">No analytics events recorded for this camera yet.</div>
        ) : (
          <table>
            <thead>
              <tr><th>Type</th><th>Identifier</th><th>Confidence</th><th>Time</th></tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>{e.event_type}</td>
                  <td>{e.entity_identifier || '—'}</td>
                  <td>{(e.confidence * 100).toFixed(0)}%</td>
                  <td>{new Date(e.event_timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
