'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import {
  AGENT_SEQUENCE,
  type AgentKey,
  type AgentStatus,
} from '@/lib/production-data'
import { analyzeScreenplay, type DirectorAnalysis } from '@/lib/director-api'
import { generateSchedule, type SchedulerAgentOutput } from '@/lib/scheduler-api'
import { generateBudget, type BudgetAgentOutput } from '@/lib/budget-api'
import { generateRisk, type RiskAgentOutput } from '@/lib/risk-api'
import { generateReport, type ReportAgentOutput } from '@/lib/report-api'
import type { LocationCandidate } from '@/lib/location-api'
import {
  createDefaultRequirements,
  fetchLocationsForScene,
  type SceneLocationRequirements,
} from '@/lib/location-requirements'

type AgentState = Record<AgentKey, AgentStatus>

const IDLE_AGENTS: AgentState = {
  director: 'idle',
  location: 'idle',
  scheduler: 'idle',
  budget: 'idle',
  risk: 'idle',
  report: 'idle',
}

const COMPLETE_AGENTS: AgentState = {
  director: 'complete',
  location: 'complete',
  scheduler: 'complete',
  budget: 'complete',
  risk: 'complete',
  report: 'complete',
}

const DEFAULT_BUDGET_CURRENCY = 'EUR'

type PendingLocationBudgetOverride = {
  amount: number
  currency: string
}

export type LocationSelectionStatus = 'auto' | 'confirmed'

export type SelectedLocation = {
  candidate: LocationCandidate
  status: LocationSelectionStatus
}

type AutoRelocateProgress = {
  current: number
  total: number
}

type AutoRelocateSummary = {
  updated: number
  needsReview: number
}

type ProductionContextValue = {
  analyzed: boolean
  agents: AgentState
  isRunning: boolean
  activeAgent: AgentKey | null
  scriptText: string
  fileName: string | null
  budgetResult: BudgetAgentOutput | null
  budgetError: string | null
  budgetOverrides: Record<string, number>
  budgetDirty: boolean
  riskResult: RiskAgentOutput | null
  riskError: string | null
  reportResult: ReportAgentOutput | null
  reportError: string | null
  pendingLocationBudgetOverride: PendingLocationBudgetOverride | null
  directorAnalysis: DirectorAnalysis | null
  analysisError: string | null
  scheduleResult: SchedulerAgentOutput | null
  scheduleError: string | null
  selectedLocationsByScene: Record<number, SelectedLocation>
  allScenesHaveSelectedLocation: boolean
  autoRelocateRequestId: number
  autoRelocateProgress: AutoRelocateProgress | null
  autoRelocateSummary: AutoRelocateSummary | null
  requirementsByScene: Record<number, SceneLocationRequirements>
  setScriptText: (value: string) => void
  setFileName: (value: string | null) => void
  startAnalysis: () => Promise<boolean>
  runScheduler: (targetShootDays: number, additionalConstraints: string) => Promise<boolean>
  runBudget: (
    targetBudget: number,
    currency: string,
    additionalConstraints: string,
  ) => Promise<boolean>
  runRisk: () => Promise<boolean>
  runReport: () => Promise<boolean>
  confirmLocationForScene: (
    sceneNumber: number,
    candidate: LocationCandidate,
    status: LocationSelectionStatus,
  ) => void
  clearPendingLocationBudgetOverride: () => void
  bumpAutoRelocateRequest: () => void
  updateSceneRequirement: <Key extends keyof SceneLocationRequirements>(
    sceneNumber: number,
    key: Key,
    value: SceneLocationRequirements[Key],
  ) => void
  reset: () => void
  setBudgetValue: (key: string, value: number) => void
  rerunPlan: () => Promise<void>
}

const ProductionContext = React.createContext<ProductionContextValue | null>(null)

