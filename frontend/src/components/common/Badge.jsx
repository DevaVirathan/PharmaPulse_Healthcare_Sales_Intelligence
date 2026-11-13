import React from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Clock,
  Eye,
  XCircle,
} from 'lucide-react';

export function SeverityBadge({ severity }) {
  const norm = (severity || '').toUpperCase();

  if (norm === 'HIGH') {
    return (
      <span className="badge badge-severity-high" title="High Severity Anomaly">
        <AlertTriangle size={12} aria-hidden="true" />
        <span>HIGH</span>
      </span>
    );
  }

  if (norm === 'MEDIUM') {
    return (
      <span className="badge badge-severity-medium" title="Medium Severity Anomaly">
        <AlertCircle size={12} aria-hidden="true" />
        <span>MEDIUM</span>
      </span>
    );
  }

  return (
    <span className="badge badge-severity-low" title="Low Severity Anomaly">
      <Info size={12} aria-hidden="true" />
      <span>LOW</span>
    </span>
  );
}

export function StatusBadge({ status }) {
  const norm = (status || '').toUpperCase();

  switch (norm) {
    case 'OPEN':
      return (
        <span className="badge badge-status-open">
          <Clock size={12} aria-hidden="true" />
          <span>OPEN</span>
        </span>
      );
    case 'INVESTIGATING':
      return (
        <span className="badge badge-status-investigating">
          <Eye size={12} aria-hidden="true" />
          <span>INVESTIGATING</span>
        </span>
      );
    case 'RESOLVED':
      return (
        <span className="badge badge-status-resolved">
          <CheckCircle2 size={12} aria-hidden="true" />
          <span>RESOLVED</span>
        </span>
      );
    case 'DISMISSED':
      return (
        <span className="badge badge-status-dismissed">
          <XCircle size={12} aria-hidden="true" />
          <span>DISMISSED</span>
        </span>
      );
    case 'COMPLETED':
      return (
        <span className="badge badge-status-resolved">
          <CheckCircle2 size={12} aria-hidden="true" />
          <span>COMPLETED</span>
        </span>
      );
    case 'COMPLETED_WITH_ERRORS':
      return (
        <span className="badge badge-severity-medium">
          <AlertCircle size={12} aria-hidden="true" />
          <span>PARTIAL (ERRORS)</span>
        </span>
      );
    case 'FAILED':
      return (
        <span className="badge badge-severity-high">
          <XCircle size={12} aria-hidden="true" />
          <span>FAILED</span>
        </span>
      );
    default:
      return <span className="badge badge-status-dismissed">{status}</span>;
  }
}
