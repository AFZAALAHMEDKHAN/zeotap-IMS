import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import IncidentDetail from './pages/IncidentDetail'
import SignalFire from './pages/SignalFire'

export default function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/"               element={<Dashboard />} />
          <Route path="/incident/:id"   element={<IncidentDetail />} />
          <Route path="/signals"        element={<SignalFire />} />
        </Routes>
      </main>
    </div>
  )
}
