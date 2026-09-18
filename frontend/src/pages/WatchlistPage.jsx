import { useEffect, useState, useCallback } from 'react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../components/Toast.jsx'
import Badge from '../components/Badge.jsx'

const EMPTY_FORM = { entity_type: 'stolen_vehicle', identifier: '', display_name: '', reason: '', description: '' }

export default function WatchlistPage() {
  const { isAdmin } = useAuth()
  const pushToast = useToast()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ q: '', entity_type: '', status: '' })
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
      const resp = await api.get('/api/v1/watchlist', { params })
      setRecords(resp.data)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  async function handleSubmit(e) {
    e.preventDefault()
    setFormError(null)
    try {
      await api.post('/api/v1/watchlist', form)
      pushToast('Watchlist record added', form.identifier)
      setForm(EMPTY_FORM)
      setShowForm(false)
      load()
    } catch (err) {
      const detail = err?.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : 'Validation failed.')
    }
  }

  async function toggleStatus(record) {
    const action = record.status === 'active' ? 'disable' : 'enable'
    await api.post(`/api/v1/watchlist/${record.id}/${action}`)
    pushToast(`Record ${action}d`, record.identifier)
    load()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Watchlist Management</h1>
          <div className="page-subtitle">Synthetic demonstration records only. No real individuals' data is stored.</div>
        </div>
        {isAdmin && <button className="btn-primary" onClick={() => setShowForm(!showForm)}>+ Add Record</button>}
      </div>

      <div className="toolbar">
        <input placeholder="Search identifier…" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
        <select value={filters.entity_type} onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}>
          <option value="">All entity types</option>
          <option value="stolen_vehicle">Stolen vehicle</option>
          <option value="blacklisted_vehicle">Blacklisted vehicle</option>
          <option value="wanted_person">Wanted person</option>
          <option value="missing_person">Missing person</option>
          <option value="other">Other</option>
        </select>
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title">Add Watchlist Record</div>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-field">
                <label>Entity Type</label>
                <select value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })}>
                  <option value="stolen_vehicle">Stolen vehicle</option>
                  <option value="blacklisted_vehicle">Blacklisted vehicle</option>
                  <option value="wanted_person">Wanted person</option>
                  <option value="missing_person">Missing person</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-field">
                <label>Identifier (e.g. vehicle number)</label>
                <input value={form.identifier} required onChange={(e) => setForm({ ...form, identifier: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Display Name / Label</label>
                <input value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Reason / Category</label>
                <input value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
              </div>
              <div className="form-field" style={{ gridColumn: '1 / -1' }}>
                <label>Description</label>
                <textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
            </div>
            {formError && <div className="form-error">{formError}</div>}
            <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
              <button className="btn-primary" type="submit">Add Record</button>
              <button className="btn-secondary" type="button" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="loading-state">Loading watchlist…</div>
        ) : records.length === 0 ? (
          <div className="empty-state">No watchlist records match the current filters.</div>
        ) : (
          <table>
            <thead>
              <tr><th>Identifier</th><th>Type</th><th>Label</th><th>Reason</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td>{r.identifier}</td>
                  <td>{r.entity_type.replace('_', ' ')}</td>
                  <td>{r.display_name || '—'}</td>
                  <td>{r.reason || '—'}</td>
                  <td><Badge value={r.status} /></td>
                  <td>
                    {isAdmin && (
                      <button className="btn-secondary" onClick={() => toggleStatus(r)}>
                        {r.status === 'active' ? 'Disable' : 'Enable'}
                      </button>
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
