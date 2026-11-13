import React from 'react';
import { Inbox } from 'lucide-react';
import Button from './Button';

export function EmptyState({
  title = 'No data found',
  description = 'There are no records matching your current filter selection.',
  icon: Icon = Inbox,
  actionLabel,
  onAction,
}) {
  return (
    <div className="state-box">
      <Icon className="state-icon" />
      <h4 className="state-title">{title}</h4>
      <p className="state-desc">{description}</p>
      {actionLabel && onAction && (
        <Button variant="secondary" onClick={onAction} style={{ marginTop: '0.5rem' }}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
