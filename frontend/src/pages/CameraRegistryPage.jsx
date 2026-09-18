import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../components/Toast.jsx'
import Badge from '../components/Badge.jsx'

const EMPTY_FORM = {
  camera_code: '', name: '', department: '', zone: '', latitude: '', longitude: '',
  camera_type: '', source_protocol: 'recorded', stream_reference: '',
}

export default function CameraRegistryPage() {
  const { isAdmin } = useAuth()
  const pushToast = useToast()
  const [cameras, setCameras] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ q: '', department: '', zone: '', status: '' })
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState(null)
  const [formError, setFormError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
      const resp = await api.get('/api/v1/cameras', { params })
      setCameras(resp.data)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  function startCreate() {
    setForm(EMPTY_FORM)
    setEditingId(null)
    setFormError(null)
    setShowForm(true)
  }

  function startEdit(cam) {
    setForm({
      camera_code: cam.camera_code, name: cam.name, department: cam.department || '',
      zone: cam.zone || '', latitude: cam.latitude, longitude: cam.longitude,
      camera_type: cam.camera_type || '', source_protocol: cam.source_protocol,
      stream_reference: cam.stream_reference || '',
    })
    setEditingId(cam.id)
    setFormError(null)
    setShowForm(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setFormError(null)
    try {
      const payload = {
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
      }
      if (editingId) {
        const { camera_code, ...updatable } = payload
        await api.patch(`/api/v1/cameras/${editingId}`, updatable)
        pushToast('Camera updated', form.name)
      } else {
        await api.post('/api/v1/cameras', payload)
        pushToast('Camera added', `${form.camera_code} — ${form.name}`)
      }
      setShowForm(false)
      load()
    } catch (err) {
      const detail = err?.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : 'Validation failed. Check the fields.')
    }
  }

  async function toggleEnabled(cam) {
    const action = cam.is_enabled ? 'disable' : 'enable'
    await api.post(`/api/v1/cameras/${cam.id}/${action}`)
    pushToast(`Camera ${action}d`, cam.name)
    load()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Camera Registry</h1>
          <div className="page-subtitle">Onboard, edit and monitor camera sources.</div>
        </div>
        {isAdmin && <button className="btn-primary" onClick={startCreate}>+ Add Camera</button>}
      </div>

      <div className="toolbar">
        <input placeholder="Search by ID or name…" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
        <input placeholder="Department" value={filters.department} onChange={(e) => setFilters({ ...filters, department: e.target.value })} />
        <input placeholder="Zone" value={filters.zone} onChange={(e) => setFilters({ ...filters, zone: e.target.value })} />
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All statuses</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="degraded">Degraded</option>
        </select>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title">{editingId ? 'Edit Camera' : 'Add Camera'}</div>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-field">
                <label>Camera ID</label>
                <input value={form.camera_code} disabled={!!editingId} required
                  onChange={(e) => setForm({ ...form, camera_code: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Name</label>
                <input value={form.name} required onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Department</label>
                <input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Zone</label>
                <input value={form.zone} onChange={(e) => setForm({ ...form, zone: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Latitude</label>
                <input type="number" step="any" value={form.latitude} required
                  onChange={(e) => setForm({ ...form, latitude: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Longitude</label>
                <input type="number" step="any" value={form.longitude} required
                  onChange={(e) => setForm({ ...form, longitude: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Camera Type</label>
                <input value={form.camera_type} onChange={(e) => setForm({ ...form, camera_type: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Source Protocol</label>
                <select value={form.source_protocol} onChange={(e) => setForm({ ...form, source_protocol: e.target.value })}>
                  <option value="recorded">Recorded (sample MP4)</option>
                  <option value="simulated">Simulated (no video)</option>
                  <option value="rtsp">RTSP (future — not implemented)</option>
                  <option value="onvif">ONVIF (future — not implemented)</option>
                  <option value="vendor_api">Vendor API (future — not implemented)</option>
                </select>
              </div>
              <div className="form-field" style={{ gridColumn: '1 / -1' }}>
                <label>Stream Reference (file path or URL to sample MP4)</label>
                <input value={form.stream_reference} onChange={(e) => setForm({ ...form, stream_reference: e.target.value })} />
              </div>
            </div>
            {formError && <div className="form-error">{formError}</div>}
            <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
              <button className="btn-primary" type="submit">{editingId ? 'Save Changes' : 'Add Camera'}</button>
              <button className="btn-secondary" type="button" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="loading-state">Loading cameras…</div>
        ) : cameras.length === 0 ? (
          <div className="empty-state">No cameras match the current filters.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Dept / Zone</th><th>Protocol</th><th>Status</th><th>Enabled</th><th>Last Heartbeat</th><th></th>
              </tr>
            </thead>
            <tbody>
              {cameras.map((cam) => (
                <tr key={cam.id}>
                  <td><Link to={`/cameras/${cam.id}`}>{cam.camera_code}</Link></td>
                  <td>{cam.name}</td>
                  <td>{cam.department || '—'} / {cam.zone || '—'}</td>
                  <td>{cam.source_protocol}</td>
                  <td><Badge value={cam.status} /></td>
                  <td>{cam.is_enabled ? 'Yes' : 'No'}</td>
                  <td>{cam.last_heartbeat ? new Date(cam.last_heartbeat).toLocaleString() : '—'}</td>
                  <td style={{ display: 'flex', gap: 6 }}>
                    {isAdmin && (
                      <>
                        <button className="btn-secondary" onClick={() => startEdit(cam)}>Edit</button>
                        <button className="btn-secondary" onClick={() => toggleEnabled(cam)}>
                          {cam.is_enabled ? 'Disable' : 'Enable'}
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
