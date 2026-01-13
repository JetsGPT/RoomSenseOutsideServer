import { Link } from 'react-router-dom'

function Footer() {
  return (
    <footer className="footer">
      <div className="container flex justify-between items-center">
        <div>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600 }}>
            RoomSense Outside
          </span>
          <p style={{ fontSize: '0.875rem' }}>
            &copy; 2026 RoomSense. All rights reserved.
          </p>
        </div>
        <div className="flex gap-4">
          <Link to="/terms" className="nav-link" style={{ fontSize: '0.875rem' }}>
            Terms
          </Link>
          <Link to="/about" className="nav-link" style={{ fontSize: '0.875rem' }}>
            About
          </Link>
        </div>
      </div>
    </footer>
  )
}

export default Footer