export function ProductionProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [analyzed, setAnalyzed] = React.useState(false)
  const [agents, setAgents] = React.useState<AgentState>(IDLE_AGENTS)
  const [scriptText, setScriptText] = React.useState('')
  const [fileName, setFileName] = React.useState<string | null>(null)
  const [budgetResult, setBudgetResult] = React.useState<BudgetAgentOutput | null>(null)
  const [budgetError, setBudgetError] = React.useState<string | null>(null)
  const [budgetOverrides, setBudgetOverrides] = React.useState<Record<string, number>>({})
  const [budgetDirty, setBudgetDirty] = React.useState(false)
  const [riskResult, setRiskResult] = React.useState<RiskAgentOutput | null>(null)
  const [riskError, setRiskError] = React.useState<string | null>(null)
  const [reportResult, setReportResult] = React.useState<ReportAgentOutput | null>(null)
  const [reportError, setReportError] = React.useState<string | null>(null)
  const [budgetCurrency, setBudgetCurrency] = React.useState(DEFAULT_BUDGET_CURRENCY)
  const [budgetAdditionalConstraints, setBudgetAdditionalConstraints] = React.useState('')
  const [pendingLocationBudgetOverride, setPendingLocationBudgetOverride] =
    React.useState<PendingLocationBudgetOverride | null>(null)
  const [autoRelocateRequestId, setAutoRelocateRequestId] = React.useState(0)
  const [autoRelocateProgress, setAutoRelocateProgress] =
    React.useState<AutoRelocateProgress | null>(null)
  const [autoRelocateSummary, setAutoRelocateSummary] =
    React.useState<AutoRelocateSummary | null>(null)
  const [directorAnalysis, setDirectorAnalysis] = React.useState<DirectorAnalysis | null>(null)
  const [analysisError, setAnalysisError] = React.useState<string | null>(null)
  const [scheduleResult, setScheduleResult] = React.useState<SchedulerAgentOutput | null>(null)
  const [scheduleError, setScheduleError] = React.useState<string | null>(null)
  const [lastScheduleTargetDays, setLastScheduleTargetDays] = React.useState<number | null>(null)
  const [lastScheduleConstraints, setLastScheduleConstraints] = React.useState<string | null>(null)
  const [selectedLocationsByScene, setSelectedLocationsByScene] = React.useState<
    Record<number, SelectedLocation>
  >({})
  const [requirementsByScene, setRequirementsByScene] = React.useState<
    Record<number, SceneLocationRequirements>
  >({})

  /*
   * Lives here (not in locations-workspace.tsx) so a scene's search
   * preferences — region, day rate, radius, etc. — survive navigating
   * away from /locations and back, and so the automatic re-search loop
   * (triggered from the Budget page) always has real data to work with,
   * not fresh empty defaults from a just-remounted component.
   */
  React.useEffect(() => {
    const scenes = directorAnalysis?.scenes ?? []
    if (scenes.length === 0) return

    setRequirementsByScene((current) => {
      const next = { ...current }

      for (const scene of scenes) {
        if (!next[scene.scene_number]) {
          next[scene.scene_number] = createDefaultRequirements(scene)
        }
      }

      return next
    })
  }, [directorAnalysis])

  const startAnalysis = React.useCallback(async () => {
    setAnalyzed(true)
    setAgents(IDLE_AGENTS)
    setDirectorAnalysis(null)
    setAnalysisError(null)
    setAgents((previous) => ({ ...previous, director: 'running' }))

    try {
      const result = await analyzeScreenplay(scriptText)
      setDirectorAnalysis(result)
      setAgents((previous) => ({ ...previous, director: 'complete' }))
      return true
    } catch (error) {
      setAnalyzed(false)
      setAgents(IDLE_AGENTS)
      setAnalysisError(error instanceof Error ? error.message : 'Director Agent failed.')
      return false
    }
  }, [scriptText])

  const runScheduler = React.useCallback(
    async (targetShootDays: number, additionalConstraints: string) => {
      if (!directorAnalysis || directorAnalysis.scenes.length === 0) {
        setScheduleError('Run Director analysis before generating a schedule.')
        return false
      }

      setAgents((previous) => ({ ...previous, scheduler: 'running' }))
      setScheduleError(null)

      try {
        const result = await generateSchedule({
          scenes: directorAnalysis.scenes,
          constraints: {
            target_shoot_days: targetShootDays,
            additional_constraints: additionalConstraints,
          },
          user_id: 'web_user',
        })

        setScheduleResult(result)
        setLastScheduleTargetDays(targetShootDays)
        setLastScheduleConstraints(additionalConstraints)
        setAgents((previous) => ({ ...previous, scheduler: 'complete' }))
        return true
      } catch (error) {
        setAgents((previous) => ({ ...previous, scheduler: 'idle' }))
        setScheduleError(error instanceof Error ? error.message : 'Scheduler Agent failed.')
        return false
      }
    },
    [directorAnalysis],
  )

  const runBudget = React.useCallback(
    async (targetBudget: number, currency: string, additionalConstraints: string) => {
      if (!directorAnalysis || directorAnalysis.scenes.length === 0) {
        setBudgetError('Run Director analysis before generating a budget.')
        return false
      }

      setAgents((previous) => ({ ...previous, budget: 'running' }))
      setBudgetError(null)

      try {
        const result = await generateBudget({
          scenes: directorAnalysis.scenes,
          selected_locations: Object.values(selectedLocationsByScene).map(
            (entry) => entry.candidate,
          ),
          total_shoot_days: scheduleResult?.total_shoot_days ?? null,
          constraints: {
            target_budget: targetBudget,
            currency,
            additional_constraints: additionalConstraints,
          },
          user_id: 'web_user',
        })

        setBudgetResult(result)
        setBudgetCurrency(currency)
        setBudgetAdditionalConstraints(additionalConstraints)
        // A fresh result makes any prior slider overrides (measured
        // against the old result) meaningless — clear them so the
        // sliders start back at the agent's new numbers.
        setBudgetOverrides({})
        setBudgetDirty(false)
        setAgents((previous) => ({ ...previous, budget: 'complete' }))
        return true
      } catch (error) {
        setAgents((previous) => ({ ...previous, budget: 'idle' }))
        setBudgetError(error instanceof Error ? error.message : 'Budget Agent failed.')
        return false
      }
    },
    [directorAnalysis, selectedLocationsByScene, scheduleResult],
  )

  const runRisk = React.useCallback(async () => {
    if (!directorAnalysis || directorAnalysis.scenes.length === 0) {
      setRiskError('Run Director analysis before generating a risk assessment.')
      return false
    }

    setAgents((previous) => ({ ...previous, risk: 'running' }))
    setRiskError(null)

    try {
      const result = await generateRisk({
        scenes: directorAnalysis.scenes,
        selected_locations: Object.values(selectedLocationsByScene).map(
          (entry) => entry.candidate,
        ),
        schedule: scheduleResult,
        budget: budgetResult,
        user_id: 'web_user',
      })

      setRiskResult(result)
      setAgents((previous) => ({ ...previous, risk: 'complete' }))
      return true
    } catch (error) {
      setAgents((previous) => ({ ...previous, risk: 'idle' }))
      setRiskError(error instanceof Error ? error.message : 'Risk Agent failed.')
      return false
    }
  }, [directorAnalysis, selectedLocationsByScene, scheduleResult, budgetResult])

  const runReport = React.useCallback(async () => {
    if (!directorAnalysis || directorAnalysis.scenes.length === 0) {
      setReportError('Run Director analysis before generating a report.')
      return false
    }

    setAgents((previous) => ({ ...previous, report: 'running' }))
    setReportError(null)

    try {
      const result = await generateReport({
        scenes: directorAnalysis.scenes,
        selected_locations: Object.values(selectedLocationsByScene).map(
          (entry) => entry.candidate,
        ),
        schedule: scheduleResult,
        budget: budgetResult,
        risk: riskResult,
        user_id: 'web_user',
      })

      setReportResult(result)
      setAgents((previous) => ({ ...previous, report: 'complete' }))
      return true
    } catch (error) {
      setAgents((previous) => ({ ...previous, report: 'idle' }))
      setReportError(error instanceof Error ? error.message : 'Report Agent failed.')
      return false
    }
  }, [directorAnalysis, selectedLocationsByScene, scheduleResult, budgetResult, riskResult])

  const confirmLocationForScene = React.useCallback(
    (
      sceneNumber: number,
      candidate: LocationCandidate,
      status: LocationSelectionStatus,
    ) => {
      setSelectedLocationsByScene((previous) => ({
        ...previous,
        [sceneNumber]: { candidate, status },
      }))
    },
    [],
  )

  const allScenesHaveSelectedLocation = React.useMemo(() => {
    const scenes = directorAnalysis?.scenes ?? []
    if (scenes.length === 0) return false
    return scenes.every((scene) => selectedLocationsByScene[scene.scene_number] !== undefined)
  }, [directorAnalysis, selectedLocationsByScene])

  React.useEffect(() => {
    if (!allScenesHaveSelectedLocation) return
    setAgents((previous) =>
      previous.location === 'complete' ? previous : { ...previous, location: 'complete' },
    )
  }, [allScenesHaveSelectedLocation])

  const clearPendingLocationBudgetOverride = React.useCallback(() => {
    setPendingLocationBudgetOverride(null)
  }, [])

  const bumpAutoRelocateRequest = React.useCallback(() => {
    setAutoRelocateRequestId((previous) => previous + 1)
  }, [])

  /*
   * Lives here (not in locations-workspace.tsx) so a budget-triggered
   * rerun keeps re-searching every scene even if the user navigates away
   * from /locations mid-loop — this provider never unmounts on route
   * changes, so the loop just keeps running in the background and
   * whichever page is on screen reflects progress reactively.
   */
  React.useEffect(() => {
    if (autoRelocateRequestId === 0) return

    let cancelled = false

    async function relocateAllScenes() {
      const scenes = directorAnalysis?.scenes ?? []
      let updatedCount = 0
      let needsReviewCount = 0

      for (let index = 0; index < scenes.length; index += 1) {
        if (cancelled) return

        const scene = scenes[index]
        setAutoRelocateProgress({ current: index + 1, total: scenes.length })

        const requirements =
          requirementsByScene[scene.scene_number] ?? createDefaultRequirements(scene)

        try {
          const result = await fetchLocationsForScene(scene, requirements)

          const candidates =
            result.scene_recommendations.find(
              (recommendation) => recommendation.scene_number === scene.scene_number,
            )?.candidates ?? []

          // The Location Agent is instructed to sort by match_score
          // descending, but that's a prompt instruction, not a
          // schema-enforced guarantee — sort defensively before
          // trusting candidates[0].
          const topCandidate = [...candidates].sort(
            (a, b) => b.match_score - a.match_score,
          )[0]

          if (cancelled) return

          if (topCandidate) {
            confirmLocationForScene(scene.scene_number, topCandidate, 'auto')
            updatedCount += 1
            needsReviewCount += 1
          } else {
            // Zero candidates: leave this scene unselected and count it
            // toward "needs review" — nothing to auto-pick, but it's
            // still not settled.
            needsReviewCount += 1
          }
        } catch {
          // Search failed for this scene: skip it, count it toward
          // "needs review", and continue rather than aborting the loop.
          needsReviewCount += 1
        }
      }

      if (!cancelled) {
        setAutoRelocateProgress(null)
        setAutoRelocateSummary({ updated: updatedCount, needsReview: needsReviewCount })
      }
    }

    void relocateAllScenes()

    return () => {
      cancelled = true
    }
  }, [autoRelocateRequestId])

  const updateSceneRequirement = React.useCallback(
    <Key extends keyof SceneLocationRequirements>(
      sceneNumber: number,
      key: Key,
      value: SceneLocationRequirements[Key],
    ) => {
      setRequirementsByScene((current) => {
        const scene = directorAnalysis?.scenes.find(
          (candidate) => candidate.scene_number === sceneNumber,
        )
        const existing = current[sceneNumber] ?? (scene ? createDefaultRequirements(scene) : null)

        if (!existing) return current

        return {
          ...current,
          [sceneNumber]: { ...existing, [key]: value },
        }
      })
    },
    [directorAnalysis],
  )

  const reset = React.useCallback(() => {
    setAnalyzed(false)
    setAgents(IDLE_AGENTS)
    setScriptText('')
    setFileName(null)
    setBudgetResult(null)
    setBudgetError(null)
    setBudgetOverrides({})
    setBudgetDirty(false)
    setRiskResult(null)
    setRiskError(null)
    setReportResult(null)
    setReportError(null)
    setBudgetCurrency(DEFAULT_BUDGET_CURRENCY)
    setBudgetAdditionalConstraints('')
    setPendingLocationBudgetOverride(null)
    setAutoRelocateRequestId(0)
    setAutoRelocateProgress(null)
    setAutoRelocateSummary(null)
    setDirectorAnalysis(null)
    setAnalysisError(null)
    setScheduleResult(null)
    setScheduleError(null)
    setLastScheduleTargetDays(null)
    setLastScheduleConstraints(null)
    setSelectedLocationsByScene({})
    setRequirementsByScene({})
  }, [])

  const setBudgetValue = React.useCallback((key: string, value: number) => {
    setBudgetOverrides((prev) => ({ ...prev, [key]: value }))
    setBudgetDirty(true)
  }, [])

  const rerunPlan = React.useCallback(async () => {
    if (!budgetResult || !directorAnalysis || directorAnalysis.scenes.length === 0) {
      return
    }

    const effectiveAmount = (key: string, fallback: number) =>
      budgetOverrides[key] ?? fallback

    const locationsItem = budgetResult.line_items.find((item) => item.key === 'locations')

    const newLocationsTarget = locationsItem
      ? effectiveAmount(locationsItem.key, locationsItem.estimated_amount)
      : 0

    const perSceneDayRateCap =
      directorAnalysis.scenes.length > 0
        ? newLocationsTarget / directorAnalysis.scenes.length
        : 0

    setPendingLocationBudgetOverride({
      amount: perSceneDayRateCap,
      currency: budgetResult.currency,
    })

    setAgents((prev) => ({ ...prev, location: 'idle', scheduler: 'idle' }))
    // The prior schedule and location picks were made against the old
    // budget assumptions — clear them rather than leaving stale results on
    // screen (and letting a stale location set silently re-complete).
    setScheduleResult(null)
    setScheduleError(null)
    setSelectedLocationsByScene({})
    setAutoRelocateSummary(null)

    const newTargetBudget = budgetResult.line_items.reduce(
      (sum, item) => sum + effectiveAmount(item.key, item.estimated_amount),
      0,
    )

    const budgetSucceeded = await runBudget(
      newTargetBudget,
      budgetResult.currency,
      budgetAdditionalConstraints,
    )

    // This is a hackathon demo — fully automatic is fine, so a
    // successful budget rerun also replays the Scheduler Agent with the
    // same inputs used last time (if a schedule existed before), and
    // then signals locations-workspace.tsx to re-search and
    // auto-select a location for every scene, instead of leaving
    // Location/Scheduler idle for the user to re-trigger by hand.
    if (budgetSucceeded && lastScheduleTargetDays !== null) {
      await runScheduler(lastScheduleTargetDays, lastScheduleConstraints ?? '')
    }

    bumpAutoRelocateRequest()

    // Send the user to Locations so they watch the re-search happen —
    // this is the one step in the cascade that produces results worth a
    // human glance. The loop itself (above) doesn't depend on this
    // navigation; it keeps running in the provider regardless of which
    // page is mounted, so this is purely about vantage point, not a
    // requirement for the loop to work.
    router.push('/locations')
  }, [
    budgetResult,
    budgetOverrides,
    budgetAdditionalConstraints,
    directorAnalysis,
    lastScheduleTargetDays,
    lastScheduleConstraints,
    router,
    runBudget,
    runScheduler,
    bumpAutoRelocateRequest,
  ])

  const activeAgent = React.useMemo(
    () => AGENT_SEQUENCE.find(({ key }) => agents[key] === 'running')?.key ?? null,
    [agents],
  )

  const value: ProductionContextValue = {
    analyzed,
    agents: analyzed ? agents : IDLE_AGENTS,
    isRunning: activeAgent !== null,
    activeAgent,
    scriptText,
    fileName,
    budgetResult,
    budgetError,
    budgetOverrides,
    budgetDirty,
    riskResult,
    riskError,
    reportResult,
    reportError,
    pendingLocationBudgetOverride,
    directorAnalysis,
    analysisError,
    scheduleResult,
    scheduleError,
    selectedLocationsByScene,
    allScenesHaveSelectedLocation,
    autoRelocateRequestId,
    autoRelocateProgress,
    autoRelocateSummary,
    requirementsByScene,
    setScriptText,
    setFileName,
    startAnalysis,
    runScheduler,
    runBudget,
    runRisk,
    runReport,
    confirmLocationForScene,
    clearPendingLocationBudgetOverride,
    bumpAutoRelocateRequest,
    updateSceneRequirement,
    reset,
    setBudgetValue,
    rerunPlan,
  }

  return <ProductionContext.Provider value={value}>{children}</ProductionContext.Provider>
}

export function useProduction() {
  const ctx = React.useContext(ProductionContext)
  if (!ctx) throw new Error('useProduction must be used inside ProductionProvider')
  return ctx
}

export { COMPLETE_AGENTS }
