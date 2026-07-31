import { Link } from 'react-router-dom';
import styles from './LandingPage.module.css';

/* ── Data ────────────────────────────────────────────────────────────────── */
const AGENTS = [
  {
    id: 'script',
    icon: '📜',
    name: 'Script Analysis Agent',
    desc: 'Parses your screenplay to extract scenes, characters, locations, and narrative arcs with deep NLP understanding.',
    tag: 'NLP · Story Intelligence',
    iconBg: 'rgba(139, 92, 246, 0.15)',
    iconBorder: 'rgba(139, 92, 246, 0.30)',
    tagBg: 'rgba(139, 92, 246, 0.10)',
    tagBorder: 'rgba(139, 92, 246, 0.28)',
    tagColor: '#a78bfa',
    cardGlow: 'rgba(139, 92, 246, 0.08)',
  },
  {
    id: 'budget',
    icon: '💰',
    name: 'Budget Estimation Agent',
    desc: 'Generates detailed production budgets — cast, crew, locations, VFX, and post-production — tuned to your script.',
    tag: 'Finance · Cost Modelling',
    iconBg: 'rgba(34, 197, 94, 0.12)',
    iconBorder: 'rgba(34, 197, 94, 0.25)',
    tagBg: 'rgba(34, 197, 94, 0.08)',
    tagBorder: 'rgba(34, 197, 94, 0.25)',
    tagColor: '#4ade80',
    cardGlow: 'rgba(34, 197, 94, 0.07)',
  },
  {
    id: 'casting',
    icon: '🎭',
    name: 'Casting Director Agent',
    desc: 'Recommends talent profiles for each character role, factoring in genre, budget range, and audience demographics.',
    tag: 'Talent · Role Matching',
    iconBg: 'rgba(251, 146, 60, 0.12)',
    iconBorder: 'rgba(251, 146, 60, 0.25)',
    tagBg: 'rgba(251, 146, 60, 0.08)',
    tagBorder: 'rgba(251, 146, 60, 0.25)',
    tagColor: '#fb923c',
    cardGlow: 'rgba(251, 146, 60, 0.07)',
  },
  {
    id: 'location',
    icon: '📍',
    name: 'Location Scout Agent',
    desc: 'Identifies optimal filming locations worldwide, surfacing permit requirements, logistics, and cost comparisons.',
    tag: 'Geo · Logistics',
    iconBg: 'rgba(56, 189, 248, 0.12)',
    iconBorder: 'rgba(56, 189, 248, 0.25)',
    tagBg: 'rgba(56, 189, 248, 0.08)',
    tagBorder: 'rgba(56, 189, 248, 0.25)',
    tagColor: '#38bdf8',
    cardGlow: 'rgba(56, 189, 248, 0.07)',
  },
  {
    id: 'schedule',
    icon: '🗓️',
    name: 'Production Scheduler',
    desc: 'Builds optimised shoot schedules, resolves location and cast conflicts, and outputs a day-out-of-days report.',
    tag: 'Planning · Scheduling',
    iconBg: 'rgba(244, 63, 94, 0.12)',
    iconBorder: 'rgba(244, 63, 94, 0.25)',
    tagBg: 'rgba(244, 63, 94, 0.08)',
    tagBorder: 'rgba(244, 63, 94, 0.25)',
    tagColor: '#fb7185',
    cardGlow: 'rgba(244, 63, 94, 0.07)',
  },
  {
    id: 'market',
    icon: '📊',
    name: 'Market Analysis Agent',
    desc: 'Forecasts box-office potential, target audience segments, and distribution strategies from comparable titles.',
    tag: 'Market · Distribution',
    iconBg: 'rgba(234, 179, 8, 0.12)',
    iconBorder: 'rgba(234, 179, 8, 0.25)',
    tagBg: 'rgba(234, 179, 8, 0.08)',
    tagBorder: 'rgba(234, 179, 8, 0.25)',
    tagColor: '#facc15',
    cardGlow: 'rgba(234, 179, 8, 0.07)',
  },
];

const STEPS = [
  {
    num: '01',
    icon: '📄',
    title: 'Upload Screenplay',
    desc: 'Drop your .pdf or .fdx screenplay file into CinePilot.',
  },
  {
    num: '02',
    icon: '🤖',
    title: 'Agents Activate',
    desc: 'Six specialised AI agents parse and analyse every element in parallel.',
  },
  {
    num: '03',
    icon: '⚡',
    title: 'Insights Generated',
    desc: 'Each agent produces structured reports, estimates, and recommendations.',
  },
  {
    num: '04',
    icon: '📦',
    title: 'Export Package',
    desc: 'Download your full production package as PDF, JSON, or share a live link.',
  },
];

