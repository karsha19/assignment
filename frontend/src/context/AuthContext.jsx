import { createContext, useContext, useState, useCallback } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('okdriver_token'))
  const [role, setRole] = useState(localStorage.getItem('okdriver_role'))
  const [username, setUsername] = useState(localStorage.getItem('okdriver_username'))

  const login = useCallback(async (usernameInput, password) => {
    const resp = await api.post('/api/v1/auth/login', { username: usernameInput, password })
    const { access_token, role: userRole, username: uname } = resp.data
    localStorage.setItem('okdriver_token', access_token)
    localStorage.setItem('okdriver_role', userRole)
    localStorage.setItem('okdriver_username', uname)
    setToken(access_token)
    setRole(userRole)
    setUsername(uname)
    return userRole
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('okdriver_token')
    localStorage.removeItem('okdriver_role')
    localStorage.removeItem('okdriver_username')
    setToken(null)
    setRole(null)
    setUsername(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, role, username, login, logout, isAdmin: role === 'admin' }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
