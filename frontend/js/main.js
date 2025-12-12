document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadHeader();
    loadFooter();
    refreshApiStatus();
});

function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icon
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

function loadHeader() {
    const headerHTML = `
    <nav class="navbar">
        <div class="container flex justify-between items-center">
            <a href="index.html" class="flex items-center gap-2">
                <span style="font-family: var(--font-heading); font-weight: 700; font-size: 1.25rem; color: hsl(var(--foreground));">
                    RoomSense Outside
                </span>
            </a>
            <div class="flex gap-4 items-center" style="flex-wrap: wrap;">
                <button id="theme-toggle" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 1.2rem;" aria-label="Toggle theme">
                    🌙
                </button>
                <a href="index.html" class="nav-link" data-nav="index.html">Home</a>
                <a href="about.html" class="nav-link" data-nav="about.html">About</a>
                <a href="team.html" class="nav-link" data-nav="team.html">Team</a>
                <a href="agb.html" class="nav-link" data-nav="agb.html">Terms</a>
                <span id="api-status" class="nav-link" style="font-size: 0.85rem; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 0.35rem 0.75rem; background: rgba(255,255,255,0.15);">
                    Checking API...
                </span>
                <div id="auth-links" class="flex gap-2">
                    <a href="login.html" class="btn btn-outline" style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">Login</a>
                    <a href="register.html" class="btn btn-primary" style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">Register</a>
                </div>
                <div id="user-menu" class="hidden flex items-center gap-2">
                    <span id="username-display" class="text-muted" style="font-size: 0.875rem;"></span>
                    <button onclick="logout()" class="btn btn-outline" style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">Logout</button>
                </div>
            </div>
        </div>
    </nav>
    `;

    document.body.insertAdjacentHTML('afterbegin', headerHTML);

    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        themeBtn.textContent = isDark ? '☀️' : '🌙';
    }

    markActiveNav();
    updateAuthUI();
}

function loadFooter() {
    const footerHTML = `
    <footer class="footer">
        <div class="container flex justify-between items-center">
            <div>
                <span style="font-family: var(--font-heading); font-weight: 600;">RoomSense Outside</span>
                <p style="font-size: 0.875rem;">&copy; 2025 RoomSense. All rights reserved.</p>
            </div>
            <div class="flex gap-4">
                <a href="agb.html" class="nav-link" style="font-size: 0.875rem;">Terms</a>
                <a href="about.html" class="nav-link" style="font-size: 0.875rem;">About</a>
            </div>
        </div>
    </footer>
    `;

    // Insert at the end of body
    document.body.insertAdjacentHTML('beforeend', footerHTML);
}

function updateAuthUI() {
    const user = (typeof getStoredUser === 'function') ? getStoredUser() : JSON.parse(localStorage.getItem('user'));
    const authLinks = document.getElementById('auth-links');
    const userMenu = document.getElementById('user-menu');
    const usernameDisplay = document.getElementById('username-display');

    if (user && authLinks && userMenu) {
        authLinks.classList.add('hidden');
        authLinks.style.display = 'none';
        userMenu.classList.remove('hidden');
        userMenu.style.display = 'flex';
        const meta = user?.user?.user_metadata || {};
        const email = user?.user?.email;
        if (usernameDisplay) usernameDisplay.textContent = meta.username || email || 'Signed in';
    } else {
        if (authLinks) {
            authLinks.classList.remove('hidden');
            authLinks.style.display = 'flex';
        }
        if (userMenu) {
            userMenu.classList.add('hidden');
            userMenu.style.display = 'none';
        }
    }
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

function markActiveNav() {
    const path = window.location.pathname.split('/').pop() || 'index.html';
    const links = document.querySelectorAll('[data-nav]');
    links.forEach(link => {
        const isActive = link.getAttribute('data-nav') === path;
        link.style.backgroundColor = isActive ? 'rgba(255,255,255,0.25)' : 'transparent';
    });
}

async function refreshApiStatus() {
    const el = document.getElementById('api-status');
    if (!el || typeof pingApi !== 'function') return;
    try {
        el.textContent = 'Checking API...';
        const result = await pingApi();
        if (result.ok) {
            el.textContent = 'API online';
            el.style.color = 'var(--foreground)';
            el.style.borderColor = 'var(--accent)';
        } else {
            el.textContent = 'API unreachable';
            el.style.color = 'hsl(var(--destructive))';
            el.style.borderColor = 'hsl(var(--destructive))';
        }
    } catch (err) {
        el.textContent = 'API unreachable';
        el.style.color = 'hsl(var(--destructive))';
        el.style.borderColor = 'hsl(var(--destructive))';
    }
}
