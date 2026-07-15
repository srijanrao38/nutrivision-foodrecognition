// src/components/Navbar.tsx
import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Activity, LayoutDashboard, Camera, FileText, Calendar, MessageSquare, User, LogOut } from 'lucide-react';
import api from '../api';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = !!localStorage.getItem('token');

  const handleLogout = async () => {
    try {
      await api.post('/api/auth/logout/');
    } catch (e) {
      console.error(e);
    }
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  };

  if (!isAuthenticated) return null;

  const links = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/food-detection', label: 'Meal Detection', icon: Camera },
    { to: '/medical-upload', label: 'Medical Reports', icon: FileText },
    { to: '/weekly-planner', label: 'Meal Planner', icon: Calendar },
    { to: '/chat', label: 'AI Assistant', icon: MessageSquare },
    { to: '/profile', label: 'Profile', icon: User },
  ];

  return (
    <nav className="bg-slate-900 text-slate-100 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
            <Activity className="h-8 w-8 text-emerald-400 animate-pulse" />
            <span className="font-bold text-xl tracking-tight text-white">NutriVision <span className="text-emerald-400">AI</span></span>
          </div>

          <div className="hidden md:flex space-x-1 lg:space-x-4">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-lg'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {link.label}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center">
            <span className="hidden lg:inline-block text-sm text-slate-400 mr-4 font-medium">
              Hello, {localStorage.getItem('username') || 'User'}
            </span>
            <button
              onClick={handleLogout}
              className="flex items-center bg-slate-800 hover:bg-red-700 text-slate-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-all duration-200"
            >
              <LogOut className="h-4 w-4 md:mr-2" />
              <span className="hidden md:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
