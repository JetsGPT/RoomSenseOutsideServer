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
