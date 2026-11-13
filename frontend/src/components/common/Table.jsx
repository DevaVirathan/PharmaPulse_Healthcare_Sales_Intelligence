import React from 'react';

export function Table({ headers = [], children, className = '' }) {
  return (
    <div className={`table-container ${className}`}>
      <table className="data-table">
        {headers.length > 0 && (
          <thead>
            <tr>
              {headers.map((h, idx) => (
                <th
                  key={idx}
                  className={h.align === 'right' ? 'text-right' : h.align === 'center' ? 'text-center' : ''}
                  style={h.width ? { width: h.width } : {}}
                >
                  {h.label}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export default Table;
