import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IndianRupee,
  Package,
  Layers,
  MapPin,
  Calendar,
  Clock,
  ArrowRight,
  RefreshCw,
  Bell,
} from 'lucide-react';
import apiClient from '../services/api';
import MetricCard from '../components/common/MetricCard';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import Table from '../components/common/Table';
import { SeverityBadge, StatusBadge } from '../components/common/Badge';
import TrendLineChart from '../components/dashboard/TrendLineChart';
import BrandBarChart from '../components/dashboard/BrandBarChart';
import RegionBarChart from '../components/dashboard/RegionBarChart';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import { formatINR, formatNumber, formatPercent, formatDate, formatDateTime } from '../utils/formatters';

export function OverviewPage() {
  const navigate = useNavigate();

  // Date range state (defaulting to whole year 2026)
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState('2026-10-31');

  // Data states
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [brandPerf, setBrandPerf] = useState([]);
  const [regionPerf, setRegionPerf] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [lastImportTime, setLastImportTime] = useState(null);

  // Status
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selected alert for modal
  const [selectedAlert, setSelectedAlert] = useState(null);

  const fetchOverviewData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      const [sumRes, trendRes, brandRes, regRes, alertsRes, importsRes] =
        await Promise.all([
          apiClient.getDashboardSummary(params),
          apiClient.getSalesTrend(params),
          apiClient.getBrandPerformance(params),
          apiClient.getRegionPerformance(params),
          apiClient.getAlerts({ severity: 'HIGH', page: 1, page_size: 5 }),
          apiClient.getImports({ page: 1, page_size: 1 }),
        ]);

      setSummary(sumRes.data);
      setTrend(trendRes.data.items || []);
      setBrandPerf(brandRes.data.items || []);
      setRegionPerf(regRes.data.items || []);
      setRecentAlerts(alertsRes.data.items || []);

      if (importsRes.data.items && importsRes.data.items.length > 0) {
        setLastImportTime(importsRes.data.items[0].imported_at);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard overview');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchOverviewData();
  }, [fetchOverviewData]);

  const handleAlertStatusUpdated = async (alertId, newStatus) => {
    await apiClient.updateAlertStatus(alertId, newStatus);
    // Refresh alerts and modal item
    const updatedAlertRes = await apiClient.getAlertDetail(alertId);
    setSelectedAlert(updatedAlertRes.data);
    const alertsRes = await apiClient.getAlerts({ severity: 'HIGH', page: 1, page_size: 5 });
    setRecentAlerts(alertsRes.data.items || []);
  };

  const setPreset = (preset) => {
    switch (preset) {
      case 'YTD':
        setStartDate('2026-01-01');
        setEndDate('2026-10-31');
        break;
      case 'Q3':
        setStartDate('2026-07-01');
        setEndDate('2026-09-30');
        break;
      case 'L3M':
        setStartDate('2026-08-01');
        setEndDate('2026-10-31');
        break;
      case 'ALL':
        setStartDate('2025-11-01');
        setEndDate('2026-10-31');
        break;
      default:
        break;
    }
  };

  return (
    <div>
      {/* Top Controls: Filter bar + Last import info */}
      <div className="filter-bar" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
            <Calendar size={16} />
            <span>Date Window:</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <input
              type="date"
              className="form-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <span style={{ color: 'var(--color-text-muted)' }}>to</span>
            <input
              type="date"
              className="form-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          {/* Quick presets */}
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            <Button size="sm" variant="outline" onClick={() => setPreset('YTD')}>
              2026 YTD
            </Button>
            <Button size="sm" variant="outline" onClick={() => setPreset('Q3')}>
              Q3 2026
            </Button>
            <Button size="sm" variant="outline" onClick={() => setPreset('L3M')}>
              Last 3M
            </Button>
            <Button size="sm" variant="outline" onClick={() => setPreset('ALL')}>
              All 12M
            </Button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {lastImportTime && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              <Clock size={14} />
              <span>Last Data Import: <strong>{formatDateTime(lastImportTime)}</strong></span>
            </div>
          )}
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchOverviewData}>
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <Spinner label="Calculating aggregate metrics..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchOverviewData} />
      ) : (
        <>
          {/* KPI Summary Cards */}
          <div className="kpi-grid">
            <MetricCard
              title="Total Sales Revenue"
              value={formatINR(summary?.total_revenue)}
              change={summary?.revenue_change_pct}
              changeLabel="vs previous period"
              icon={IndianRupee}
            />
            <MetricCard
              title="Total Units Sold"
              value={formatNumber(summary?.total_units)}
              icon={Package}
            />
            <MetricCard
              title="Active Brands"
              value={summary?.brand_count || 0}
              icon={Layers}
            />
            <MetricCard
              title="Active Regions"
              value={summary?.region_count || 0}
              icon={MapPin}
            />
          </div>

          {/* Monthly Trend Chart */}
          <div style={{ marginBottom: '1.75rem' }}>
            <Card
              title="Monthly Sales & Units Trend"
              subtitle={`Aggregated sales from ${formatDate(startDate)} to ${formatDate(endDate)}`}
            >
              <TrendLineChart data={trend} />
            </Card>
          </div>

          {/* Brand & Region Comparisons */}
          <div className="charts-grid">
            <Card
              title="Revenue by Brand"
              subtitle="Brand distribution in selected window"
            >
              <BrandBarChart data={brandPerf} />
            </Card>

            <Card
              title="Revenue by Region"
              subtitle="Regional distribution in selected window"
            >
              <RegionBarChart data={regionPerf} />
            </Card>
          </div>

          {/* Recent High-Priority Alerts */}
          <Card
            title="Recent High-Priority Anomaly Alerts"
            subtitle="Signals requiring management review (High Severity)"
            action={
              <Button
                variant="outline"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate('/alerts')}
              >
                View All Alerts
              </Button>
            }
          >
            {recentAlerts.length === 0 ? (
              <EmptyState
                icon={Bell}
                title="No high-priority alerts"
                description="No critical decline anomalies currently active."
              />
            ) : (
              <Table
                headers={[
                  { label: 'Brand' },
                  { label: 'Region' },
                  { label: 'Period' },
                  { label: 'Baseline', align: 'right' },
                  { label: 'Current', align: 'right' },
                  { label: 'Change', align: 'right' },
                  { label: 'Severity' },
                  { label: 'Status' },
                  { label: 'Action', align: 'center' },
                ]}
              >
                {recentAlerts.map((alert) => (
                  <tr key={alert.id}>
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
                        variant="secondary"
                        onClick={() => setSelectedAlert(alert)}
                      >
                        Inspect
                      </Button>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>
        </>
      )}

      {/* Alert Inspection Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          isOpen={Boolean(selectedAlert)}
          onClose={() => setSelectedAlert(null)}
          onStatusUpdated={handleAlertStatusUpdated}
        />
      )}
    </div>
  );
}

export default OverviewPage;
