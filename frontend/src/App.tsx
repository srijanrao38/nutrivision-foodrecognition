// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import FoodDetection from './pages/FoodDetection';
import MedicalUpload from './pages/MedicalUpload';
import WeeklyPlanner from './pages/WeeklyPlanner';
import AIChat from './pages/AIChat';
import Profile from './pages/Profile';

// Route Guard Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = !!localStorage.getItem('token');
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/food-detection" element={
              <ProtectedRoute>
                <FoodDetection />
              </ProtectedRoute>
            } />

            <Route path="/medical-upload" element={
              <ProtectedRoute>
                <MedicalUpload />
              </ProtectedRoute>
            } />

            <Route path="/weekly-planner" element={
              <ProtectedRoute>
                <WeeklyPlanner />
              </ProtectedRoute>
            } />

            <Route path="/chat" element={
              <ProtectedRoute>
                <AIChat />
              </ProtectedRoute>
            } />

            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />

            {/* Catch-all redirects */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
