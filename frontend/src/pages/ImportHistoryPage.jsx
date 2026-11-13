import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History,
  FileText,
  ChevronLeft,
  ChevronRight,
  UploadCloud,
  AlertCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
} from 'lucide-react';
import apiClient from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Table from '../components/common/Table';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { StatusBadge } from '../components/common/Badge';
import { formatNumber, formatDateTime } from '../utils/formatters';

export function ImportHistoryPage() {
  const navigate = useNavigate();

  const [imports, setImports] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Detail Modal
  const [selectedImport, setSelectedImport] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchImports = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.getImports({ page, page_size: pageSize });
      setImports({
        items: res.data.items || [],
        total: res.data.total || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch import history');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchImports();
  }, [fetchImports]);

  const handleViewDetail = async (importId) => {
    try {
      setDetailLoading(true);
      const res = await apiClient.getImportDetail(importId);
      setSelectedImport(res.data);
    } catch (err) {
      alert('Failed to load import detail');
    } finally {
      setDetailLoading(false);
    }
  };

  const totalPages = Math.ceil((imports.total || 0) / pageSize) || 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          Audit trail of all uploaded sales CSV files, validation status, and row-level rejection logs.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchImports}>
            Refresh
          </Button>
          <Button
            variant="primary"
            icon={UploadCloud}
            onClick={() => navigate('/upload')}
          >
            Upload New File
          </Button>
        </div>
      </div>

      <Card
        title="File Ingestion Logs"
        subtitle={`Showing ${imports.items.length} of ${imports.total} total imports`}
      >
        {loading ? (
          <Spinner label="Loading import audit trail..." />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchImports} />
        ) : imports.items.length === 0 ? (
          <EmptyState
            icon={History}
            title="No imports recorded yet"
            description="Upload your first CSV file to populate the sales intelligence database."
            actionLabel="Go to Upload Data"
            onAction={() => navigate('/upload')}
          />
        ) : (
          <>
            <Table
              headers={[
                { label: 'Import ID', width: '90px' },
                { label: 'File Name' },
                { label: 'Imported At' },
                { label: 'Status' },
                { label: 'Total Rows', align: 'right' },
                { label: 'Accepted', align: 'right' },
                { label: 'Rejected', align: 'right' },
                { label: 'Actions', align: 'center' },
              ]}
            >
              {imports.items.map((imp) => (
                <tr key={imp.id}>
                  <td>#{imp.id}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontWeight: 600 }}>
                      <FileText size={14} style={{ color: 'var(--color-text-muted)' }} />
                      <span>{imp.file_name}</span>
                    </div>
                  </td>
                  <td style={{ fontSize: '0.8125rem' }}>
                    {formatDateTime(imp.imported_at)}
                  </td>
                  <td>
                    <StatusBadge status={imp.status} />
                  </td>
                  <td className="text-right">{formatNumber(imp.total_rows)}</td>
                  <td className="text-right" style={{ color: '#065f46', fontWeight: 600 }}>
                    {formatNumber(imp.accepted_rows)}
                  </td>
                  <td
                    className="text-right"
                    style={{
                      color: imp.rejected_rows > 0 ? '#991b1b' : 'inherit',
                      fontWeight: imp.rejected_rows > 0 ? 600 : 'normal',
                    }}
                  >
                    {formatNumber(imp.rejected_rows)}
                  </td>
                  <td className="text-center">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleViewDetail(imp.id)}
                    >
                      Details & Errors
                    </Button>
                  </td>
                </tr>
              ))}
            </Table>

            {/* Pagination Controls */}
            <div className="pagination-row">
              <div>
                Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({imports.total} total imports)
              </div>
              <div className="pagination-controls">
                <Button
                  variant="outline"
                  size="sm"
                  icon={ChevronLeft}
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page <= 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  disabled={page >= totalPages}
                >
                  Next
                  <ChevronRight size={14} />
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Import Detail & Errors Modal */}
      {selectedImport && (
        <Modal
          isOpen={Boolean(selectedImport)}
          onClose={() => setSelectedImport(null)}
          title={`Import #${selectedImport.id} — ${selectedImport.file_name}`}
          maxWidth="700px"
          footer={
            <Button variant="outline" onClick={() => setSelectedImport(null)}>
              Close
            </Button>
          }
        >
          {/* Status & Timing */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <StatusBadge status={selectedImport.status} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                {formatDateTime(selectedImport.imported_at)}
              </span>
            </div>
            {selectedImport.file_hash && (
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }} title={selectedImport.file_hash}>
                SHA-256: {selectedImport.file_hash.substring(0, 12)}...
              </span>
            )}
          </div>

          {/* Counts */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: 'var(--radius-md)' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Total Rows</span>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{formatNumber(selectedImport.total_rows)}</div>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: '#065f46' }}>Accepted Rows</span>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#065f46' }}>
                {formatNumber(selectedImport.accepted_rows)}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: selectedImport.rejected_rows > 0 ? '#991b1b' : 'var(--color-text-muted)' }}>
                Rejected Rows
              </span>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: selectedImport.rejected_rows > 0 ? '#991b1b' : 'inherit' }}>
                {formatNumber(selectedImport.rejected_rows)}
              </div>
            </div>
          </div>

          {/* Errors table */}
          {selectedImport.errors && selectedImport.errors.length > 0 ? (
            <div>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#991b1b', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <AlertCircle size={14} />
                Validation Errors ({selectedImport.errors.length} {selectedImport.errors_truncated ? 'shown of total' : 'recorded'})
              </h4>
              <Table headers={[{ label: 'Row #', width: '90px' }, { label: 'Field', width: '130px' }, { label: 'Validation Issue' }]}>
                {selectedImport.errors.map((err, idx) => (
                  <tr key={idx}>
                    <td>Row {err.row_number}</td>
                    <td><code>{err.field}</code></td>
                    <td style={{ color: '#991b1b' }}>{err.message}</td>
                  </tr>
                ))}
              </Table>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#065f46', fontSize: '0.875rem', padding: '0.75rem', backgroundColor: 'var(--color-success-light)', borderRadius: 'var(--radius-md)' }}>
              <CheckCircle2 size={16} />
              <span>No errors. All data rows met validation constraints.</span>
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}

export default ImportHistoryPage;
