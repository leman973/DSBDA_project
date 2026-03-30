import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Index from "./pages/Index";
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
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, hsl(270, 30%, 98%), hsl(280, 40%, 96%))',
      }}>
        <div style={{
          width: 40,
          height: 40,
          border: '3px solid hsl(270, 20%, 80%)',
          borderTopColor: 'hsl(280, 80%, 60%)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
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
        
        {/* Default redirect */}
        <Route 
          path="/" 
          element={<Navigate to={isAuthenticated ? "/app" : "/login"} />} 
        />
      </Routes>
    </Router>
  )
}

export default App
