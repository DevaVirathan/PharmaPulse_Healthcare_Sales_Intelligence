import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import { Play, CheckCircle2, AlertTriangle } from 'lucide-react';
import apiClient from '../../services/api';

export function RunDetectionModal({ isOpen, onClose, onDetectionCompleted }) {
  const [month, setMonth] = useState('2026-10');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleRun = async () => {
    try {
      setRunning(true);
      setError(null);
      setResult(null);
      const res = await apiClient.runDetection(month);
      setResult(res.data);
      if (onDetectionCompleted) {
        onDetectionCompleted(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Detection failed');
    } finally {
      setRunning(false);
    }
  };

  const footer = (
    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', width: '100%' }}>
      <Button variant="outline" onClick={onClose} disabled={running}>
        {result ? 'Done' : 'Cancel'}
      </Button>
      {!result && (
        <Button
          variant="primary"
          icon={Play}
          onClick={handleRun}
          loading={running}
          disabled={!month}
        >
          Execute Detection
        </Button>
      )}
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Run Anomaly Detection"
      footer={footer}
      maxWidth="500px"
    >
      <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
        Evaluate month-over-month sales figures for each brand-region pair and surface unusual declines ($\ge 20\%$) and growths ($\ge 30\%$).
      </p>

      <div className="form-group" style={{ marginTop: '0.5rem' }}>
        <label className="form-label">Target Month (YYYY-MM)</label>
        <input
          type="month"
          className="form-input"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          disabled={running}
        />
      </div>

      {error && (
        <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-light)', color: '#991b1b', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--color-success-light)', border: '1px solid #a7f3d0', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#065f46', fontWeight: 600, fontSize: '0.9375rem', marginBottom: '0.5rem' }}>
            <CheckCircle2 size={18} />
            Detection Completed Successfully
          </div>
          <div style={{ fontSize: '0.875rem', color: '#065f46', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            <div>Evaluated brand-region pairs: <strong>{result.evaluated_combinations}</strong></div>
            <div>New alerts created: <strong>{result.alerts_created}</strong></div>
            <div>Existing OPEN alerts refreshed: <strong>{result.alerts_updated}</strong></div>
          </div>
        </div>
      )}
    </Modal>
  );
}

export default RunDetectionModal;
