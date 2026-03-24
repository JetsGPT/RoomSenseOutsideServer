import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  getNotificationLogs,
  getServerNotificationSettings,
  saveServerNotificationSettings,
  getGlobalConfigs,
  saveGlobalConfig,
  deleteGlobalConfig,
  getProviders,
  getBoxes,
} from '../services/api'
import { useAuth } from '../context/AuthContext'

function Notifications() {
  const { isAuthenticated } = useAuth()

  // ─── Logs State ───
  const [logs, setLogs] = useState([])
  const [logsLoading, setLogsLoading] = useState(true)
  const [logsError, setLogsError] = useState('')
  const [filterServerId, setFilterServerId] = useState('')

  // ─── Server Settings State ───
  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState('')
  const [settings, setSettings] = useState(null)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [settingsError, setSettingsError] = useState('')
  const [settingsSaved, setSettingsSaved] = useState(false)

  // ─── Global Config State ───
  const [configs, setConfigs] = useState([])
  const [configsLoading, setConfigsLoading] = useState(true)
  const [configsError, setConfigsError] = useState('')
  const [newConfigKey, setNewConfigKey] = useState('')
  const [newConfigValue, setNewConfigValue] = useState('')
  const [newConfigDesc, setNewConfigDesc] = useState('')

  // ─── Providers State ───
  const [providers, setProviders] = useState([])
  const [providersLoading, setProvidersLoading] = useState(true)

  // ─── Section Collapse State ───
  const [openSections, setOpenSections] = useState({
    logs: true,
    settings: false,
    config: false,
    providers: false,
  })

  const toggleSection = (key) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  // ─── Load Data ───
  useEffect(() => {
    if (isAuthenticated) {
      fetchLogs()
      fetchConfigs()
      fetchProviders()
      fetchServers()
    }
  }, [isAuthenticated])

  const fetchServers = async () => {
    try {
      const data = await getBoxes()
      const owned = data?.servers?.owned || []
      const assigned = data?.servers?.assigned || []
      setServers([...owned, ...assigned])
    } catch {}
  }

  const fetchLogs = async (serverId = null) => {
    setLogsLoading(true)
    setLogsError('')
    try {
      const data = await getNotificationLogs(serverId || null)
      setLogs(data.logs || [])
    } catch (err) {
      setLogsError(err.message)
    } finally {
      setLogsLoading(false)
    }
  }

  const handleFilterLogs = () => {
    fetchLogs(filterServerId.trim() || null)
  }

  const fetchSettings = async (serverId) => {
    if (!serverId) return
    setSettingsLoading(true)
    setSettingsError('')
    setSettingsSaved(false)
    try {
      const data = await getServerNotificationSettings(serverId)
      setSettings(data.settings || {})
    } catch (err) {
      setSettingsError(err.message)
      setSettings(null)
    } finally {
      setSettingsLoading(false)
    }
  }

  const handleSaveSettings = async () => {
    if (!selectedServer || !settings) return
    setSettingsError('')
    setSettingsSaved(false)
    try {
      await saveServerNotificationSettings(selectedServer, settings)
      setSettingsSaved(true)
      setTimeout(() => setSettingsSaved(false), 3000)
    } catch (err) {
      setSettingsError(err.message)
    }
  }

  const fetchConfigs = async () => {
    setConfigsLoading(true)
    setConfigsError('')
    try {
      const data = await getGlobalConfigs()
      setConfigs(data.configs || [])
    } catch (err) {
      setConfigsError(err.message)
    } finally {
      setConfigsLoading(false)
    }
  }

  const handleAddConfig = async (e) => {
    e.preventDefault()
    setConfigsError('')
    try {
      const parsed = JSON.parse(newConfigValue)
      await saveGlobalConfig(newConfigKey, parsed, newConfigDesc || null)
      setNewConfigKey('')
      setNewConfigValue('')
      setNewConfigDesc('')
      fetchConfigs()
    } catch (err) {
      setConfigsError(err.message === 'Unexpected token' || err instanceof SyntaxError
        ? 'Config value must be valid JSON'
        : err.message)
    }
  }

  const handleDeleteConfig = async (key) => {
    if (!confirm(`Delete config "${key}"?`)) return
    try {
      await deleteGlobalConfig(key)
      fetchConfigs()
    } catch (err) {
      setConfigsError(err.message)
    }
  }

  const fetchProviders = async () => {
    setProvidersLoading(true)
    try {
      const data = await getProviders()
      setProviders(data.providers || [])
    } catch {}
    setProvidersLoading(false)
  }

  // ─── Auth Guard ───
  if (!isAuthenticated) {
    return (
      <div className="container py-8 animate-fade-in">
        <div className="card text-center">
          <h2 className="mb-4">Authentication Required</h2>
          <p className="mb-4 text-muted">Please log in to manage notifications.</p>
          <div className="flex gap-4 justify-center">
            <Link to="/login" className="btn btn-primary">Login</Link>
            <Link to="/register" className="btn btn-outline">Register</Link>
          </div>
        </div>
      </div>
    )
  }

  // ─── Section Header Component ───
  const SectionHeader = ({ title, sectionKey, badge }) => (
    <button
      onClick={() => toggleSection(sectionKey)}
      className="flex justify-between items-center w-full"
      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'inherit' }}
    >
      <h2 style={{ margin: 0 }}>{title}</h2>
      <div className="flex items-center gap-2">
        {badge && <span className="badge badge-outline">{badge}</span>}
        <span style={{ fontSize: '1.25rem', transition: 'transform 0.2s', transform: openSections[sectionKey] ? 'rotate(180deg)' : 'rotate(0deg)' }}>
          ▼
        </span>
      </div>
    </button>
  )

  return (
    <div className="container py-8 animate-fade-in">
      <h1 className="mb-8">Notifications</h1>

      {/* ─── Notification Logs ─── */}
      <div className="card mb-6">
        <SectionHeader title="📋 Notification Logs" sectionKey="logs" badge={`${logs.length} entries`} />
        {openSections.logs && (
          <div style={{ marginTop: '1rem' }}>
            {/* Filter */}
            <div className="flex gap-2 mb-4" style={{ flexWrap: 'wrap' }}>
              <input
                type="text"
                className="input"
                placeholder="Filter by Server ID..."
                value={filterServerId}
                onChange={(e) => setFilterServerId(e.target.value)}
                style={{ flex: 1, minWidth: '200px', maxWidth: '400px' }}
              />
              <button onClick={handleFilterLogs} className="btn btn-outline">Filter</button>
              <button onClick={() => { setFilterServerId(''); fetchLogs() }} className="btn btn-ghost">Clear</button>
            </div>

            {logsError && <div className="alert alert-error mb-4">{logsError}</div>}

            {logsLoading ? (
              <p className="text-muted">Loading logs...</p>
            ) : logs.length === 0 ? (
              <p className="text-muted">No notification logs found.</p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left' }}>
                      <th style={thStyle}>Time</th>
                      <th style={thStyle}>Provider</th>
                      <th style={thStyle}>Target</th>
                      <th style={thStyle}>Title</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Server</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, i) => (
                      <tr key={log.id || i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={tdStyle}>{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</td>
                        <td style={tdStyle}>
                          <span className="badge badge-outline">{log.provider || '—'}</span>
                        </td>
                        <td style={tdStyle}>{log.target || '—'}</td>
                        <td style={tdStyle}>{log.title || '—'}</td>
                        <td style={tdStyle}>
                          <span className={`badge ${log.success ? 'badge-success' : 'badge-destructive'}`}>
                            {log.success ? '✓ Sent' : '✗ Failed'}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {log.server_id ? log.server_id.slice(0, 8) + '…' : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ─── Server Notification Settings ─── */}
      <div className="card mb-6">
        <SectionHeader title="⚙️ Server Settings" sectionKey="settings" />
        {openSections.settings && (
          <div style={{ marginTop: '1rem' }}>
            {/* Server Selector */}
            <div className="flex gap-2 mb-4" style={{ flexWrap: 'wrap' }}>
              <select
                className="input"
                value={selectedServer}
                onChange={(e) => { setSelectedServer(e.target.value); fetchSettings(e.target.value) }}
                style={{ flex: 1, maxWidth: '400px' }}
              >
                <option value="">Select a server...</option>
                {servers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name || s.id} {s.role === 'owner' ? '(Owner)' : '(Assigned)'}
                  </option>
                ))}
              </select>
            </div>

            {settingsError && <div className="alert alert-error mb-4">{settingsError}</div>}
            {settingsSaved && <div className="alert alert-success mb-4">Settings saved successfully!</div>}

            {settingsLoading ? (
              <p className="text-muted">Loading settings...</p>
            ) : settings && selectedServer ? (
              <div className="flex-col gap-4">
                {/* ntfy Settings */}
                <div className="mb-4">
                  <h4 className="mb-2">ntfy</h4>
                  <div className="flex gap-4 items-center mb-2" style={{ flexWrap: 'wrap' }}>
                    <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={settings.ntfy_enabled ?? true}
                        onChange={(e) => setSettings({ ...settings, ntfy_enabled: e.target.checked })}
                      />
                      Enabled
                    </label>
                  </div>
                  <div className="flex gap-4 mb-2" style={{ flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                      <label className="label">Base URL</label>
                      <input
                        type="text"
                        className="input"
                        placeholder="https://ntfy.sh"
                        value={settings.ntfy_base_url || ''}
                        onChange={(e) => setSettings({ ...settings, ntfy_base_url: e.target.value })}
                      />
                    </div>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                      <label className="label">Default Topic</label>
                      <input
                        type="text"
                        className="input"
                        placeholder="roomsense-alerts"
                        value={settings.ntfy_default_topic || ''}
                        onChange={(e) => setSettings({ ...settings, ntfy_default_topic: e.target.value })}
                      />
                    </div>
                  </div>
                </div>

                {/* Email / SMS toggles */}
                <div className="flex gap-6 mb-4" style={{ flexWrap: 'wrap' }}>
                  <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.email_enabled ?? false}
                      onChange={(e) => setSettings({ ...settings, email_enabled: e.target.checked })}
                    />
                    Email Notifications
                  </label>
                  <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.sms_enabled ?? false}
                      onChange={(e) => setSettings({ ...settings, sms_enabled: e.target.checked })}
                    />
                    SMS Notifications
                  </label>
                </div>

                {/* DND Schedule */}
                <div className="mb-4">
                  <h4 className="mb-2">Do Not Disturb</h4>
                  <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
                    <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={settings.dnd_enabled ?? false}
                        onChange={(e) => setSettings({ ...settings, dnd_enabled: e.target.checked })}
                      />
                      Enabled
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="time"
                        className="input"
                        value={settings.dnd_start || '22:00'}
                        onChange={(e) => setSettings({ ...settings, dnd_start: e.target.value })}
                        style={{ width: 'auto' }}
                        disabled={!settings.dnd_enabled}
                      />
                      <span className="text-muted">to</span>
                      <input
                        type="time"
                        className="input"
                        value={settings.dnd_end || '07:00'}
                        onChange={(e) => setSettings({ ...settings, dnd_end: e.target.value })}
                        style={{ width: 'auto' }}
                        disabled={!settings.dnd_enabled}
                      />
                    </div>
                  </div>
                </div>

                <button onClick={handleSaveSettings} className="btn btn-primary">
                  Save Settings
                </button>
              </div>
            ) : !selectedServer ? (
              <p className="text-muted">Select a server to view its notification settings.</p>
            ) : null}
          </div>
        )}
      </div>

      {/* ─── Global Configuration ─── */}
      <div className="card mb-6">
        <SectionHeader title="🌐 Global Configuration" sectionKey="config" badge={`${configs.length} configs`} />
        {openSections.config && (
          <div style={{ marginTop: '1rem' }}>
            {configsError && <div className="alert alert-error mb-4">{configsError}</div>}

            {configsLoading ? (
              <p className="text-muted">Loading configs...</p>
            ) : (
              <>
                {/* Existing Configs */}
                {configs.length > 0 && (
                  <div className="mb-6">
                    {configs.map((cfg) => (
                      <div
                        key={cfg.config_key}
                        className="flex justify-between items-center p-4 mb-2"
                        style={{
                          background: 'var(--muted)',
                          borderRadius: 'var(--radius-md)',
                          gap: '1rem',
                          flexWrap: 'wrap',
                        }}
                      >
                        <div style={{ flex: 1, minWidth: '200px' }}>
                          <strong>{cfg.config_key}</strong>
                          {cfg.description && <p className="text-muted text-sm">{cfg.description}</p>}
                          <code style={{ fontSize: '0.75rem', display: 'block', marginTop: '0.25rem', wordBreak: 'break-all' }}>
                            {JSON.stringify(cfg.config_value)}
                          </code>
                        </div>
                        <button
                          onClick={() => handleDeleteConfig(cfg.config_key)}
                          className="btn btn-destructive btn-sm"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Config Form */}
                <form onSubmit={handleAddConfig} className="flex-col gap-4">
                  <h4 className="mb-2">Add / Update Config</h4>
                  <div className="flex gap-4 mb-2" style={{ flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: '150px' }}>
                      <label className="label">Key</label>
                      <input
                        type="text"
                        className="input"
                        placeholder="ntfy_config"
                        value={newConfigKey}
                        onChange={(e) => setNewConfigKey(e.target.value)}
                        required
                      />
                    </div>
                    <div style={{ flex: 1, minWidth: '150px' }}>
                      <label className="label">Description</label>
                      <input
                        type="text"
                        className="input"
                        placeholder="Optional description"
                        value={newConfigDesc}
                        onChange={(e) => setNewConfigDesc(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="mb-2">
                    <label className="label">Value (JSON)</label>
                    <textarea
                      className="input"
                      placeholder='{"base_url": "https://ntfy.sh"}'
                      value={newConfigValue}
                      onChange={(e) => setNewConfigValue(e.target.value)}
                      required
                      rows={3}
                      style={{ height: 'auto', resize: 'vertical' }}
                    />
                  </div>
                  <button type="submit" className="btn btn-primary">Save Config</button>
                </form>
              </>
            )}
          </div>
        )}
      </div>

      {/* ─── Providers ─── */}
      <div className="card mb-6">
        <SectionHeader title="🔌 Providers" sectionKey="providers" badge={`${providers.length} available`} />
        {openSections.providers && (
          <div style={{ marginTop: '1rem' }}>
            {providersLoading ? (
              <p className="text-muted">Loading providers...</p>
            ) : providers.length === 0 ? (
              <p className="text-muted">No providers registered.</p>
            ) : (
              <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                {providers.map((name) => (
                  <span key={name} className="badge badge-primary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                    {name}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Styles ───
const thStyle = { padding: '0.5rem 0.75rem', fontWeight: 600, whiteSpace: 'nowrap' }
const tdStyle = { padding: '0.5rem 0.75rem' }

export default Notifications
