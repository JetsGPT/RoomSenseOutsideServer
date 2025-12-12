const API_URL = window.__ROOMSENSE_API__ || 'https://localhost:8443';

function extractError(detail, fallback) {
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object') {
        return detail.message || detail.error || fallback;
    }
    return fallback;
}

async function register(username, email, password) {
    const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const message = extractError(data.detail, 'Registration failed');
        throw new Error(message);
    }

    return data;
}

async function login(email, password) {
    const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const message = extractError(data.detail, 'Login failed');
        throw new Error(message);
    }

    // Persist session payload for UI display
    if (data?.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
}

function getStoredUser() {
    try {
        const raw = localStorage.getItem('user');
        return raw ? JSON.parse(raw) : null;
    } catch (err) {
        console.warn('Failed to parse stored user', err);
        return null;
    }
}

async function pingApi() {
    const response = await fetch(`${API_URL}/`);
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, data };
}
