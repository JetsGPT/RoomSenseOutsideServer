import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getBoxes } from '../services/api'
import { useAuth } from '../context/AuthContext'

function Boxes() {
  const [boxes, setBoxes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      fetchBoxes()
    } else {
      setLoading(false)
    }
  }, [isAuthenticated])

  const fetchBoxes = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getBoxes()
      setBoxes(Array.isArray(data) ? data : data.boxes || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="container py-8 animate-fade-in">
        <div className="card text-center">
          <h2 className="mb-4">Authentication Required</h2>
          <p className="mb-4 text-muted">Please log in to view your RoomSense boxes.</p>
          <div className="flex gap-4 justify-center">
            <Link to="/login" className="btn btn-primary">Login</Link>
            <Link to="/register" className="btn btn-outline">Register</Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-8 animate-fade-in">
      <div className="flex justify-between items-center mb-4">
        <h1>Your RoomSense Boxes</h1>
        <button onClick={fetchBoxes} className="btn btn-outline" disabled={loading}>
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {error && (
        <div className="card mb-4" style={{ borderColor: 'var(--destructive)' }}>
          <p className="error-message">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="card text-center">
          <p className="text-muted">Loading boxes...</p>
        </div>
      ) : boxes.length === 0 ? (
        <div className="card text-center">
          <h3 className="mb-4">No Boxes Found</h3>
          <p className="text-muted">
            You don't have any RoomSense boxes registered yet. 
            Connect your first box to start monitoring!
          </p>
        </div>
      ) : (
        <div className="flex gap-4" style={{ flexWrap: 'wrap' }}>
          {boxes.map((box, index) => (
            <div 
              key={box.id || box.box_id || index} 
              className="card" 
              style={{ flex: '1 1 300px', minWidth: '280px', maxWidth: '400px' }}
            >
              <div className="flex justify-between items-center mb-4">
                <h3>{box.name || box.box_name || `Box ${index + 1}`}</h3>
                <span 
                  className="status-badge"
                  style={{ 
                    backgroundColor: box.online || box.is_online ? 'var(--primary)' : 'var(--muted)',
                    color: box.online || box.is_online ? 'var(--primary-foreground)' : 'var(--foreground)'
                  }}
                >
                  {box.online || box.is_online ? '● Online' : '○ Offline'}
                </span>
              </div>
              
              {box.description && (
                <p className="text-muted mb-4" style={{ fontSize: '0.875rem' }}>
                  {box.description}
                </p>
              )}

              <div style={{ fontSize: '0.875rem' }}>
                {box.id && (
                  <p className="mb-2">
                    <strong>ID:</strong> <code style={{ background: 'var(--muted)', padding: '0.125rem 0.375rem', borderRadius: '4px' }}>{box.id}</code>
                  </p>
                )}
                {box.location && (
                  <p className="mb-2">
                    <strong>Location:</strong> {box.location}
                  </p>
                )}
                {box.last_seen && (
                  <p className="mb-2">
                    <strong>Last Seen:</strong> {new Date(box.last_seen).toLocaleString()}
                  </p>
                )}
                {box.created_at && (
                  <p className="text-muted">
                    <strong>Added:</strong> {new Date(box.created_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Boxes
