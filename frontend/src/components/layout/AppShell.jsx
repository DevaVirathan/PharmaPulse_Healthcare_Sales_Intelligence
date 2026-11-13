import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/':
        return 'Overview Dashboard';
      case '/analytics':
        return 'Sales Analytics Workspace';
      case '/alerts':
        return 'Anomaly Alerts';
      case '/upload':
        return 'Upload Sales Data';
      case '/imports':
        return 'Import History';
      default:
        return 'PharmaPulse';
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="main-content">
        <Header
          title={getPageTitle(location.pathname)}
          onToggleSidebar={() => setMobileOpen(!mobileOpen)}
        />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppShell;
