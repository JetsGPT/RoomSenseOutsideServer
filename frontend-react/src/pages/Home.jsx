import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { pingApi } from '../services/api'

function Home() {
  const [apiStatus, setApiStatus] = useState({ status: 'checking', detail: 'Awaiting response from middleware' })

  useEffect(() => {
    checkApi()
  }, [])

  const checkApi = async () => {
    setApiStatus({ status: 'checking', detail: 'Pinging https://localhost:8443' })
    const result = await pingApi()
    if (result.ok) {
      setApiStatus({ status: 'Online', detail: JSON.stringify(result.data) })
    } else {
      setApiStatus({ status: 'Offline', detail: 'Could not reach the middleware.' })
    }
  }

  return (
    <div className="flex-col items-center">
      {/* Hero Section */}
      <section 
        className="container py-8 flex-col items-center text-center animate-fade-in"
        style={{ minHeight: '60vh', justifyContent: 'center', display: 'flex', flexDirection: 'column' }}
      >
        <h1 style={{ 
          fontSize: '4rem', 
          marginBottom: '1.5rem', 
          background: 'linear-gradient(to right, var(--dark-slate-green), var(--moss-green))', 
          WebkitBackgroundClip: 'text', 
          WebkitTextFillColor: 'transparent' 
        }}>
          RoomSense
        </h1>
        <p style={{ fontSize: '1.5rem', fontWeight: 500, marginBottom: '1rem', color: 'var(--foreground)' }}>
          Intelligent IoT Sensor Box for Environmental Monitoring
        </p>
        <p style={{ fontSize: '1.1rem', maxWidth: '700px', margin: '0 auto 2rem auto', color: 'var(--muted-foreground)' }}>
          Residential buildings and offices often lack precise, real-time environmental data.
          RoomSense bridges this gap by providing actionable insights on temperature, humidity, air quality,
          noise, and occupancy.
        </p>
        <div className="flex gap-4 justify-center">
          <Link to="/register" className="btn btn-primary" style={{ padding: '0.75rem 2rem', fontSize: '1.1rem' }}>
            Get Started
          </Link>
          <Link to="/about" className="btn btn-outline" style={{ padding: '0.75rem 2rem', fontSize: '1.1rem' }}>
            Learn More
          </Link>
        </div>
      </section>

      {/* Problem & Solution */}
      <section className="container py-8">
        <div className="flex gap-8" style={{ flexWrap: 'wrap' }}>
          <div className="card" style={{ flex: 1, minWidth: '300px' }}>
            <h2 className="mb-4">The Problem</h2>
            <p>
              Many buildings suffer from the absence of a system that delivers precise, real-time
              environmental and occupancy data.
              This leads to energy waste (e.g., lights on in empty rooms) and suboptimal living conditions.
            </p>
          </div>
          <div className="card" style={{ flex: 1, minWidth: '300px', borderColor: 'var(--primary)' }}>
            <h2 className="mb-4">Our Solution</h2>
            <p>
              An innovative IoT sensor box that measures temperature, humidity, air quality, noise levels, and
              occupancy.
              It empowers you to formulate automation strategies—like automatically closing windows or
              adjusting the AC.
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container py-8">
        <h2 className="text-center mb-4">Key Features</h2>
        <div className="flex gap-8 justify-center" style={{ flexWrap: 'wrap', marginTop: '3rem' }}>
          <div className="card" style={{ flex: 1, minWidth: '250px' }}>
            <h3 className="mb-4">Secure Authentication</h3>
            <p>Powered by our Outside Server middleware with Supabase auth, ready for login and registration.</p>
          </div>
          <div className="card" style={{ flex: 1, minWidth: '250px' }}>
            <h3 className="mb-4">Customizable Intervals</h3>
            <p>Capture sensor data at personalized intervals and sync to the cloud.</p>
          </div>
          <div className="card" style={{ flex: 1, minWidth: '250px' }}>
            <h3 className="mb-4">Smart Analysis</h3>
            <p>Get insights like average temperature or peak room occupancy times.</p>
          </div>
          <div className="card" style={{ flex: 1, minWidth: '250px' }}>
            <h3 className="mb-4">Automation Events</h3>
            <p>Set rules such as "Turn on AC if temp &gt; 30°C and room is occupied."</p>
          </div>
          <div className="card" style={{ flex: 1, minWidth: '250px' }}>
            <h3 className="mb-4">Open API</h3>
            <p>Export data or connect the SensorBox with your stack via the REST endpoints.</p>
          </div>
        </div>
      </section>

      {/* API Status & Actions */}
      <section className="container py-8">
        <div className="card" style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 2, minWidth: '260px' }}>
            <h3 className="mb-2">Outside Server Middleware</h3>
            <p className="text-muted">
              Calls are routed to the FastAPI + Supabase backend at https://localhost:8443. 
              Try a health check or jump straight to authentication.
            </p>
            <div className="flex gap-2" style={{ marginTop: '1rem', flexWrap: 'wrap' }}>
              <button onClick={checkApi} className="btn btn-outline">Check API Health</button>
              <Link to="/login" className="btn btn-primary">Go to Login</Link>
              <Link to="/register" className="btn btn-outline">Create Account</Link>
            </div>
          </div>
          <div 
            className="card" 
            style={{ 
              flex: 1, 
              minWidth: '220px', 
              background: 'linear-gradient(135deg, var(--sidebar) 0%, var(--accent) 100%)', 
              color: 'var(--foreground)' 
            }}
          >
            <p style={{ fontSize: '0.95rem' }}>API status</p>
            <h3 style={{ margin: '0.35rem 0' }}>{apiStatus.status}</h3>
            <p className="text-muted" style={{ fontSize: '0.9rem' }}>{apiStatus.detail}</p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
