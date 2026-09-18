import { useEffect, useState, useCallback } from 'react'
import { api } from '../services/api'

export default function AuditPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ action: '', resource_type: '' })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
      const resp = await api.get('/api/v1/audit-logs', { params: { ...params, limit: 200 } })
      setLogs(resp.data)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Audit History</h1>
          <div className="page-subtitle">Administrator-only view of important system operations.</div>
        </div>
      </div>

      <div className="toolbar">
        <input placeholder="Filter by action…" value={filters.action} onChange={(e) => setFilters({ ...filters, action: e.target.value })} />
        <input placeholder="Filter by resource type…" value={filters.resource_type} onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })} />
      </div>

      <div className="card">
        {loading ? (
          <div className="loading-state">Loading audit logs…</div>
        ) : logs.length === 0 ? (
          <div className="empty-state">No audit records match the current filters.</div>
        ) : (
          <table>
            <thead>
              <tr><th>Action</th><th>Resource</th><th>Resource ID</th><th>Actor</th><th>Result</th><th>Time</th></tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{l.action}</td>
                  <td>{l.resource_type}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{l.resource_id || '—'}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 11 }}>{l.actor_user_id || 'system'}</td>
                  <td>{l.result}</td>
                  <td>{new Date(l.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
