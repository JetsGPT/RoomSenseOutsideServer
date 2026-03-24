import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import About from './pages/About'
import Team from './pages/Team'
import Terms from './pages/Terms'
import Login from './pages/Login'
import Register from './pages/Register'
import Boxes from './pages/Boxes'
import Notifications from './pages/Notifications'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="about" element={<About />} />
        <Route path="team" element={<Team />} />
        <Route path="terms" element={<Terms />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="boxes" element={<Boxes />} />
        <Route path="notifications" element={<Notifications />} />
      </Route>
    </Routes>
  )
}

export default App
