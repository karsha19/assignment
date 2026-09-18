import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

const STATUS_COLORS = { online: '#22c55e', offline: '#93a1bd', degraded: '#f59e0b' }

export default function CameraMapPage() {
  const [cameras, setCameras] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [camRes, alertRes] = await Promise.all([
          api.get('/api/v1/cameras'),
          api.get('/api/v1/alerts', { params: { status: 'new', limit: 100 } }),
        ])
        setCameras(camRes.data)
        setAlerts(alertRes.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const alertCameraIds = new Set(alerts.map((a) => a.camera_id))
  const center = cameras.length
    ? [cameras[0].latitude, cameras[0].longitude]
    : [23.0225, 72.5714]

  if (loading) return <div className="loading-state">Loading map…</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Camera Map</h1>
          <div className="page-subtitle">Marker color reflects health; a red ring indicates an active unresolved alert.</div>
        </div>
      </div>
      <div className="map-wrap">
        <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {cameras.map((cam) => (
            <CircleMarker
              key={cam.id}
              center={[cam.latitude, cam.longitude]}
              radius={alertCameraIds.has(cam.id) ? 12 : 8}
              pathOptions={{
                color: alertCameraIds.has(cam.id) ? '#ef4444' : STATUS_COLORS[cam.status] || '#93a1bd',
                fillColor: STATUS_COLORS[cam.status] || '#93a1bd',
                fillOpacity: 0.8,
                weight: alertCameraIds.has(cam.id) ? 3 : 1,
              }}
            >
              <Popup>
                <div style={{ fontSize: 13 }}>
                  <b>{cam.name}</b><br />
                  {cam.camera_code} · {cam.status}<br />
                  {cam.department || '—'} / {cam.zone || '—'}<br />
                  <Link to={`/cameras/${cam.id}`}>Open details</Link>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
