import { useRef, useState, useCallback } from 'react';
import styles from './DropZone.module.css';

const ACCEPTED_TYPES = ['application/pdf', 'application/vnd.final-draft'];
const ACCEPTED_EXTS = ['.pdf', '.fdx'];
const MAX_SIZE_MB = 50;

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function validateFile(file) {
  const extOk = ACCEPTED_EXTS.some((ext) =>
    file.name.toLowerCase().endsWith(ext)
  );
  if (!extOk) return 'Only .pdf and .fdx files are accepted.';
  if (file.size > MAX_SIZE_MB * 1024 * 1024)
    return `File exceeds the ${MAX_SIZE_MB} MB limit.`;
  return null;
}

/**
 * DropZone — drag-and-drop / click-to-browse file upload area.
 *
 * Props:
 *   file      {File|null}  – controlled selected file (or null)
 *   onChange  {Function}   – called with (File|null) on selection / removal
 *   error     {string}     – external validation error to display
 */
export default function DropZone({ file, onChange, error: externalError }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState('');

  const displayError = localError || externalError;

  const handleFiles = useCallback(
    (files) => {
      setLocalError('');
      const picked = files[0];
      if (!picked) return;
      const err = validateFile(picked);
      if (err) {
        setLocalError(err);
        onChange(null);
        return;
      }
      onChange(picked);
    },
    [onChange]
  );

  /* ── Drag handlers ───────────────────────────────────────────────────── */
  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };
  const onDragLeave = (e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false);
  };
  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  /* ── Input change ────────────────────────────────────────────────────── */
  const onInputChange = (e) => handleFiles(e.target.files);

  const remove = (e) => {
    e.stopPropagation();
    setLocalError('');
    onChange(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const zoneClass = [
    styles.zone,
    dragging ? styles.zoneActive : '',
    displayError ? styles.zoneError : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div>
      {/* Drop area — always visible so user can re-pick */}
      <div
        className={zoneClass}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload screenplay file"
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          className={styles.fileInput}
          accept=".pdf,.fdx"
          onChange={onInputChange}
          onClick={(e) => e.stopPropagation()}
          tabIndex={-1}
        />

        <span className={styles.icon}>{file ? '📄' : '🎞️'}</span>

        <p className={styles.title}>
          {dragging
            ? 'Release to upload'
            : file
            ? 'Replace screenplay'
            : 'Drop your screenplay here'}
        </p>

        <p className={styles.subtitle}>
          {file ? 'Click or drop to swap the file' : 'or click to browse your files'}
        </p>

        <div className={styles.formatBadges}>
          <span className={styles.badge}>PDF</span>
          <span className={styles.badge}>FDX</span>
          <span className={styles.badge}>Max {MAX_SIZE_MB} MB</span>
        </div>
      </div>

      {/* Selected file preview */}
      {file && (
        <div className={styles.preview}>
          <span className={styles.previewIcon}>
            {file.name.endsWith('.fdx') ? '🎬' : '📄'}
          </span>
          <div className={styles.previewMeta}>
            <div className={styles.previewName}>{file.name}</div>
            <div className={styles.previewSize}>{formatBytes(file.size)}</div>
          </div>
          <button
            type="button"
            className={styles.removeBtn}
            onClick={remove}
            aria-label="Remove file"
            title="Remove file"
          >
            ×
          </button>
        </div>
      )}

      {displayError && <p className={styles.errorMsg}>⚠ {displayError}</p>}
    </div>
  );
}
