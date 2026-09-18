import { useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline } from 'react-leaflet'
import { api } from '../services/api'

export default function EntitySearchPage() {
  const [identifier, setIdentifier] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)

  async function handleSearch(e) {
    e.preventDefault()
    if (!identifier.trim()) return
    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const resp = await api.get(`/api/v1/entities/${encodeURIComponent(identifier)}/movement-history`)
      setResult(resp.data)
    } catch (err) {
      setError('Search failed. Try again.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const hasCoords = result?.events?.length > 0
  const center = hasCoords ? [result.events[0].latitude, result.events[0].longitude] : [23.0225, 72.5714]
  const polyline = hasCoords ? result.events.map((e) => [e.latitude, e.longitude]) : []

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Entity / Vehicle Search</h1>
          <div className="page-subtitle">Search a vehicle number or entity identifier to see its detection history across cameras.</div>
        </div>
      </div>

      <form onSubmit={handleSearch} className="toolbar">
        <input
          placeholder="e.g. GJ01XX0001"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          style={{ minWidth: 260 }}
        />
        <button className="btn-primary" type="submit" disabled={loading}>{loading ? 'Searching…' : 'Search'}</button>
      </form>

      {error && <div className="form-error">{error}</div>}

      {searched && !loading && result && result.events.length === 0 && (
        <div className="empty-state">No detection events found for "{identifier}". Try a different identifier, or seed demo data.</div>
      )}

      {hasCoords && (
        <div className="grid-2">
          <div className="card">
            <div className="section-title">Detected Route (chronological)</div>
            <div className="limitation-note">
              This shows detected camera events joined chronologically — it does not represent confirmed
              continuous physical movement between cameras, only the sequence of detections.
            </div>
            <div className="map-wrap" style={{ height: 420 }}>
              <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
                <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <Polyline positions={polyline} pathOptions={{ color: '#3b82f6', weight: 3, dashArray: '6 6' }} />
                {result.events.map((e, i) => (
                  <CircleMarker key={i} center={[e.latitude, e.longitude]} radius={9} pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.85 }}>
                    <Popup>
                      <b>{e.camera_name}</b><br />
                      {new Date(e.timestamp).toLocaleString()}<br />
                      Confidence: {(e.confidence * 100).toFixed(0)}%
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>
          </div>

          <div className="card">
            <div className="section-title">Event Timeline</div>
            <div className="timeline">
              {result.events.map((e, i) => (
                <div className="timeline-item" key={i}>
                  <div className="timeline-time">{new Date(e.timestamp).toLocaleString()}</div>
                  <div className="timeline-title">{e.camera_name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                    Confidence {(e.confidence * 100).toFixed(0)}% · {e.event_type}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
