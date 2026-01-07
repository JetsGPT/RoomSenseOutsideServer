const API_URL = window.__ROOMSENSE_API__ || 'https://localhost:8443';

/**
 * Extract error message from API response
 */
function extractError(detail, fallback) {
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object') {
        return detail.message || detail.error || fallback;
    }
    return fallback;
}

/**
 * Register a new user
 */
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

/**
 * Login user
 */
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

/**
 * Logout user - clear session data
 */
function logout() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

/**
 * Get stored user from localStorage
 */
function getStoredUser() {
    try {
        const raw = localStorage.getItem('user');
        return raw ? JSON.parse(raw) : null;
    } catch (err) {
        console.warn('Failed to parse stored user', err);
        return null;
    }
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return getStoredUser() !== null;
}

/**
 * Get stored access token
 */
function getAccessToken() {
    const user = getStoredUser();
    return user?.session?.access_token || null;
}

/**
 * Ping API health endpoint
 */
async function pingApi() {
    try {
        const response = await fetch(`${API_URL}/`);
        const data = await response.json().catch(() => ({}));
        return { ok: response.ok, data };
    } catch (error) {
        return { ok: false, error: error.message };
    }
}

/**
 * Make authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
    const token = getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
    };

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(extractError(data.detail, 'Request failed'));
    }

    return data;
}

/**
 * Redirect to login if not authenticated (for protected pages)
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

/**
 * Request password reset
 */
async function requestPasswordReset(email) {
    const response = await fetch(`${API_URL}/forgot-password`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const message = extractError(data.detail, 'Password reset request failed');
        throw new Error(message);
    }

    return data;
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate password strength
 * Returns: { valid: boolean, score: number (0-4), message: string }
 */
function validatePasswordStrength(password) {
    let score = 0;
    const messages = [];

    if (password.length < 6) {
        return { valid: false, score: 0, message: 'Password must be at least 6 characters' };
    }

    if (password.length >= 6) score++;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password) || /[^A-Za-z0-9]/.test(password)) score++;

    const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong'];
    
    return {
        valid: true,
        score: score,
        message: strengthLabels[score - 1] || 'Weak'
    };
}

/**
 * Debounce function for input validation
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Session timeout handler - auto logout after inactivity
 */
let sessionTimeout;
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

function resetSessionTimeout() {
    if (sessionTimeout) {
        clearTimeout(sessionTimeout);
    }
    
    if (isAuthenticated()) {
        sessionTimeout = setTimeout(() => {
            if (typeof showToast === 'function') {
                showToast('Session expired. Please log in again.', 'warning');
            }
            setTimeout(logout, 2000);
        }, SESSION_TIMEOUT_MS);
    }
}

// Reset timeout on user activity
if (typeof document !== 'undefined') {
    ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, debounce(resetSessionTimeout, 1000), { passive: true });
    });
    
    // Initialize timeout if authenticated
    if (isAuthenticated()) {
        resetSessionTimeout();
    }
}
