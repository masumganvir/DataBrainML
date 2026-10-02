import React, { useState, useRef } from 'react'
import { datasetsApi } from '@/services/api'
import { Dataset } from '@/types'
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw } from 'lucide-react'

interface DatasetUploadProps {
  sessionId: string
  onUploadSuccess: (dataset: Dataset) => void
}

export default function DatasetUpload({ sessionId, onUploadSuccess }: DatasetUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadedDataset, setUploadedDataset] = useState<Dataset | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (file: File) => {
    setError(null)
    setIsUploading(true)

    try {
      const dataset = await datasetsApi.upload(sessionId, file)
      setUploadedDataset(dataset)
      onUploadSuccess(dataset)
    } catch (err: any) {
      console.error('Upload error:', err)
      const detail = err.response?.data?.detail
      if (typeof detail === 'object' && detail?.message) {
        setError(detail.message)
      } else if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('Failed to upload and validate dataset. Please check the file and try again.')
      }
    } finally {
      setIsUploading(false)
    }
  }

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const onDragLeave = () => {
    setIsDragging(false)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0])
    }
  }

  return (
    <div style={{ width: '100%' }}>
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={onChange}
        accept=".csv,.xlsx,.xls,.json"
        style={{ display: 'none' }}
      />

      {uploadedDataset ? (
        <div className="glass-card" style={{ padding: '24px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '10px',
                background: 'rgba(16, 185, 129, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--success)'
              }}>
                <CheckCircle2 size={24} />
              </div>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>{uploadedDataset.original_filename}</h4>
                <div style={{ display: 'flex', gap: '8px', marginTop: '4px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <span className="badge badge-success">{uploadedDataset.file_format.toUpperCase()}</span>
                  <span>{(uploadedDataset.row_count || 0).toLocaleString()} rows</span>
                  <span>•</span>
                  <span>{uploadedDataset.column_count || 0} columns</span>
                  <span>•</span>
                  <span>{(uploadedDataset.file_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
              </div>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => fileInputRef.current?.click()}
            >
              <RefreshCw size={14} />
              <span>Replace Dataset</span>
            </button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${isDragging ? 'var(--primary-light)' : 'var(--border-medium)'}`,
            borderRadius: 'var(--radius-lg)',
            background: isDragging ? 'rgba(99, 102, 241, 0.08)' : 'rgba(15, 23, 42, 0.5)',
            padding: '40px 24px',
            textAlign: 'center',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            transition: 'all var(--transition-normal)',
          }}
        >
          {isUploading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <div className="spinner"></div>
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Validating & ingesting dataset…</p>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sniffing schema, delimiters, and row encodings</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '56px',
                height: '56px',
                borderRadius: '16px',
                background: 'rgba(99, 102, 241, 0.12)',
                color: 'var(--primary-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(99, 102, 241, 0.2)'
              }}>
                <UploadCloud size={28} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', marginBottom: '6px' }}>
                  Click to upload or drag & drop dataset
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Supports CSV, XLSX, XLS, and JSON (up to 100 MB)
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <span className="badge badge-neutral">.CSV</span>
                <span className="badge badge-neutral">.XLSX</span>
                <span className="badge badge-neutral">.JSON</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div style={{
          marginTop: '12px',
          padding: '12px 16px',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#fca5a5',
          fontSize: '0.85rem'
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
