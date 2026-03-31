import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Landing from "./pages/Landing"
import DataAnalysisAssistant from "./pages/DataAnalysisAssistant"
import Login from "./pages/Login"
import Register from "./pages/Register"
import './App.css'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setIsAuthenticated(true)
    }
    setIsLoading(false)
  }, [])

  const handleLogin = (token) => {
    localStorage.setItem('token', token)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-sidebar">
        <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
            <Navigate to="/app" /> : 
            <Login onLogin={handleLogin} />
          } 
        />
        <Route 
          path="/register" 
          element={
            isAuthenticated ? 
            <Navigate to="/app" /> : 
            <Register />
          } 
        />
        
        {/* Protected Routes */}
        <Route 
          path="/app" 
          element={
            isAuthenticated ? 
            <DataAnalysisAssistant onLogout={handleLogout} /> : 
            <Navigate to="/login" />
          } 
        />
        
        {/* Default redirect for unknown paths */}
        <Route 
          path="*" 
          element={<Navigate to="/" />} 
        />
      </Routes>
    </Router>
  )
}

export default App
