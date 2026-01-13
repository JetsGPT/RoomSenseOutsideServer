import { Link, NavLink } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import ApiStatus from './ApiStatus'

function Header() {
  const { theme, toggleTheme } = useTheme()
  const { user, logout, isAuthenticated } = useAuth()

  const getDisplayName = () => {
    if (!user) return ''
    const meta = user?.user_metadata || {}
    return meta.username || user?.email || 'Signed in'
  }

  return (
    <nav className="navbar">
      <div className="container flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2">
          <span style={{ 
            fontFamily: 'var(--font-heading)', 
            fontWeight: 700, 
            fontSize: '1.25rem', 
            color: 'var(--foreground)' 
          }}>
            RoomSense Outside
          </span>
        </Link>
        
        <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
          <button 
            onClick={toggleTheme}
            className="btn btn-outline" 
            style={{ padding: '0.25rem 0.5rem', fontSize: '1.2rem' }}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Home
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            About
          </NavLink>
          <NavLink to="/team" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Team
          </NavLink>
          <NavLink to="/terms" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Terms
          </NavLink>
          
          <ApiStatus />
          
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <span className="text-muted" style={{ fontSize: '0.875rem' }}>
                {getDisplayName()}
              </span>
              <button 
                onClick={logout}
                className="btn btn-outline" 
                style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <Link to="/login" className="btn btn-outline" style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}>
                Login
              </Link>
              <Link to="/register" className="btn btn-primary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}>
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Header
