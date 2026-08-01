import { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import NavBar from '../components/NavBar';
import FormField from '../components/FormField';
import DropZone from '../components/DropZone';
import styles from './UploadPage.module.css';

/* ── Static data ─────────────────────────────────────────────────────────── */
const GENRES = [
  { value: '', label: 'Select a genre…' },
  { value: 'action', label: 'Action' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'animation', label: 'Animation' },
  { value: 'comedy', label: 'Comedy' },
  { value: 'crime', label: 'Crime / Thriller' },
  { value: 'documentary', label: 'Documentary' },
  { value: 'drama', label: 'Drama' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'horror', label: 'Horror' },
  { value: 'musical', label: 'Musical' },
  { value: 'romance', label: 'Romance' },
  { value: 'sci-fi', label: 'Science Fiction' },
  { value: 'western', label: 'Western' },
];

const REGIONS = [
  { value: '', label: 'Any / Not specified' },
  { value: 'north-america', label: 'North America' },
  { value: 'latin-america', label: 'Latin America' },
  { value: 'uk-ireland', label: 'UK & Ireland' },
  { value: 'western-europe', label: 'Western Europe' },
  { value: 'eastern-europe', label: 'Eastern Europe' },
  { value: 'middle-east', label: 'Middle East' },
  { value: 'africa', label: 'Africa' },
  { value: 'south-asia', label: 'South Asia' },
  { value: 'east-asia', label: 'East Asia' },
  { value: 'southeast-asia', label: 'Southeast Asia' },
  { value: 'oceania', label: 'Australia / Oceania' },
];

const INITIAL_FORM = {
  projectName: '',
  genre: '',
  budget: '',
  region: '',
};

const INITIAL_ERRORS = {
  projectName: '',
  genre: '',
  file: '',
};

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function formatBudget(raw) {
  const num = parseFloat(raw);
  if (isNaN(num) || num <= 0) return '—';
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `$${(num / 1_000).toFixed(0)}K`;
  return `$${num.toLocaleString()}`;
}

function validate(form, file) {
  const errs = { projectName: '', genre: '', file: '' };
  if (!form.projectName.trim()) errs.projectName = 'Project name is required.';
  if (!form.genre) errs.genre = 'Please select a genre.';
  if (!file) errs.file = 'Please upload a screenplay file.';
  return errs;
}

/* ── Component ────────────────────────────────────────────────────────────── */
export default function UploadPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState(INITIAL_FORM);
  const [file, setFile] = useState(null);
  const [errors, setErrors] = useState(INITIAL_ERRORS);
  const [submitting, setSubmitting] = useState(false);

  /* ── Field change ───────────────────────────────────────────────────── */
  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: '' }));
  }, []);

  const handleFileChange = useCallback((picked) => {
    setFile(picked);
    if (picked) setErrors((prev) => ({ ...prev, file: '' }));
  }, []);

  /* ── Reset ──────────────────────────────────────────────────────────── */
  const handleReset = () => {
    setForm(INITIAL_FORM);
    setFile(null);
    setErrors(INITIAL_ERRORS);
  };

  /* ── Submit ─────────────────────────────────────────────────────────── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate(form, file);
    const hasErrors = Object.values(errs).some(Boolean);
    if (hasErrors) {
      setErrors(errs);
      return;
    }

    setSubmitting(true);

    /**
     * TODO: Replace the timeout below with a real API call, e.g.:
     *
     *   const formData = new FormData();
     *   formData.append('file', file);
     *   formData.append('projectName', form.projectName);
     *   formData.append('genre', form.genre);
     *   formData.append('budget', form.budget);
     *   formData.append('region', form.region);
     *   const res = await axios.post('/api/analyze', formData);
     *   navigate(`/dashboard?jobId=${res.data.jobId}`);
     */
    await new Promise((r) => setTimeout(r, 1800)); // simulated latency

    setSubmitting(false);
    navigate('/dashboard');
  };

  /* ── Derived display values ─────────────────────────────────────────── */
  const genreLabel =
    GENRES.find((g) => g.value === form.genre)?.label ?? '—';
  const regionLabel =
    REGIONS.find((r) => r.value === form.region)?.label ?? '—';

  /* ── Render ─────────────────────────────────────────────────────────── */
  return (
    <div className={styles.page}>
      <NavBar backTo="/" backLabel="Home" />

      <main className={styles.main}>
        {/* Page header */}
        <header className={styles.pageHeader}>
          <nav className={styles.breadcrumb} aria-label="breadcrumb">
            <Link to="/">Home</Link>
            <span className={styles.breadcrumbSep}>›</span>
            <span>Upload Screenplay</span>
          </nav>

          <h1 className={styles.pageTitle}>
            Upload Your <span>Screenplay</span>
          </h1>
          <p className={styles.pageDesc}>
            Fill in your project details and attach your screenplay. Our AI
            agents will generate a full pre-production package in under a minute.
          </p>
        </header>

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate>
          <div className={styles.formGrid}>

            {/* ── Project details card ── */}
            <div className={`${styles.card} ${styles.cardProject}`}>
              <p className={styles.cardTitle}>
                <span className={styles.cardTitleIcon}>🎬</span>
                Project Details
              </p>

              <div className={styles.fieldsGrid}>
                {/* Project Name */}
                <div className={styles.fieldFull}>
                  <FormField
                    label="Project Name"
                    name="projectName"
                    required
                    placeholder="e.g. The Last Horizon"
                    value={form.projectName}
                    onChange={handleChange}
                    error={errors.projectName}
                    maxLength={120}
                  />
                </div>

                {/* Genre */}
                <FormField
                  label="Genre"
                  name="genre"
                  required
                  type="select"
                  options={GENRES}
                  value={form.genre}
                  onChange={handleChange}
                  error={errors.genre}
                />

                {/* Estimated Budget */}
                <FormField
                  label="Estimated Budget (USD)"
                  name="budget"
                  type="number"
                  placeholder="e.g. 5000000"
                  value={form.budget}
                  onChange={handleChange}
                  hint="Optional — helps calibrate recommendations"
                  min={0}
                />

                {/* Preferred Shooting Region */}
                <div className={styles.fieldFull}>
                  <FormField
                    label="Preferred Shooting Region"
                    name="region"
                    type="select"
                    options={REGIONS}
                    value={form.region}
                    onChange={handleChange}
                    hint="Optional — used for location scouting"
                  />
                </div>
              </div>
            </div>

            {/* ── Upload card ── */}
            <div className={`${styles.card} ${styles.cardUpload}`}>
              <p className={styles.cardTitle}>
                <span className={styles.cardTitleIcon}>📄</span>
                Screenplay File
              </p>

              <DropZone
                file={file}
                onChange={handleFileChange}
                error={errors.file}
              />
            </div>

            {/* ── Summary strip ── */}
            <div className={styles.summaryCard}>
              <div className={styles.summaryItems}>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryItemLabel}>Project</span>
                  <span
                    className={
                      form.projectName
                        ? styles.summaryItemValue
                        : styles.summaryItemValueEmpty
                    }
                  >
                    {form.projectName || 'Untitled'}
                  </span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryItemLabel}>Genre</span>
                  <span
                    className={
                      form.genre
                        ? styles.summaryItemValue
                        : styles.summaryItemValueEmpty
                    }
                  >
                    {form.genre ? genreLabel : 'Not set'}
                  </span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryItemLabel}>Budget</span>
                  <span
                    className={
                      form.budget
                        ? styles.summaryItemValue
                        : styles.summaryItemValueEmpty
                    }
                  >
                    {formatBudget(form.budget)}
                  </span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryItemLabel}>Region</span>
                  <span
                    className={
                      form.region
                        ? styles.summaryItemValue
                        : styles.summaryItemValueEmpty
                    }
                  >
                    {form.region ? regionLabel : 'Any'}
                  </span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryItemLabel}>File</span>
                  <span
                    className={
                      file
                        ? styles.summaryItemValue
                        : styles.summaryItemValueEmpty
                    }
                  >
                    {file ? file.name : 'No file'}
                  </span>
                </div>
              </div>
            </div>

            {/* ── Actions ── */}
            <div className={styles.submitRow}>
              <button
                type="button"
                className={styles.resetBtn}
                onClick={handleReset}
                disabled={submitting}
              >
                Reset
              </button>
              <button
                type="submit"
                className={styles.submitBtn}
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <span className={styles.submitSpinner} />
                    Analyzing…
                  </>
                ) : (
                  <>⚡ Analyze with AI</>
                )}
              </button>
            </div>

          </div>
        </form>
      </main>
    </div>
  );
}
