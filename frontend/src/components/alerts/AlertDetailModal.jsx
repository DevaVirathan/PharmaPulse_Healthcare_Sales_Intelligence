import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import { SeverityBadge, StatusBadge } from '../common/Badge';
import { formatINR, formatPercent, formatDate, formatDateTime } from '../../utils/formatters';
import { Check, AlertCircle } from 'lucide-react';

export function AlertDetailModal({ alert, isOpen, onClose, onStatusUpdated }) {
  const [selectedStatus, setSelectedStatus] = useState(alert?.status || 'OPEN');
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState(null);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  if (!alert) return null;

  const handleUpdate = async () => {
    if (selectedStatus === alert.status) return;
    try {
      setUpdating(true);
      setUpdateError(null);
      setUpdateSuccess(false);
      await onStatusUpdated(alert.id, selectedStatus);
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);
    } catch (err) {
      setUpdateError(err.response?.data?.detail || err.message || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const footer = (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <select
          className="form-select"
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          disabled={updating}
        >
          <option value="OPEN">OPEN</option>
          <option value="INVESTIGATING">INVESTIGATING</option>
          <option value="RESOLVED">RESOLVED</option>
          <option value="DISMISSED">DISMISSED</option>
        </select>
        <Button
          variant="primary"
          onClick={handleUpdate}
          loading={updating}
          disabled={selectedStatus === alert.status}
        >
          Save Status
        </Button>
        {updateSuccess && (
          <span style={{ color: 'var(--color-success)', fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Check size={14} /> Saved
          </span>
        )}
      </div>
      <Button variant="outline" onClick={onClose}>
        Close
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Alert #${alert.id} — ${alert.brand_name} (${alert.region_name})`}
      footer={footer}
      maxWidth="680px"
    >
      {updateError && (
        <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-light)', color: '#991b1b', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
          {updateError}
        </div>
      )}

      {/* Top Badges & Meta */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <SeverityBadge severity={alert.severity} />
          <StatusBadge status={alert.status} />
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          Period: {formatDate(alert.period_start)} – {formatDate(alert.period_end)}
        </span>
      </div>

      {/* Metrics Comparison Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', backgroundColor: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Previous Baseline
          </span>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem' }}>
            {formatINR(alert.previous_value)}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Current Value
          </span>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem' }}>
            {formatINR(alert.current_value)}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Observed Change
          </span>
          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              marginTop: '0.25rem',
              color: alert.change_pct < 0 ? '#991b1b' : '#065f46',
            }}
          >
            {formatPercent(alert.change_pct)}
          </div>
        </div>
      </div>

      {/* Factual Stored Explanation */}
      <div>
        <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
          Factual Explanation
        </h4>
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderLeft: '4px solid var(--color-primary)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.9375rem',
            lineHeight: 1.6,
            color: 'var(--color-text-main)',
          }}
        >
          {alert.explanation}
        </div>
      </div>

      {/* Rule Reference Details */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8125rem' }}>
        <div>
          <span style={{ color: 'var(--color-text-muted)' }}>Configured Rule: </span>
          <strong>{alert.rule_name}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--color-text-muted)' }}>Comparison Period: </span>
          <strong>{alert.comparison_period || 'month_over_month'}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--color-text-muted)' }}>Decline Threshold: </span>
          <strong>{alert.decline_threshold_pct}%</strong>
        </div>
        <div>
          <span style={{ color: 'var(--color-text-muted)' }}>Growth Threshold: </span>
          <strong>{alert.growth_threshold_pct}%</strong>
        </div>
      </div>

      {/* Disclaimer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.75rem',
          color: 'var(--color-text-muted)',
          backgroundColor: '#f1f5f9',
          padding: '0.625rem 0.875rem',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <AlertCircle size={14} />
        <span>
          An alert is an objective signal to prioritize investigation. It does not provide automated diagnoses or assign blame.
        </span>
      </div>
    </Modal>
  );
}

export default AlertDetailModal;
