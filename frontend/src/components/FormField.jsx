import styles from './FormField.module.css';

/**
 * FormField — reusable labelled input or select.
 *
 * Props:
 *   label      {string}   – visible label text
 *   required   {boolean}  – appends a * marker
 *   hint       {string}   – optional helper text below the field
 *   error      {string}   – validation error message
 *   type       {string}   – "text" | "number" | "select" (default "text")
 *   options    {Array}    – [{ value, label }] — required when type="select"
 *   All other props are forwarded to <input> or <select>.
 */
export default function FormField({
  label,
  required = false,
  hint,
  error,
  type = 'text',
  options = [],
  id,
  ...rest
}) {
  const fieldId = id || label?.toLowerCase().replace(/\s+/g, '-');
  const hasError = Boolean(error);

  return (
    <div className={styles.group}>
      {label && (
        <label htmlFor={fieldId} className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}

      {type === 'select' ? (
        <div className={styles.selectWrap}>
          <select
            id={fieldId}
            className={`${styles.select}${hasError ? ` ${styles.hasError}` : ''}`}
            {...rest}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <input
          id={fieldId}
          type={type}
          className={`${styles.input}${hasError ? ` ${styles.hasError}` : ''}`}
          {...rest}
        />
      )}

      {hint && !error && <p className={styles.hint}>{hint}</p>}
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
