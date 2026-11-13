import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Clean params helper
function cleanParams(params = {}) {
  const cleaned = {};
  Object.keys(params).forEach((key) => {
    const val = params[key];
    if (val !== undefined && val !== null && val !== '') {
      cleaned[key] = val;
    }
  });
  return cleaned;
}

export const apiClient = {
  // Health
  getHealth: () => api.get('/health'),
  getReadiness: () => api.get('/health/ready'),

  // Master Data
  getBrands: (activeOnly = false) =>
    api.get('/brands', { params: { active_only: activeOnly } }),
  getRegions: (activeOnly = false) =>
    api.get('/regions', { params: { active_only: activeOnly } }),

  // Dashboard Analytics
  getDashboardSummary: (params = {}) =>
    api.get('/dashboard/summary', { params: cleanParams(params) }),
  getSalesTrend: (params = {}) =>
    api.get('/dashboard/sales-trend', { params: cleanParams(params) }),
  getBrandPerformance: (params = {}) =>
    api.get('/dashboard/brand-performance', { params: cleanParams(params) }),
  getRegionPerformance: (params = {}) =>
    api.get('/dashboard/region-performance', { params: cleanParams(params) }),

  // Sales List
  getSales: (params = {}) =>
    api.get('/sales', { params: cleanParams(params) }),

  // Imports
  uploadCSV: (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/imports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
  },
  getImports: (params = {}) =>
    api.get('/imports', { params: cleanParams(params) }),
  getImportDetail: (importId) =>
    api.get(`/imports/${importId}`),

  // Alerts
  getAlerts: (params = {}) =>
    api.get('/alerts', { params: cleanParams(params) }),
  getAlertDetail: (alertId) =>
    api.get(`/alerts/${alertId}`),
  updateAlertStatus: (alertId, status) =>
    api.patch(`/alerts/${alertId}`, { status }),
  getAlertSummary: () =>
    api.get('/alerts/summary'),
  runDetection: (month) =>
    api.post('/alerts/run-detection', { month }),
};

export default apiClient;
