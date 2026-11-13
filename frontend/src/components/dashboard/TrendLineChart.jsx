import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
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

  const formatCompactINR = (val) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
    return `₹${val}`;
  };

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 15, right: 25, left: 10, bottom: 5 }}>
          <defs>
            {/* Revenue Gradient Fill (Purple-to-Transparent) */}
            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#a855f7" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#a855f7" stopOpacity={0.0} />
            </linearGradient>

            {/* Units Gradient Fill (Cyan-to-Transparent) */}
            <linearGradient id="colorUnits" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          
          <XAxis
            dataKey="month"
            stroke="#94a3b8"
            fontSize={12}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          
          <YAxis
            yAxisId="left"
            tickFormatter={formatCompactINR}
            stroke="#9333ea"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={formatNumber}
            stroke="#06b6d4"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          
          <Tooltip
            formatter={(value, name) => {
              if (name === 'Revenue (INR)') return [formatINR(value), name];
              return [formatNumber(value), name];
            }}
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '0.75rem',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
              padding: '0.75rem 1rem',
              fontWeight: 600,
            }}
          />
          
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ paddingBottom: '1rem', fontSize: '0.8125rem', fontWeight: 600 }}
          />

          <Area
            yAxisId="left"
            type="monotone"
            dataKey="revenue"
            name="Revenue (INR)"
            stroke="#9333ea"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorRevenue)"
            activeDot={{ r: 6, fill: '#9333ea', stroke: '#ffffff', strokeWidth: 2 }}
          />
          
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="units"
            name="Units"
            stroke="#06b6d4"
            strokeWidth={2.5}
            strokeDasharray="4 4"
            fillOpacity={1}
            fill="url(#colorUnits)"
            activeDot={{ r: 5, fill: '#06b6d4', stroke: '#ffffff', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendLineChart;
