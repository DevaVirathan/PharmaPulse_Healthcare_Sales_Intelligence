import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart2,
  Bell,
  UploadCloud,
  History,
  Activity,
  Sparkles,
} from 'lucide-react';

export function Sidebar({ mobileOpen, onCloseMobile }) {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/analytics', label: 'Sales Analytics', icon: BarChart2 },
    { to: '/alerts', label: 'Anomaly Alerts', icon: Bell },
    { to: '/upload', label: 'Upload Data', icon: UploadCloud },
    { to: '/imports', label: 'Import History', icon: History },
  ];

  return (
    <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-badge">
          <Activity size={24} />
        </div>
        <div>
          <div className="logo-title">PharmaPulse</div>
          <div className="logo-subtitle">Sales Intelligence</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              end={item.to === '/'}
            >
              <Icon size={19} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Modern promotional / POC info card like in reference design */}
      <div className="sidebar-card-promo">
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #a855f7, #ec4899)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Sparkles size={16} />
        </div>
        <p style={{ fontWeight: 800, fontSize: '0.875rem', color: '#1e293b' }}>
          PharmaPulse Pro
        </p>
        <p style={{ fontSize: '0.75rem', color: '#64748b', lineHeight: 1.3 }}>
          Commercial BI & rule-based anomaly detection engine
        </p>
        <div
          style={{
            marginTop: '0.25rem',
            padding: '0.3125rem 0.875rem',
            borderRadius: '9999px',
            backgroundColor: '#7c3aed',
            color: '#ffffff',
            fontSize: '0.75rem',
            fontWeight: 700,
          }}
        >
          POC Active
        </div>
      </div>

    </aside>
  );
}

export default Sidebar;
