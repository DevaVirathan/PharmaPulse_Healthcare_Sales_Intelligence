/**
 * Formatting utilities for currency (INR), percentages, and dates.
 */

export function formatINR(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return '₹0.00';
  }
  const num = Number(value);
  const isNegative = num < 0;
  const absValue = Math.abs(num).toFixed(2);
  const [intPart, decPart] = absValue.split('.');

  let formattedInt = '';
  if (intPart.length > 3) {
    const lastThree = intPart.substring(intPart.length - 3);
    const otherNumbers = intPart.substring(0, intPart.length - 3);
    formattedInt =
      otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + lastThree;
  } else {
    formattedInt = intPart;
  }

  return `${isNegative ? '-' : ''}₹${formattedInt}.${decPart}`;
}

export function formatINRCompact(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return '₹0.00';
  }
  const num = Number(value);
  const isNegative = num < 0;
  const abs = Math.abs(num);

  let formatted = '';
  if (abs >= 10000000) {
    formatted = `${(abs / 10000000).toFixed(2)} Cr`;
  } else if (abs >= 100000) {
    formatted = `${(abs / 100000).toFixed(2)} L`;
  } else if (abs >= 1000) {
    formatted = `${(abs / 1000).toFixed(1)}k`;
  } else {
    formatted = abs.toFixed(2);
  }

  return `${isNegative ? '-' : ''}₹${formatted}`;
}

export function formatPercent(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  const num = Number(value);
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
}

export function formatNumber(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return '0';
  }
  return Number(value).toLocaleString('en-IN');
}

export function formatDate(dateString) {
  if (!dateString) return '-';
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return dateString;
  return d.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatMonthYear(dateString) {
  if (!dateString) return '-';
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return dateString;
  return d.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
  });
}

export function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '-';
  const d = new Date(dateTimeString);
  if (isNaN(d.getTime())) return dateTimeString;
  return d.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
