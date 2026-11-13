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
  TrendingUp,
  TrendingDown,
  Download,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import apiClient from '../services/api';
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
import { formatINR, formatINRCompact, formatNumber, formatPercent, formatDate, formatMonthYear, formatDateTime } from '../utils/formatters';

export function OverviewPage() {
  const navigate = useNavigate();

  // Date range state
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState('2026-10-31');
  const [activePreset, setActivePreset] = useState('YTD');

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
    const updatedAlertRes = await apiClient.getAlertDetail(alertId);
    setSelectedAlert(updatedAlertRes.data);
    const alertsRes = await apiClient.getAlerts({ severity: 'HIGH', page: 1, page_size: 5 });
    setRecentAlerts(alertsRes.data.items || []);
  };

  const setPreset = (preset) => {
    setActivePreset(preset);
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
      {/* Modern Filter & Controls Bar */}
      <div className="filter-bar-modern">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
          {/* Date Picker Pill Group */}
          <div className="date-pill-input">
            <Calendar size={15} color="#64748b" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setActivePreset('CUSTOM');
              }}
              title="Start Date"
            />
            <span style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600 }}>TO</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setActivePreset('CUSTOM');
              }}
              title="End Date"
            />
          </div>

          {/* Quick preset tabs inspired by modern UI */}
          <div className="pill-group">
            <button
              className={`pill-tab ${activePreset === 'YTD' ? 'active' : ''}`}
              onClick={() => setPreset('YTD')}
            >
              2026 YTD
            </button>
            <button
              className={`pill-tab ${activePreset === 'Q3' ? 'active' : ''}`}
              onClick={() => setPreset('Q3')}
            >
              Q3 2026
            </button>
            <button
              className={`pill-tab ${activePreset === 'L3M' ? 'active' : ''}`}
              onClick={() => setPreset('L3M')}
            >
              Last 3M
            </button>
            <button
              className={`pill-tab ${activePreset === 'ALL' ? 'active' : ''}`}
              onClick={() => setPreset('ALL')}
            >
              All 12M
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {lastImportTime && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>
              <Clock size={13} color="#94a3b8" />
              <span>Imported: <strong>{formatDateTime(lastImportTime)}</strong></span>
            </div>
          )}
          <Button
            variant="outline"
            size="sm"
            icon={RefreshCw}
            onClick={fetchOverviewData}
          >
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <Spinner label="Loading executive dashboard..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchOverviewData} />
      ) : (
        <>
          {/* "Today's Sales" / Sales Summary Container with 4 Vibrant Gradient Stat Cards */}
          <div className="sales-summary-container">
            <div className="sales-summary-header">
              <div>
                <h2 className="sales-summary-title">Sales Performance</h2>
                <p className="sales-summary-subtitle">
                  Aggregated commercial metrics for {formatDate(startDate)} – {formatDate(endDate)}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                icon={Download}
                onClick={() => navigate('/analytics')}
              >
                Detailed Analytics
              </Button>
            </div>

            <div className="stat-cards-grid">
              {/* Card 1: Purple-Pink Gradient (Total Revenue) */}
              <div className="stat-card-gradient stat-card-purple">
                <div className="stat-card-top">
                  <div>
                    <div className="stat-card-value" title={formatINR(summary?.total_revenue)}>
                      {formatINRCompact(summary?.total_revenue)}
                    </div>
                    <div className="stat-card-sub-value" title="Exact Total Sales Revenue">
                      {formatINR(summary?.total_revenue)}
                    </div>
                  </div>
                  <div className="stat-card-icon-pill">
                    <IndianRupee size={22} />
                  </div>
                </div>
                <div className="stat-card-bottom">
                  <div className="stat-card-label">Total Sales Revenue</div>
                  <div className="stat-card-subtext">
                    {summary?.revenue_change_pct !== null && summary?.revenue_change_pct !== undefined ? (
                      summary.revenue_change_pct >= 0 ? (
                        <>
                          <TrendingUp size={14} />
                          <span>{formatPercent(summary.revenue_change_pct)} vs prior period</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown size={14} />
                          <span>{formatPercent(summary.revenue_change_pct)} vs prior period</span>
                        </>
                      )
                    ) : (
                      <span>Baseline comparison</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Card 2: Cyan-Blue Gradient (Total Units) */}
              <div className="stat-card-gradient stat-card-cyan">
                <div className="stat-card-top">
                  <div className="stat-card-value">
                    {formatNumber(summary?.total_units)}
                  </div>
                  <div className="stat-card-icon-pill">
                    <Package size={22} />
                  </div>
                </div>
                <div className="stat-card-bottom">
                  <div className="stat-card-label">Total Volume (Units)</div>
                  <div className="stat-card-subtext">
                    <span>Aggregated units across all brands</span>
                  </div>
                </div>
              </div>

              {/* Card 3: Orange-Amber Gradient (Active Brands) */}
              <div className="stat-card-gradient stat-card-orange">
                <div className="stat-card-top">
                  <div className="stat-card-value">
                    {summary?.brand_count || 0}
                  </div>
                  <div className="stat-card-icon-pill">
                    <Layers size={22} />
                  </div>
                </div>
                <div className="stat-card-bottom">
                  <div className="stat-card-label">Active Therapeutic Brands</div>
                  <div className="stat-card-subtext">
                    <span>Cardio, Neuro, Metabolic, Oncology, etc.</span>
                  </div>
                </div>
              </div>

              {/* Card 4: Emerald-Teal Gradient (Active Regions) */}
              <div className="stat-card-gradient stat-card-emerald">
                <div className="stat-card-top">
                  <div className="stat-card-value">
                    {summary?.region_count || 0}
                  </div>
                  <div className="stat-card-icon-pill">
                    <MapPin size={22} />
                  </div>
                </div>
                <div className="stat-card-bottom">
                  <div className="stat-card-label">Commercial Territories</div>
                  <div className="stat-card-subtext">
                    <span>Chennai, Coimbatore, Madurai, Trichy</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Monthly Trend Area Chart (Smooth Curved Multi-Stop Splines) */}
          <div style={{ marginBottom: '2rem' }}>
            <Card
              title="Sales & Volume Trajectory"
              subtitle={`Monthly aggregated revenue curve & unit volume from ${formatDate(startDate)} to ${formatDate(endDate)}`}
            >
              <TrendLineChart data={trend} />
            </Card>
          </div>

          {/* Brand & Regional Performance Bar Charts Side-by-Side */}
          <div className="charts-grid">
            <Card
              title="Brand Performance"
              subtitle="Revenue breakdown by pharmaceutical brand"
            >
              <BrandBarChart data={brandPerf} />
            </Card>

            <Card
              title="Territory Performance"
              subtitle="Revenue breakdown across geographical sales regions"
            >
              <RegionBarChart data={regionPerf} />
            </Card>
          </div>

          {/* Recent High-Priority Alerts (Styled like Top Products in reference design) */}
          <Card
            title="High-Priority Anomaly Signals"
            subtitle="Flagged month-over-month variances requiring commercial investigation"
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
                icon={Sparkles}
                title="No high-priority alerts"
                description="No critical decline anomalies currently active in the selected window."
              />
            ) : (
              <Table
                className="table-container-fit"
                headers={[
                  { label: 'Brand', width: '18%' },
                  { label: 'Region', width: '12%' },
                  { label: 'Period', width: '10%' },
                  { label: 'Baseline', align: 'right', width: '13%' },
                  { label: 'Current', align: 'right', width: '13%' },
                  { label: 'Variance', align: 'right', width: '10%' },
                  { label: 'Severity', width: '10%' },
                  { label: 'Status', width: '10%' },
                  { label: 'Action', align: 'center', width: '4%' },
                ]}
              >
                {recentAlerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div
                          style={{
                            width: 26,
                            height: 26,
                            borderRadius: '50%',
                            backgroundColor: '#f5f3ff',
                            color: '#7c3aed',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 700,
                            fontSize: '0.75rem',
                            flexShrink: 0,
                          }}
                        >
                          {alert.brand_name.substring(0, 1)}
                        </div>
                        <strong>{alert.brand_name}</strong>
                      </div>
                    </td>
                    <td>{alert.region_name}</td>
                    <td style={{ fontSize: '0.8125rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {formatMonthYear(alert.period_end)}
                    </td>
                    <td className="text-right" style={{ color: '#64748b' }}>
                      {formatINR(alert.previous_value)}
                    </td>
                    <td className="text-right" style={{ fontWeight: 700 }}>
                      {formatINR(alert.current_value)}
                    </td>
                    <td
                      className="text-right"
                      style={{
                        fontWeight: 700,
                        color: alert.change_pct < 0 ? '#dc2626' : '#059669',
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

      {/* Alert Inspection & Transition Modal */}
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
