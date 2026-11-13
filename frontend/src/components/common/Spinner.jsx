import React from 'react';
import { Loader2 } from 'lucide-react';

export function Spinner({ size = 24, label = 'Loading data...', className = '' }) {
  return (
    <div
      className={`state-box ${className}`}
      style={{ padding: '2rem 1rem' }}
      role="status"
    >
      <Loader2
        size={size}
        style={{
          color: 'var(--color-primary)',
          animation: 'spin 1s linear infinite',
        }}
      />
      {label && (
        <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          {label}
        </span>
      )}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Spinner;
