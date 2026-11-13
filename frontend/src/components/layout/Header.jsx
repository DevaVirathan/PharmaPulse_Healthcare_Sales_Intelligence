import React, { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import apiClient from '../../services/api';

export function Header({ title, onToggleSidebar }) {
  const [healthy, setHealthy] = useState(null);

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
            <Menu size={20} />
          </button>
        )}
        <h1 className="page-title">{title}</h1>
      </div>

      <div className="header-right">
        <div className="demo-pill">POC Demo (Synthetic Data)</div>
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
            ? 'API Online'
            : healthy === false
            ? 'API Offline'
            : 'Connecting...'}
        </div>
      </div>
    </header>
  );
}

export default Header;
