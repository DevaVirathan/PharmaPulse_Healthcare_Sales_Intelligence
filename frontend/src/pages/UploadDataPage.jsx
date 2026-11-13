import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  History,
  Info,
  X,
} from 'lucide-react';
import apiClient from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Table from '../components/common/Table';
import { StatusBadge } from '../components/common/Badge';
import { formatNumber } from '../utils/formatters';

export function UploadDataPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Results
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [duplicateConflict, setDuplicateConflict] = useState(null);

  const handleFileSelect = (selectedFile) => {
    setError(null);
    setResult(null);
    setDuplicateConflict(null);

    if (!selectedFile) return;

    // Client-side checks as convenience
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setError('Selected file must be a CSV (.csv) document.');
      return;
    }
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('File size exceeds the 5 MB limit.');
      return;
    }

    setFile(selectedFile);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      setResult(null);
      setDuplicateConflict(null);
      setUploadProgress(0);

      const res = await apiClient.uploadCSV(file, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        }
      });

      setResult(res.data);
    } catch (err) {
      if (err.response?.status === 409) {
        setDuplicateConflict(err.response.data?.detail);
      } else {
        const detail = err.response?.data?.detail;
        const msg = typeof detail === 'object' ? detail.message : detail;
        setError(msg || err.message || 'CSV upload failed');
      }
    } finally {
      setUploading(false);
    }
  };

  const clearSelection = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setDuplicateConflict(null);
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Upload Zone Card */}
      <Card
        title="Upload Sales CSV"
        subtitle="Upload a batch of pharmaceutical sales records for transactional validation and storage"
        action={
          <Button
            variant="outline"
            size="sm"
            icon={History}
            onClick={() => navigate('/imports')}
          >
            Import History
          </Button>
        }
      >
        {/* Drag and Drop Zone */}
        <div
          className={`dropzone ${isDragActive ? 'drag-active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".csv"
            onChange={(e) => handleFileSelect(e.target.files?.[0])}
            disabled={uploading}
          />
          <UploadCloud size={48} style={{ color: 'var(--color-primary)' }} />
          <div>
            <p style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--color-text-main)' }}>
              {file ? file.name : 'Click to select or drag and drop a CSV file'}
            </p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
              {file
                ? `${(file.size / 1024).toFixed(1)} KB — ready to upload`
                : 'UTF-8 formatted .csv file up to 5 MB'}
            </p>
          </div>

          {file && !uploading && (
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => {
                e.stopPropagation();
                clearSelection();
              }}
              icon={X}
            >
              Clear Selected File
            </Button>
          )}
        </div>

        {/* Upload Progress Bar */}
        {uploading && (
          <div style={{ marginTop: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              <span>Uploading & parsing file in database...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        )}

        {/* Submit Actions */}
        <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={!file || uploading}
            loading={uploading}
            icon={UploadCloud}
          >
            {uploading ? 'Processing File...' : 'Upload & Process'}
          </Button>
        </div>
      </Card>

      {/* 409 Duplicate File Warning */}
      {duplicateConflict && (
        <div style={{ padding: '1.25rem', backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <AlertTriangle style={{ color: '#d97706', flexShrink: 0 }} size={20} />
            <div>
              <h4 style={{ fontWeight: 600, color: '#92400e', fontSize: '0.9375rem' }}>
                Duplicate Upload Blocked (409 Conflict)
              </h4>
              <p style={{ color: '#92400e', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                {duplicateConflict.message || 'This file has already been imported with identical content.'}
              </p>
              {duplicateConflict.import_id && (
                <div style={{ marginTop: '0.75rem' }}>
                  <Link
                    to="/imports"
                    style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-primary)', textDecoration: 'underline' }}
                  >
                    View existing Import #{duplicateConflict.import_id} in history &rarr;
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* General Error Banner */}
      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--color-danger-light)', border: '1px solid #fecaca', borderRadius: 'var(--radius-lg)', color: '#991b1b', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <AlertCircle size={18} />
          <span style={{ fontSize: '0.875rem' }}>{error}</span>
        </div>
      )}

      {/* Import Results Panel */}
      {result && (
        <Card title={`Import Result: #${result.import_id} — ${result.file_name}`}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '1rem', borderBottom: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <StatusBadge status={result.status} />
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
                {result.status === 'COMPLETED'
                  ? 'All rows were validated and accepted.'
                  : result.status === 'COMPLETED_WITH_ERRORS'
                  ? 'Partial acceptance: valid rows saved, invalid rows rejected.'
                  : 'Import failed: no rows were imported.'}
              </span>
            </div>
            <Link to="/imports" style={{ fontSize: '0.8125rem', color: 'var(--color-primary)', textDecoration: 'underline' }}>
              View in Import History
            </Link>
          </div>

          {/* Counts Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1rem', marginBottom: '1.25rem' }}>
            <div style={{ padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Total Parsed</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{formatNumber(result.total_rows)}</div>
            </div>

            <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-success-light)', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.75rem', color: '#065f46' }}>Accepted Rows</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#065f46' }}>
                {formatNumber(result.accepted_rows)}
              </div>
            </div>

            <div style={{ padding: '0.75rem', backgroundColor: result.rejected_rows > 0 ? 'var(--color-danger-light)' : '#f8fafc', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.75rem', color: result.rejected_rows > 0 ? '#991b1b' : 'var(--color-text-muted)' }}>
                Rejected Rows
              </span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: result.rejected_rows > 0 ? '#991b1b' : 'inherit' }}>
                {formatNumber(result.rejected_rows)}
              </div>
            </div>
          </div>

          {/* Row-Level Errors Table */}
          {result.errors && result.errors.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#991b1b', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <AlertCircle size={14} />
                Validation Errors ({result.errors.length} {result.errors_truncated ? 'shown of total' : 'found'})
              </h4>
              <Table headers={[{ label: 'Row #', width: '90px' }, { label: 'Field', width: '130px' }, { label: 'Validation Issue' }]}>
                {result.errors.map((err, idx) => (
                  <tr key={idx}>
                    <td>Row {err.row_number}</td>
                    <td><code>{err.field}</code></td>
                    <td style={{ color: '#991b1b' }}>{err.message}</td>
                  </tr>
                ))}
              </Table>
            </div>
          )}
        </Card>
      )}

      {/* CSV Contract & Format Guidance */}
      <Card title="CSV Format Requirements & Sample">
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
          Your CSV file must include the exact header below. Extra columns are ignored. Master data (brand and region names) must match seeded records (case-insensitive) and will never be auto-created.
        </p>

        <div style={{ backgroundColor: '#0f172a', color: '#38bdf8', padding: '1rem', borderRadius: 'var(--radius-md)', fontFamily: 'monospace', fontSize: '0.8125rem', overflowX: 'auto' }}>
          <div>sales_date,brand_name,region_name,quantity,revenue</div>
          <div style={{ color: '#94a3b8' }}>2026-10-01,Cardioval,Chennai,2400,164621.32</div>
          <div style={{ color: '#94a3b8' }}>2026-10-01,Neurozen,Coimbatore,3100,492528.37</div>
        </div>

        <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
          <div>&bull; <strong>sales_date:</strong> YYYY-MM-DD format</div>
          <div>&bull; <strong>quantity:</strong> Non-negative integer</div>
          <div>&bull; <strong>brand_name:</strong> Cardioval, Neurozen, Glucofine, Oncovera, Respirax</div>
          <div>&bull; <strong>revenue:</strong> Non-negative decimal (INR)</div>
          <div>&bull; <strong>region_name:</strong> Chennai, Coimbatore, Madurai, Trichy</div>
          <div>&bull; <strong>Partial Acceptance:</strong> Valid rows are stored; invalid rows are logged</div>
        </div>
      </Card>
    </div>
  );
}

export default UploadDataPage;
