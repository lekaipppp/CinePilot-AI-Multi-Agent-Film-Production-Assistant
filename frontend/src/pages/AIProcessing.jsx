import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import NavBar from '../components/NavBar';
import styles from './AIProcessing.module.css';

/* ── Mock data ───────────────────────────────────────────────────────────── */
const AGENTS = [
  {
    id: 'parser',
    icon: '📜',
    name: 'Script Parser',
    tag: 'Extraction · Metadata',
    status: 'complete',
    progress: 100,
    detail: 'Extracting screenplay text, scenes, characters and metadata.',
    iconBg: 'rgba(139, 92, 246, 0.15)',
    iconBorder: 'rgba(139, 92, 246, 0.30)',
    accentColor: '#a78bfa',
  },
  {
    id: 'director',
    icon: '🎬',
    name: 'Director Agent',
    tag: 'Story · Cinematic Insights',
    status: 'active',
    progress: 55,
    detail: 'Analyzing story structure, scenes and cinematic insights.',
    iconBg: 'rgba(34, 197, 94, 0.12)',
    iconBorder: 'rgba(34, 197, 94, 0.25)',
    accentColor: '#4ade80',
  },
  {
    id: 'scheduler',
    icon: '🗓️',
    name: 'Scheduler Agent',
    tag: 'Planning · Scheduling',
    status: 'waiting',
    progress: 0,
    detail: 'Preparing an optimized shooting schedule.',
    iconBg: 'rgba(56, 189, 248, 0.12)',
    iconBorder: 'rgba(56, 189, 248, 0.25)',
    accentColor: '#38bdf8',
  },
  {
    id: 'budget',
    icon: '💰',
    name: 'Budget Agent',
    tag: 'Finance · Cost Modelling',
    status: 'waiting',
    progress: 0,
    detail: 'Estimating production costs.',
    iconBg: 'rgba(251, 146, 60, 0.12)',
    iconBorder: 'rgba(251, 146, 60, 0.25)',
    accentColor: '#fb923c',
  },
  {
    id: 'risk',
    icon: '⚠️',
    name: 'Risk Agent',
    tag: 'Risk · Production Safety',
    status: 'waiting',
    progress: 0,
    detail: 'Detecting scheduling and production risks.',
    iconBg: 'rgba(244, 63, 94, 0.12)',
    iconBorder: 'rgba(244, 63, 94, 0.25)',
    accentColor: '#fb7185',
  },
  {
    id: 'producer',
    icon: '🎥',
    name: 'Producer Agent',
    tag: 'Synthesis · Final Plan',
    status: 'waiting',
    progress: 0,
    detail: 'Combining all agent outputs into the final production plan.',
    iconBg: 'rgba(234, 179, 8, 0.12)',
    iconBorder: 'rgba(234, 179, 8, 0.25)',
    accentColor: '#facc15',
  },
];

const ACTIVITY_FEED = [
  { id: 1, time: '0:31', icon: '✅', text: 'Script Parser completed — screenplay fully parsed.' },
  { id: 2, time: '0:27', icon: '🔍', text: 'Characters extracted — 8 named roles identified.' },
  { id: 3, time: '0:22', icon: '🎬', text: 'Director Agent started — analyzing story structure.' },
  { id: 4, time: '0:18', icon: '📋', text: 'Scene breakdown in progress — 42 scenes identified.' },
  { id: 5, time: '0:12', icon: '🌐', text: 'Cinematic tone analysis — 60% drama, 25% action, 15% comedy.' },
  { id: 6, time: '0:06', icon: '⏳', text: 'Scheduler, Budget and Risk agents queued — awaiting Director.' },
  { id: 7, time: '0:01', icon: '📄', text: 'Screenplay "The Last Horizon" uploaded — 112 pages parsed.' },
];

const STATUS_META = {
  complete: { label: 'Complete', color: '#4ade80', bg: 'rgba(34,197,94,0.10)',       border: 'rgba(34,197,94,0.25)' },
  active:   { label: 'Running',  color: '#c084fc', bg: 'rgba(139,92,246,0.10)',      border: 'rgba(139,92,246,0.28)' },
  waiting:  { label: 'Waiting',  color: '#64748b', bg: 'rgba(100,116,139,0.08)',     border: 'rgba(100,116,139,0.20)' },
};

