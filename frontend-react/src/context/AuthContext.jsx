import { createContext, useContext, useState, useEffect } from 'react'
import * as api from '../services/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const login = async (email, password) => {
    const data = await api.login(email, password)
    if (data?.user) {
      setUser(data.user)
      localStorage.setItem('user', JSON.stringify(data.user))
    }
    return data
  }

  const register = async (username, email, password) => {
    const data = await api.register(username, email, password)
    return data
  }

  const logout = async () => {
    // Call server-side logout
    await api.logout()
    // Clear local state
    setUser(null)
    localStorage.removeItem('user')
  }

  const isAuthenticated = !!user

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
