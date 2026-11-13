import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Download,
} from 'lucide-react';
import apiClient from '../services/api';
import { useMasterData } from '../hooks/useMasterData';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import Table from '../components/common/Table';
import TrendLineChart from '../components/dashboard/TrendLineChart';
import { formatINR, formatNumber, formatPercent, formatDate } from '../utils/formatters';

export function SalesAnalyticsPage() {
  const { brands, regions } = useMasterData();

  // Filters
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState('2026-10-31');
  const [activePreset, setActivePreset] = useState('YTD');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');

  // Pagination for raw sales table
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Data states
  const [trend, setTrend] = useState([]);
  const [brandPerf, setBrandPerf] = useState([]);
  const [regionPerf, setRegionPerf] = useState([]);
  const [salesData, setSalesData] = useState({ items: [], total: 0 });

  // Status
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        brand_id: selectedBrand ? Number(selectedBrand) : undefined,
        region_id: selectedRegion ? Number(selectedRegion) : undefined,
      };

      const [trendRes, brandRes, regRes, salesRes] = await Promise.all([
        apiClient.getSalesTrend(params),
        apiClient.getBrandPerformance(params),
        apiClient.getRegionPerformance(params),
        apiClient.getSales({
          ...params,
          page,
          page_size: pageSize,
        }),
      ]);

      setTrend(trendRes.data.items || []);
      setBrandPerf(brandRes.data.items || []);
      setRegionPerf(regRes.data.items || []);
      setSalesData({
        items: salesRes.data.items || [],
        total: salesRes.data.total || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load sales analytics');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, selectedBrand, selectedRegion, page, pageSize]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const setPreset = (preset) => {
    setActivePreset(preset);
    setPage(1);
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

  const clearAllFilters = () => {
    setStartDate('2026-01-01');
    setEndDate('2026-10-31');
    setActivePreset('YTD');
    setSelectedBrand('');
    setSelectedRegion('');
    setPage(1);
  };

  const totalPages = Math.ceil((salesData.total || 0) / pageSize) || 1;

  // Active filter label helpers
  const brandObj = brands.find((b) => String(b.id) === String(selectedBrand));
  const regionObj = regions.find((r) => String(r.id) === String(selectedRegion));

  return (
    <div>
      {/* Filter Bar with Presets and Active Chips */}
      <div className="filter-bar">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', alignItems: 'flex-end', width: '100%' }}>
          {/* Quick Period Presets */}
          <div className="form-group">
            <label className="form-label">Period Preset</label>
            <div className="pill-group">
              <button
                type="button"
                className={`pill-tab ${activePreset === 'YTD' ? 'active' : ''}`}
                onClick={() => setPreset('YTD')}
              >
                2026 YTD
              </button>
              <button
                type="button"
                className={`pill-tab ${activePreset === 'Q3' ? 'active' : ''}`}
                onClick={() => setPreset('Q3')}
              >
                Q3
              </button>
              <button
                type="button"
                className={`pill-tab ${activePreset === 'L3M' ? 'active' : ''}`}
                onClick={() => setPreset('L3M')}
              >
                Last 3M
              </button>
              <button
                type="button"
                className={`pill-tab ${activePreset === 'ALL' ? 'active' : ''}`}
                onClick={() => setPreset('ALL')}
              >
                All 12M
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Start Date</label>
            <input
              type="date"
              className="form-input"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setActivePreset('CUSTOM');
                setPage(1);
              }}
            />
          </div>

          <div className="form-group">
            <label className="form-label">End Date</label>
            <input
              type="date"
              className="form-input"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setActivePreset('CUSTOM');
                setPage(1);
              }}
            />
          </div>

          <div className="form-group" style={{ minWidth: 180 }}>
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
                  {b.name} ({b.category || 'Standard'})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ minWidth: 180 }}>
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
                  {r.name} ({r.code})
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignSelf: 'flex-end', paddingBottom: '2px' }}>
            {(selectedBrand || selectedRegion || activePreset !== 'YTD') && (
              <Button variant="outline" size="sm" onClick={clearAllFilters}>
                Reset Filters
              </Button>
            )}
          </div>
        </div>

        {/* Active Filter Chips */}
        {(selectedBrand || selectedRegion) && (
          <div className="chips-row">
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
              Active Filters:
            </span>
            {brandObj && (
              <span className="chip">
                Brand: {brandObj.name}
                <button
                  className="chip-remove"
                  onClick={() => setSelectedBrand('')}
                  title="Remove Brand filter"
                >
                  <X size={12} />
                </button>
              </span>
            )}
            {regionObj && (
              <span className="chip">
                Region: {regionObj.name}
                <button
                  className="chip-remove"
                  onClick={() => setSelectedRegion('')}
                  title="Remove Region filter"
                >
                  <X size={12} />
                </button>
              </span>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <Spinner label="Filtering and computing aggregations..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAnalytics} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          {/* Trend Chart with active filters applied */}
          <Card
            title="Sales Trend"
            subtitle={`Monthly aggregated revenue and units for selected filters (${formatDate(startDate)} to ${formatDate(endDate)})`}
          >
            <TrendLineChart data={trend} />
          </Card>

          {/* Comparison Tables Side-by-Side */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
            {/* Brand Comparison */}
            <Card title="Brand Performance Breakdown" subtitle="Revenue, units, and prior-period change">
              {brandPerf.length === 0 ? (
                <EmptyState title="No brand data" description="No sales recorded for the chosen filters." />
              ) : (
                <Table
                  headers={[
                    { label: 'Brand' },
                    { label: 'Revenue', align: 'right' },
                    { label: 'Units', align: 'right' },
                    { label: 'Growth', align: 'right' },
                  ]}
                >
                  {brandPerf.map((b) => (
                    <tr key={b.brand_id}>
                      <td><strong>{b.brand_name}</strong></td>
                      <td className="text-right">{formatINR(b.revenue)}</td>
                      <td className="text-right">{formatNumber(b.units)}</td>
                      <td
                        className="text-right"
                        style={{
                          fontWeight: 600,
                          color: b.revenue_change_pct < 0 ? '#991b1b' : b.revenue_change_pct > 0 ? '#065f46' : 'inherit',
                        }}
                      >
                        {formatPercent(b.revenue_change_pct)}
                      </td>
                    </tr>
                  ))}
                </Table>
              )}
            </Card>

            {/* Region Comparison */}
            <Card title="Regional Performance Breakdown" subtitle="Revenue, units, and prior-period change">
              {regionPerf.length === 0 ? (
                <EmptyState title="No region data" description="No sales recorded for the chosen filters." />
              ) : (
                <Table
                  headers={[
                    { label: 'Region' },
                    { label: 'Revenue', align: 'right' },
                    { label: 'Units', align: 'right' },
                    { label: 'Growth', align: 'right' },
                  ]}
                >
                  {regionPerf.map((r) => (
                    <tr key={r.region_id}>
                      <td><strong>{r.region_name}</strong></td>
                      <td className="text-right">{formatINR(r.revenue)}</td>
                      <td className="text-right">{formatNumber(r.units)}</td>
                      <td
                        className="text-right"
                        style={{
                          fontWeight: 600,
                          color: r.revenue_change_pct < 0 ? '#991b1b' : r.revenue_change_pct > 0 ? '#065f46' : 'inherit',
                        }}
                      >
                        {formatPercent(r.revenue_change_pct)}
                      </td>
                    </tr>
                  ))}
                </Table>
              )}
            </Card>
          </div>

          {/* Granular Sales Transactions Table */}
          <Card
            title="Sales Detail Records"
            subtitle={`Displaying ${salesData.items.length} of ${salesData.total} total rows matching filter criteria`}
          >
            {salesData.items.length === 0 ? (
              <EmptyState title="No transactions" description="No sales rows match your filter parameters." />
            ) : (
              <>
                <Table
                  headers={[
                    { label: 'Date' },
                    { label: 'Brand' },
                    { label: 'Region' },
                    { label: 'Quantity', align: 'right' },
                    { label: 'Revenue (INR)', align: 'right' },
                  ]}
                >
                  {salesData.items.map((row) => (
                    <tr key={row.id}>
                      <td>{formatDate(row.sales_date)}</td>
                      <td><strong>{row.brand_name}</strong></td>
                      <td>{row.region_name}</td>
                      <td className="text-right">{formatNumber(row.quantity)}</td>
                      <td className="text-right" style={{ fontWeight: 600 }}>
                        {formatINR(row.revenue)}
                      </td>
                    </tr>
                  ))}
                </Table>

                {/* Pagination Controls */}
                <div className="pagination-row">
                  <div>
                    Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({salesData.total} items)
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
        </div>
      )}
    </div>
  );
}

export default SalesAnalyticsPage;