/* ── Component ────────────────────────────────────────────────────────────── */
export default function AIProcessing() {
  // Simulated overall progress that ticks up from the initial mock value
  const [overallProgress, setOverallProgress] = useState(33);
  const [elapsed, setElapsed] = useState(23);

  useEffect(() => {
    const tick = setInterval(() => {
      setOverallProgress((p) => Math.min(p + 0.4, 99));
      setElapsed((s) => s + 1);
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  const remaining = Math.max(0, Math.round((100 - overallProgress) / 0.4));
  const remainingStr =
    remaining > 60
      ? `${Math.ceil(remaining / 60)}m ${remaining % 60}s`
      : `${remaining}s`;

  return (
    <div className={styles.page}>

      {/* NAV */}
      <NavBar backTo="/upload" backLabel="Upload" />

      {/* MAIN */}
      <main className={styles.main}>

        {/* ── Page header ── */}
        <header className={styles.pageHeader}>
          <div className={styles.headerBadge}>
            <span className={styles.pulseDot} />
            Processing in Progress
          </div>
          <h1 className={styles.pageTitle}>
            Analyzing your <span className={styles.accent}>screenplay…</span>
          </h1>
          <p className={styles.pageDesc}>
            Six AI agents are running in parallel — sit back while CinePilot
            assembles your full pre-production package.
          </p>
        </header>

        {/* ── Overall progress ── */}
        <section className={styles.overallCard}>
          <div className={styles.overallTop}>
            <span className={styles.overallLabel}>Overall Progress</span>
            <span className={styles.overallPct}>{Math.floor(overallProgress)}%</span>
          </div>
          <div className={styles.progressTrack}>
            <div
              className={styles.progressFill}
              style={{ width: `${overallProgress}%` }}
            />
          </div>
          <div className={styles.overallMeta}>
            <span>⏱ {Math.floor(elapsed / 60)}m {elapsed % 60}s elapsed</span>
            <span>~{remainingStr} remaining</span>
          </div>
        </section>

        {/* ── Two-column layout ── */}
        <div className={styles.columns}>

          {/* ── Agent cards ── */}
          <section className={styles.agentsSection}>
            <p className={styles.colLabel}>AI Agents</p>
            <div className={styles.agentsGrid}>
              {AGENTS.map((agent) => {
                const meta = STATUS_META[agent.status];
                return (
                  <div
                    key={agent.id}
                    className={`${styles.agentCard} ${agent.status === 'waiting' ? styles.agent_queued : styles[`agent_${agent.status}`]}`}
                  >
                    <div className={styles.agentCardTop}>
                      <div
                        className={styles.agentIcon}
                        style={{
                          background: agent.iconBg,
                          border: `1px solid ${agent.iconBorder}`,
                        }}
                      >
                        {agent.icon}
                      </div>
                      <div className={styles.agentInfo}>
                        <span className={styles.agentName}>{agent.name}</span>
                        <span className={styles.agentTag}>{agent.tag}</span>
                      </div>
                      <span
                        className={styles.statusBadge}
                        style={{
                          color: meta.color,
                          background: meta.bg,
                          border: `1px solid ${meta.border}`,
                        }}
                      >
                        {agent.status === 'active' && (
                          <span className={styles.spinnerDot} style={{ background: meta.color }} />
                        )}
                        {meta.label}
                      </span>
                    </div>

                    {agent.status !== 'waiting' && (
                      <div className={styles.agentProgressWrap}>
                        <div className={styles.agentProgressTrack}>
                          <div
                            className={styles.agentProgressFill}
                            style={{
                              width: `${agent.progress}%`,
                              background: `linear-gradient(90deg, ${agent.accentColor}cc, ${agent.accentColor})`,
                            }}
                          />
                        </div>
                        <span className={styles.agentProgressPct}>{agent.progress}%</span>
                      </div>
                    )}

                    <p className={styles.agentDetail}>{agent.detail}</p>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── Activity feed ── */}
          <section className={styles.feedSection}>
            <p className={styles.colLabel}>Recent Activity</p>
            <div className={styles.feedCard}>
              <ul className={styles.feedList}>
                {ACTIVITY_FEED.map((item) => (
                  <li key={item.id} className={styles.feedItem}>
                    <span className={styles.feedIcon}>{item.icon}</span>
                    <span className={styles.feedText}>{item.text}</span>
                    <span className={styles.feedTime}>{item.time}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

        </div>
      </main>

      {/* FOOTER */}
      <footer className={styles.footer}>
        <span className={styles.footerBrand}>🎬 CinePilot AI</span>
        <div className={styles.footerPills}>
          <span className={styles.footerPill}>Google ADK</span>
          <span className={styles.footerPill}>Gemini 2.5</span>
          <span className={styles.footerPill}>Supabase</span>
        </div>
        <Link to="/results" className={styles.footerLink}>
          Skip to results →
        </Link>
      </footer>

    </div>
  );
}
