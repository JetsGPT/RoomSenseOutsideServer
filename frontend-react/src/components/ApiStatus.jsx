import { useState, useEffect } from 'react'
import { pingApi } from '../services/api'

function ApiStatus() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    setStatus('checking')
    const result = await pingApi()
    setStatus(result.ok ? 'online' : 'offline')
  }

  const getStatusText = () => {
    switch (status) {
      case 'checking': return 'Checking API...'
      case 'online': return 'API online'
      case 'offline': return 'API unreachable'
      default: return 'Unknown'
    }
  }

  return (
    <span 
      className={`status-badge ${status}`}
      style={{ cursor: 'pointer' }}
      onClick={checkStatus}
      title="Click to refresh"
    >
      {getStatusText()}
    </span>
  )
}

export default ApiStatus
