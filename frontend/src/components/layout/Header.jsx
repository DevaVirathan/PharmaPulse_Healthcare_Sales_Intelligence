import React, { useState, useEffect } from 'react';
import { Menu, Search, Bell, ChevronDown } from 'lucide-react';
import apiClient from '../../services/api';

export function Header({ title, onToggleSidebar }) {
  const [healthy, setHealthy] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    let mounted = true;
    apiClient
      .getHealth()
      .then(() => {
        if (mounted) setHealthy(true);
      })
      .catch(() => {
        if (mounted) setHealthy(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="top-header">
      <div className="header-left">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-text-main)',
              display: 'flex',
            }}
            aria-label="Toggle Navigation"
          >
            <Menu size={22} />
          </button>
        )}
        <h1 className="page-title">{title}</h1>
      </div>

      {/* Center Search Bar inspired by the reference design */}
      <div className="header-search">
        <Search size={16} color="#94a3b8" />
        <input
          type="text"
          placeholder="Search brands, regions, alerts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="header-right">
        {/* Backend health status pill */}
        <div
          className="health-pill"
          style={
            healthy === false
              ? { backgroundColor: 'var(--color-danger-light)', color: '#991b1b' }
              : {}
          }
        >
          <span
            className="health-dot"
            style={healthy === false ? { backgroundColor: 'var(--color-danger)' } : {}}
          />
          {healthy === true
            ? 'Online'
            : healthy === false
              ? 'Offline'
              : 'Connecting...'}
        </div>

        {/* Notification Icon Button with Pink Badge */}
        <button className="icon-button" aria-label="Notifications">
          <Bell size={18} />
          <span className="icon-button-badge" />
        </button>

        {/* User Profile Avatar Widget like in reference image */}
        <div className="user-profile-widget">
          <div className="user-avatar">JB</div>
          <div className="user-info">
            <span className="user-name">Jerome Bell</span>
            <span className="user-role">Commercial Lead</span>
          </div>
          <ChevronDown size={14} color="#94a3b8" style={{ marginLeft: '0.25rem' }} />
        </div>
      </div>
    </header>
  );
}

export default Header;
