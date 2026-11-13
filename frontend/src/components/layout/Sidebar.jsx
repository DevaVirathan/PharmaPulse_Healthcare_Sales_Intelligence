import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart2,
  Bell,
  UploadCloud,
  History,
  Activity,
} from 'lucide-react';

export function Sidebar({ mobileOpen, onCloseMobile }) {
  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/analytics', label: 'Sales Analytics', icon: BarChart2 },
    { to: '/alerts', label: 'Alerts', icon: Bell },
    { to: '/upload', label: 'Upload Data', icon: UploadCloud },
    { to: '/imports', label: 'Import History', icon: History },
  ];

  return (
    <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-badge">
          <Activity size={22} />
        </div>
        <div>
          <div className="logo-title">PharmaPulse</div>
          <div className="logo-subtitle">Sales Intelligence POC</div>
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
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <p style={{ fontWeight: 600, color: '#94a3b8', marginBottom: '0.25rem' }}>
          PharmaPulse v0.1.0
        </p>
        {/* <p>PostgreSQL • FastAPI • React</p> */}
      </div>
    </aside>
  );
}

export default Sidebar;