const STATS = [
  { value: '6', label: 'AI Agents' },
  { value: '<60s', label: 'Analysis Time' },
  { value: '100+', label: 'Data Points' },
  { value: '∞', label: 'Screenplays' },
];

/* ── Component ────────────────────────────────────────────────────────────── */
export default function LandingPage() {
  return (
    <div className={styles.page}>

      {/* NAV */}
      <nav className={styles.nav}>
        <Link to="/" className={styles.navBrand}>
          <span className={styles.navLogo}>🎬</span>
          <span className={styles.navTitle}>CinePilot AI</span>
        </Link>
        <ul className={styles.navLinks}>
          <li><a href="#agents">Agents</a></li>
          <li><a href="#how">How it works</a></li>
          <li>
            <Link to="/upload" className={styles.navCta}>
              Upload Screenplay
            </Link>
          </li>
        </ul>
      </nav>

      {/* HERO */}
      <section className={styles.hero}>
        <div className={styles.heroBadge}>
          <span className={styles.heroBadgeDot} />
          Google Agentic Cinema Hackathon
        </div>

        <h1 className={styles.heroTitle}>
          From Script to Screen
          <br />
          <span className={styles.heroAccent}>Powered by AI Agents</span>
        </h1>

        <p className={styles.heroSubtitle}>
          Upload your screenplay and watch six specialised AI agents instantly
          generate budgets, casting suggestions, location scouting reports,
          schedules, and market analysis — all in under a minute.
        </p>

        <div className={styles.heroActions}>
          <Link to="/upload" className={styles.btnPrimary}>
            <span>📄</span> Upload Screenplay
          </Link>
          <a href="#agents" className={styles.btnSecondary}>
            <span>⚡</span> Explore Agents
          </a>
        </div>
      </section>

      {/* STATS */}
      <div className={styles.statsStrip}>
        {STATS.map((s) => (
          <div key={s.label} className={styles.statItem}>
            <span className={styles.statValue}>{s.value}</span>
            <span className={styles.statLabel}>{s.label}</span>
          </div>
        ))}
      </div>

      {/* AGENT CARDS */}
      <section id="agents" className={styles.section}>
        <div className={styles.sectionHeader}>
          <p className={styles.sectionEyebrow}>Multi-Agent Architecture</p>
          <h2 className={styles.sectionTitle}>Your AI Production Team</h2>
          <p className={styles.sectionDesc}>
            Each agent is purpose-built for a critical film-making discipline,
            working in parallel to deliver a complete pre-production package.
          </p>
        </div>

        <div className={styles.agentsGrid}>
          {AGENTS.map((agent) => (
            <div
              key={agent.id}
              className={styles.agentCard}
              style={{ '--card-glow': agent.cardGlow }}
            >
              <div
                className={styles.agentIconWrap}
                style={{
                  '--icon-bg': agent.iconBg,
                  '--icon-border': agent.iconBorder,
                }}
              >
                {agent.icon}
              </div>
              <h3 className={styles.agentName}>{agent.name}</h3>
              <p className={styles.agentDesc}>{agent.desc}</p>
              <span
                className={styles.agentTag}
                style={{
                  '--tag-bg': agent.tagBg,
                  '--tag-border': agent.tagBorder,
                  '--tag-color': agent.tagColor,
                }}
              >
                {agent.tag}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className={styles.section} style={{ paddingTop: 0 }}>
        <div className={styles.sectionHeader}>
          <p className={styles.sectionEyebrow}>Workflow</p>
          <h2 className={styles.sectionTitle}>How It Works</h2>
          <p className={styles.sectionDesc}>
            Four steps from raw screenplay to a fully packaged production brief.
          </p>
        </div>

        <div className={styles.stepsGrid}>
          {STEPS.map((step) => (
            <div key={step.num} className={styles.stepCard}>
              <p className={styles.stepNumber}>Step {step.num}</p>
              <span className={styles.stepIcon}>{step.icon}</span>
              <h3 className={styles.stepTitle}>{step.title}</h3>
              <p className={styles.stepDesc}>{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaCard}>
          <h2 className={styles.ctaTitle}>Ready to Produce?</h2>
          <p className={styles.ctaDesc}>
            Drop your screenplay and let the agents do the heavy lifting. No
            account required — just pure AI-powered pre-production intelligence.
          </p>
          <Link to="/upload" className={styles.btnPrimary}>
            <span>🎬</span> Start with Your Screenplay
          </Link>
        </div>
      </section>

      {/* FOOTER */}
      <footer className={styles.footer}>
        <span className={styles.footerBrand}>🎬 CinePilot AI</span>
        <span className={styles.footerNote}>
          Built for the Google Agentic Cinema Hackathon
        </span>
      </footer>

    </div>
  );
}
