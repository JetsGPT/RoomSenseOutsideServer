const API_URL = import.meta.env.VITE_API_URL || 'https://localhost:8443'

function extractError(detail, fallback) {
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (typeof detail === 'object') {
    return detail.message || detail.error || fallback
  }
  return fallback
}

function getAuthHeaders() {
  try {
    const user = JSON.parse(localStorage.getItem('user'))
    if (user?.access_token) {
      return { 'Authorization': `Bearer ${user.access_token}` }
    }
  } catch {}
  return {}
}

export async function register(username, email, password) {
  const response = await fetch(`${API_URL}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, email, password }),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = extractError(data.detail, 'Registration failed')
    throw new Error(message)
  }

  return data
}

export async function login(email, password) {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = extractError(data.detail, 'Login failed')
    throw new Error(message)
  }

  return data
}

export async function logout() {
  try {
    const response = await fetch(`${API_URL}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })
    return { ok: response.ok }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

export async function getBoxes() {
  const response = await fetch(`${API_URL}/api/boxes`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = extractError(data.detail, 'Failed to fetch boxes')
    throw new Error(message)
  }

  return data
}

export async function pingApi() {
  try {
    const response = await fetch(`${API_URL}/`)
    const data = await response.json().catch(() => ({}))
    return { ok: response.ok, data }
  } catch (error) {
    return { ok: false, error: error.message }
  }
}

// ─── Notification API ───

export async function getNotificationLogs(serverId = null, limit = 100) {
  const endpoint = serverId
    ? `/api/v1/servers/${serverId}/notifications/logs?limit=${limit}`
    : `/api/v1/notifications/logs?limit=${limit}`

  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: { ...getAuthHeaders() },
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to fetch notification logs'))
  return data
}

export async function getServerNotificationSettings(serverId) {
  const response = await fetch(`${API_URL}/api/v1/servers/${serverId}/notification-settings`, {
    headers: { ...getAuthHeaders() },
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to fetch notification settings'))
  return data
}

export async function saveServerNotificationSettings(serverId, settings) {
  const response = await fetch(`${API_URL}/api/v1/servers/${serverId}/notification-settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(settings),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to save notification settings'))
  return data
}

export async function getGlobalConfigs() {
  const response = await fetch(`${API_URL}/api/v1/config/global`, {
    headers: { ...getAuthHeaders() },
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to fetch global configs'))
  return data
}

export async function saveGlobalConfig(configKey, configValue, description = null) {
  const response = await fetch(`${API_URL}/api/v1/config/global`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({ config_key: configKey, config_value: configValue, description }),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to save global config'))
  return data
}

export async function deleteGlobalConfig(configKey) {
  const response = await fetch(`${API_URL}/api/v1/config/global/${configKey}`, {
    method: 'DELETE',
    headers: { ...getAuthHeaders() },
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to delete global config'))
  return data
}

export async function getProviders() {
  const response = await fetch(`${API_URL}/api/v1/relay/providers`)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractError(data.detail, 'Failed to fetch providers'))
  return data
}
