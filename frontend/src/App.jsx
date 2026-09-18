import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import AppLayout from './layouts/AppLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import CameraRegistryPage from './pages/CameraRegistryPage.jsx'
import CameraDetailPage from './pages/CameraDetailPage.jsx'
import CameraMapPage from './pages/CameraMapPage.jsx'
import WatchlistPage from './pages/WatchlistPage.jsx'
import AlertsPage from './pages/AlertsPage.jsx'
import EntitySearchPage from './pages/EntitySearchPage.jsx'
import AuditPage from './pages/AuditPage.jsx'

function ProtectedRoute({ children, adminOnly = false }) {
  const { token, isAdmin } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (adminOnly && !isAdmin) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/cameras" element={<CameraRegistryPage />} />
          <Route path="/cameras/:cameraId" element={<CameraDetailPage />} />
          <Route path="/map" element={<CameraMapPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/search" element={<EntitySearchPage />} />
          <Route
            path="/audit"
            element={
              <ProtectedRoute adminOnly>
                <AuditPage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
