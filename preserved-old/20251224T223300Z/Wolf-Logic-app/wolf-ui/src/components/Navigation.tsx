import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

const API_BASE = 'http://localhost:8084';

const Navigation: React.FC = () => {
  const location = useLocation();
  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/health`, { method: 'GET' });
        setBackendOnline(response.ok);
      } catch {
        setBackendOnline(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 3000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/dashboard', label: 'Charts' },
    { path: '/control', label: 'Control' },
    { path: '/memory', label: 'Memory' },
    { path: '/graph', label: 'Graph' },
    { path: '/settings', label: 'Settings' },
  ];

  return (
    <nav className="main-navigation">
      <div className="nav-brand">
        <img src="/logo.png" alt="Wolf Logic AI" className="nav-logo-img" />
        <div className="nav-brand-text">
          <span className="nav-title">Wolf Logic AI</span>
          <span className="nav-subtitle">Because the wolf never forgets</span>
        </div>
      </div>

      <div className="nav-links">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
          >
            {item.label}
          </Link>
        ))}
      </div>

      <div className={`nav-status backend-status ${backendOnline ? 'online' : 'offline'}`}>
        <span className={`status-indicator backend-glow ${backendOnline ? 'online' : 'offline'}`}></span>
        <span className="status-text">{backendOnline ? 'Backend Online' : 'Backend Offline'}</span>
      </div>
    </nav>
  );
};

export default Navigation;
