import React, { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  Play,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  AlertCircle,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import apiClient from '../services/api';
import { useMasterData } from '../hooks/useMasterData';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Table from '../components/common/Table';
import Spinner from '../components/common/Spinner';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { SeverityBadge, StatusBadge } from '../components/common/Badge';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import RunDetectionModal from '../components/alerts/RunDetectionModal';
import { formatINR, formatPercent, formatDate } from '../utils/formatters';

export function AlertsPage() {
  const { brands, regions } = useMasterData();

  // Summary counts
  const [summary, setSummary] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Alerts data
  const [alerts, setAlerts] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [runDetectionOpen, setRunDetectionOpen] = useState(false);

  const fetchAlertsData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        brand_id: selectedBrand ? Number(selectedBrand) : undefined,
        region_id: selectedRegion ? Number(selectedRegion) : undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        page_size: pageSize,
      };

      const [alertsRes, summaryRes] = await Promise.all([
        apiClient.getAlerts(params),
        apiClient.getAlertSummary(),
      ]);

      setAlerts({
        items: alertsRes.data.items || [],
        total: alertsRes.data.total || 0,
      });
      setSummary(summaryRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, severityFilter, selectedBrand, selectedRegion, startDate, endDate, page, pageSize]);

  useEffect(() => {
    fetchAlertsData();
  }, [fetchAlertsData]);

  const handleStatusUpdated = async (alertId, newStatus) => {
    await apiClient.updateAlertStatus(alertId, newStatus);
    // Refresh modal item and list
    const detailRes = await apiClient.getAlertDetail(alertId);
    setSelectedAlert(detailRes.data);
    fetchAlertsData();
  };

  const handleDetectionCompleted = () => {
    fetchAlertsData();
  };

  const clearFilters = () => {
    setStatusFilter('');
    setSeverityFilter('');
    setSelectedBrand('');
    setSelectedRegion('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  const totalPages = Math.ceil((alerts.total || 0) / pageSize) || 1;

  return (
    <div>
      {/* Top Summary KPI Cards */}
      <div className="kpi-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="kpi-card" style={{ borderLeft: '4px solid #7c3aed' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="kpi-title">Total Alerts</span>
            <div style={{ width: 34, height: 34, borderRadius: '50%', backgroundColor: '#f5f3ff', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bell size={18} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value" style={{ color: '#4c1d95' }}>{summary?.total ?? 0}</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Detected anomalies
          </span>
        </div>

        <div className="kpi-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="kpi-title">High Severity</span>
            <div style={{ width: 34, height: 34, borderRadius: '50%', backgroundColor: '#fef2f2', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value" style={{ color: '#dc2626' }}>
              {summary?.by_severity?.HIGH ?? 0}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Decline anomalies (&ge; 20%)
          </span>
        </div>

        <div className="kpi-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="kpi-title">Medium Severity</span>
            <div style={{ width: 34, height: 34, borderRadius: '50%', backgroundColor: '#fffbeb', color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertCircle size={18} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value" style={{ color: '#d97706' }}>
              {summary?.by_severity?.MEDIUM ?? 0}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Growth anomalies (&ge; 30%)
          </span>
        </div>

        <div className="kpi-card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="kpi-title">Open Queue</span>
            <div style={{ width: 34, height: 34, borderRadius: '50%', backgroundColor: '#f0f9ff', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Clock size={18} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value" style={{ color: '#0284c7' }}>
              {summary?.by_status?.OPEN ?? 0}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Pending investigation
          </span>
        </div>
      </div>

      {/* Action / Trigger Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          Rule-based detection surfaces unusual month-over-month sales shifts. Alerts provide a signal to investigate, not a diagnosis.
        </p>
        <Button
          variant="primary"
          icon={Play}
          onClick={() => setRunDetectionOpen(true)}
        >
          Run Anomaly Detection
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="form-group">
          <label className="form-label">Status</label>
          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="DISMISSED">DISMISSED</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Severity</label>
          <select
            className="form-select"
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Severities</option>
            <option value="HIGH">HIGH (Decline &ge; 20%)</option>
            <option value="MEDIUM">MEDIUM (Growth &ge; 30%)</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Brand</label>
          <select
            className="form-select"
            value={selectedBrand}
            onChange={(e) => {
              setSelectedBrand(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Brands</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Region</label>
          <select
            className="form-select"
            value={selectedRegion}
            onChange={(e) => {
              setSelectedRegion(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Regions</option>
            {regions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">From Date</label>
          <input
            type="date"
            className="form-input"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="form-group">
          <label className="form-label">To Date</label>
          <input
            type="date"
            className="form-input"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          {(statusFilter || severityFilter || selectedBrand || selectedRegion || startDate || endDate) && (
            <Button variant="outline" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchAlertsData}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Alerts Table Card */}
      <Card
        title="Detected Sales Anomalies"
        subtitle={`Showing ${alerts.items.length} of ${alerts.total} total alerts`}
      >
        {loading ? (
          <Spinner label="Loading alerts..." />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchAlertsData} />
        ) : alerts.items.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="No alerts match the criteria"
            description="Run anomaly detection or adjust your filter selection to review alerts."
            actionLabel="Run Anomaly Detection"
            onAction={() => setRunDetectionOpen(true)}
          />
        ) : (
          <>
            <Table
              headers={[
                { label: 'ID', width: '60px' },
                { label: 'Brand' },
                { label: 'Region' },
                { label: 'Period' },
                { label: 'Prior Baseline', align: 'right' },
                { label: 'Current Value', align: 'right' },
                { label: 'Change', align: 'right' },
                { label: 'Severity' },
                { label: 'Status' },
                { label: 'Actions', align: 'center' },
              ]}
            >
              {alerts.items.map((alert) => (
                <tr key={alert.id}>
                  <td>{alert.id}</td>
                  <td><strong>{alert.brand_name}</strong></td>
                  <td>{alert.region_name}</td>
                  <td style={{ fontSize: '0.8125rem' }}>
                    {formatDate(alert.period_start)} – {formatDate(alert.period_end)}
                  </td>
                  <td className="text-right">{formatINR(alert.previous_value)}</td>
                  <td className="text-right">{formatINR(alert.current_value)}</td>
                  <td
                    className="text-right"
                    style={{
                      fontWeight: 600,
                      color: alert.change_pct < 0 ? '#991b1b' : '#065f46',
                    }}
                  >
                    {formatPercent(alert.change_pct)}
                  </td>
                  <td>
                    <SeverityBadge severity={alert.severity} />
                  </td>
                  <td>
                    <StatusBadge status={alert.status} />
                  </td>
                  <td className="text-center">
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => setSelectedAlert(alert)}
                    >
                      Review
                    </Button>
                  </td>
                </tr>
              ))}
            </Table>

            {/* Pagination Controls */}
            <div className="pagination-row">
              <div>
                Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({alerts.total} total alerts)
              </div>
              <div className="pagination-controls">
                <Button
                  variant="outline"
                  size="sm"
                  icon={ChevronLeft}
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page <= 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  disabled={page >= totalPages}
                >
                  Next
                  <ChevronRight size={14} />
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Alert Detail & Status Transition Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          isOpen={Boolean(selectedAlert)}
          onClose={() => setSelectedAlert(null)}
          onStatusUpdated={handleStatusUpdated}
        />
      )}

      {/* Run Detection Modal */}
      <RunDetectionModal
        isOpen={runDetectionOpen}
        onClose={() => setRunDetectionOpen(false)}
        onDetectionCompleted={handleDetectionCompleted}
      />
    </div>
  );
}

export default AlertsPage;
