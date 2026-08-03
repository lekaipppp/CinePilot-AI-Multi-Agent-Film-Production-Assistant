import { Link } from 'react-router-dom';
import styles from './NavBar.module.css';

/**
 * NavBar — shared cinematic navigation bar.
 *
 * Props:
 *   backTo   {string}  – if set, shows a "← Back" link pointing to this path
 *   backLabel {string} – label for the back link (default "Back")
 */
export default function NavBar({ backTo, backLabel = 'Back' }) {
  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.brand}>
        <span className={styles.brandLogo}>🎬</span>
        <span className={styles.brandTitle}>CinePilot AI</span>
      </Link>

      <ul className={styles.links}>
        {backTo ? (
          <li>
            <Link to={backTo} className={styles.backLink}>
              ← {backLabel}
            </Link>
          </li>
        ) : (
          <>
            <li><a href="/#agents">Agents</a></li>
            <li><a href="/#how">How it works</a></li>
          </>
        )}
        <li>
          <Link to="/upload" className={styles.ctaLink}>
            Upload Screenplay
          </Link>
        </li>
      </ul>
    </nav>
  );
}
