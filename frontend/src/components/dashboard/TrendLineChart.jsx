import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { formatINR, formatNumber } from '../../utils/formatters';

export function TrendLineChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ height: 320, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
        No trend data available for selected period
      </div>
    );
  }

  // Format currency in compact form for Y-axis (e.g. ₹5L, ₹10L)
  const formatCompactINR = (val) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
    return `₹${val}`;
  };

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
          <YAxis
            yAxisId="left"
            tickFormatter={formatCompactINR}
            stroke="#0284c7"
            fontSize={12}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={formatNumber}
            stroke="#10b981"
            fontSize={12}
          />
          <Tooltip
            formatter={(value, name) => {
              if (name === 'Revenue (INR)') return [formatINR(value), name];
              return [formatNumber(value), name];
            }}
            contentStyle={{
              backgroundColor: '#ffffff',
              borderColor: '#e2e8f0',
              borderRadius: '0.375rem',
              boxShadow: 'var(--shadow-md)',
            }}
          />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="revenue"
            name="Revenue (INR)"
            stroke="#0284c7"
            strokeWidth={2.5}
            dot={{ r: 3 }}
            activeDot={{ r: 6 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="units"
            name="Units"
            stroke="#10b981"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={{ r: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendLineChart;
