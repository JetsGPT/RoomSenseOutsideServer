/**
 * RoomSense Main JavaScript
 * Handles navigation, theme, and common UI components
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadHeader();
    loadFooter();
    refreshApiStatus();
});

/**
 * Initialize theme based on localStorage or system preference
 */
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icon
    updateThemeIcon(newTheme);
}

/**
 * Update theme toggle button icon
 */
function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle');
    if (btn) {
        const sunIcon = `<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
        const moonIcon = `<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
        btn.innerHTML = theme === 'dark' ? sunIcon : moonIcon;
    }
}

/**
 * Load header/navbar
 */
function loadHeader() {
    const user = (typeof getStoredUser === 'function') ? getStoredUser() : null;
    const isLoggedIn = user !== null;
    const meta = user?.user?.user_metadata || {};
    const email = user?.user?.email || '';
    const username = meta.username || email.split('@')[0] || 'User';
    const initial = username.charAt(0).toUpperCase();

    const headerHTML = `
    <nav class="navbar">
        <div class="container flex justify-between items-center">
            <a href="index.html" class="navbar-brand">
                <svg class="icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                </svg>
                RoomSense
            </a>
            
            <!-- Mobile menu button -->
            <button id="mobile-menu-btn" class="mobile-menu-btn btn btn-ghost btn-icon" aria-label="Toggle menu">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>
            
            <div id="nav-links" class="nav-links flex gap-4 items-center">
                <a href="index.html" class="nav-link" data-nav="index.html">Home</a>
                <a href="about.html" class="nav-link" data-nav="about.html">About</a>
                <a href="team.html" class="nav-link" data-nav="team.html">Team</a>
                <a href="contact.html" class="nav-link" data-nav="contact.html">Contact</a>
                ${isLoggedIn ? '<a href="dashboard.html" class="nav-link" data-nav="dashboard.html">Dashboard</a>' : ''}
                
                <button id="theme-toggle" class="btn btn-ghost btn-icon" aria-label="Toggle theme">
                    <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                    </svg>
                </button>
                
                <span id="api-status" class="badge badge-outline">
                    <span class="status-dot status-pending"></span>
                    Checking...
                </span>
                
                ${isLoggedIn ? `
                <div class="user-menu">
                    <button id="user-menu-trigger" class="user-menu-trigger">
                        <div class="user-avatar">${initial}</div>
                        <span class="text-sm">${username}</span>
                        <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                    <div id="user-dropdown" class="user-dropdown">
                        <a href="dashboard.html" class="user-dropdown-item">
                            <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="7" height="7"></rect>
                                <rect x="14" y="3" width="7" height="7"></rect>
                                <rect x="14" y="14" width="7" height="7"></rect>
                                <rect x="3" y="14" width="7" height="7"></rect>
                            </svg>
                            Dashboard
                        </a>
                        <div class="user-dropdown-divider"></div>
                        <button onclick="logout()" class="user-dropdown-item">
                            <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                                <polyline points="16 17 21 12 16 7"></polyline>
                                <line x1="21" y1="12" x2="9" y2="12"></line>
                            </svg>
                            Sign Out
                        </button>
                    </div>
                </div>
                ` : `
                <div class="flex gap-2">
                    <a href="login.html" class="btn btn-ghost btn-sm">Sign In</a>
                    <a href="register.html" class="btn btn-primary btn-sm">Get Started</a>
                </div>
                `}
            </div>
        </div>
    </nav>
    `;

    document.body.insertAdjacentHTML('afterbegin', headerHTML);

    // Theme toggle
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        updateThemeIcon(isDark ? 'dark' : 'light');
    }

    // Mobile menu
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.getElementById('nav-links');
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
    }

    // User dropdown
    const userMenuTrigger = document.getElementById('user-menu-trigger');
    const userDropdown = document.getElementById('user-dropdown');
    if (userMenuTrigger && userDropdown) {
        userMenuTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('open');
        });

        document.addEventListener('click', () => {
            userDropdown.classList.remove('open');
        });
    }

    markActiveNav();
}

/**
 * Load footer
 */
function loadFooter() {
    const footerHTML = `
    <footer class="footer">
        <div class="container">
            <div class="flex justify-between items-center flex-wrap gap-4">
                <div>
                    <div class="flex items-center gap-2 mb-2">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                        </svg>
                        <span class="font-semibold">RoomSense</span>
                    </div>
                    <p class="text-sm text-muted">&copy; 2025 RoomSense. All rights reserved.</p>
                </div>
                <div class="flex gap-6">
                    <a href="about.html" class="text-sm">About</a>
                    <a href="team.html" class="text-sm">Team</a>
                    <a href="contact.html" class="text-sm">Contact</a>
                    <a href="privacy.html" class="text-sm">Privacy</a>
                    <a href="agb.html" class="text-sm">Terms</a>
                </div>
            </div>
        </div>
    </footer>
    `;

    document.body.insertAdjacentHTML('beforeend', footerHTML);
}

/**
 * Mark active navigation link
 */
function markActiveNav() {
    const path = window.location.pathname.split('/').pop() || 'index.html';
    const links = document.querySelectorAll('[data-nav]');
    links.forEach(link => {
        const isActive = link.getAttribute('data-nav') === path;
        link.classList.toggle('active', isActive);
    });
}

/**
 * Refresh API status indicator
 */
async function refreshApiStatus() {
    const el = document.getElementById('api-status');
    if (!el || typeof pingApi !== 'function') return;

    try {
        const result = await pingApi();
        if (result.ok) {
            el.innerHTML = '<span class="status-dot status-online"></span> Online';
            el.className = 'badge badge-outline';
        } else {
            el.innerHTML = '<span class="status-dot status-offline"></span> Offline';
            el.className = 'badge badge-outline';
        }
    } catch (err) {
        el.innerHTML = '<span class="status-dot status-offline"></span> Offline';
        el.className = 'badge badge-outline';
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        error: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        warning: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        info: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
    `;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Cookie Consent Banner
 */
function initCookieConsent() {
    // Check if user has already made a choice
    if (localStorage.getItem('cookieConsent')) {
        return;
    }

    const bannerHTML = `
    <div id="cookie-banner" class="cookie-banner">
        <div class="cookie-content">
            <div class="cookie-text">
                <p>
                    <strong>🍪 Cookie Notice:</strong> We use cookies to enhance your experience. 
                    By continuing to visit this site you agree to our use of cookies.
                    <a href="agb.html" class="text-primary link-underline">Learn more</a>
                </p>
            </div>
            <div class="cookie-buttons">
                <button onclick="acceptCookies('essential')" class="btn btn-outline btn-sm">Essential Only</button>
                <button onclick="acceptCookies('all')" class="btn btn-primary btn-sm">Accept All</button>
            </div>
        </div>
    </div>
    `;

    document.body.insertAdjacentHTML('beforeend', bannerHTML);
}

/**
 * Accept cookies and hide banner
 */
function acceptCookies(type) {
    localStorage.setItem('cookieConsent', type);
    localStorage.setItem('cookieConsentDate', new Date().toISOString());
    
    const banner = document.getElementById('cookie-banner');
    if (banner) {
        banner.style.animation = 'slideInUp 0.3s ease reverse';
        setTimeout(() => banner.remove(), 300);
    }
}

/**
 * Check if analytics cookies are accepted
 */
function hasAnalyticsConsent() {
    return localStorage.getItem('cookieConsent') === 'all';
}

// Initialize cookie consent on page load
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to not interfere with page load
    setTimeout(initCookieConsent, 1000);
});
