import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import OverviewPage from '../pages/OverviewPage';
import SalesAnalyticsPage from '../pages/SalesAnalyticsPage';
import UploadDataPage from '../pages/UploadDataPage';
import AlertsPage from '../pages/AlertsPage';
import ImportHistoryPage from '../pages/ImportHistoryPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <OverviewPage />,
      },
      {
        path: 'analytics',
        element: <SalesAnalyticsPage />,
      },
      {
        path: 'alerts',
        element: <AlertsPage />,
      },
      {
        path: 'upload',
        element: <UploadDataPage />,
      },
      {
        path: 'imports',
        element: <ImportHistoryPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);

export default router;
