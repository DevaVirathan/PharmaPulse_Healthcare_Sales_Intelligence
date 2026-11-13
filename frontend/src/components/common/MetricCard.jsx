import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatPercent } from '../../utils/formatters';

export function MetricCard({
  title,
  value,
  change,
  changeLabel = 'vs prev window',
  icon: Icon,
}) {
  let changeType = 'neutral';
  let ChangeIcon = Minus;

  if (change !== null && change !== undefined && !isNaN(change)) {
    const num = Number(change);
    if (num > 0) {
      changeType = 'positive';
      ChangeIcon = TrendingUp;
    } else if (num < 0) {
      changeType = 'negative';
      ChangeIcon = TrendingDown;
    }
  }

  return (
    <div className="kpi-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="kpi-title">{title}</span>
        {Icon && (
          <div
            style={{
              padding: '0.375rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-primary-light)',
              color: 'var(--color-primary)',
              display: 'flex',
            }}
          >
            <Icon size={16} />
          </div>
        )}
      </div>

      <div className="kpi-value-row">
        <span className="kpi-value">{value}</span>
      </div>

      {change !== undefined && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
          <span className={`kpi-change ${changeType}`}>
            <ChangeIcon size={12} />
            {formatPercent(change)}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            {changeLabel}
          </span>
        </div>
      )}
    </div>
  );
}

export default MetricCard;
