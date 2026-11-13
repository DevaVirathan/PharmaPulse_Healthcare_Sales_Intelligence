import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import Button from './Button';

export function ErrorState({
  title = 'Failed to load data',
  message = 'An unexpected error occurred while fetching information from the server.',
  onRetry,
}) {
  return (
    <div className="state-box" style={{ color: 'var(--color-danger)' }}>
      <AlertCircle className="state-icon" style={{ color: 'var(--color-danger)' }} />
      <h4 className="state-title" style={{ color: 'var(--color-text-main)' }}>
        {title}
      </h4>
      <p className="state-desc">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          onClick={onRetry}
          icon={RotateCcw}
          style={{ marginTop: '0.5rem' }}
        >
          Try Again
        </Button>
      )}
    </div>
  );
}

export default ErrorState;
