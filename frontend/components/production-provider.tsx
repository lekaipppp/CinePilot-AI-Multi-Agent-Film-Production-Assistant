'use client'

import * as React from 'react'
import {
  AGENT_SEQUENCE,
  type AgentKey,
  type AgentStatus,
} from '@/lib/production-data'
import { analyzeScreenplay, type DirectorAnalysis } from '@/lib/director-api'
import { generateSchedule, type SchedulerAgentOutput } from '@/lib/scheduler-api'
import { generateBudget, type BudgetAgentOutput } from '@/lib/budget-api'
import type { LocationCandidate } from '@/lib/location-api'

type AgentState = Record<AgentKey, AgentStatus>

const IDLE_AGENTS: AgentState = {
  director: 'idle',
  location: 'idle',
  scheduler: 'idle',
  budget: 'idle',
  risk: 'idle',
}

const COMPLETE_AGENTS: AgentState = {
  director: 'complete',
  location: 'complete',
  scheduler: 'complete',
  budget: 'complete',
  risk: 'complete',
}

const DEFAULT_BUDGET_CURRENCY = 'EUR'

type PendingLocationBudgetOverride = {
  amount: number
  currency: string
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
  pendingLocationBudgetOverride: PendingLocationBudgetOverride | null
  directorAnalysis: DirectorAnalysis | null
  analysisError: string | null
  scheduleResult: SchedulerAgentOutput | null
  scheduleError: string | null
  selectedLocationsByScene: Record<number, LocationCandidate>
  allScenesHaveSelectedLocation: boolean
  setScriptText: (value: string) => void
  setFileName: (value: string | null) => void
  startAnalysis: () => Promise<boolean>
  runScheduler: (targetShootDays: number, additionalConstraints: string) => Promise<boolean>
  runBudget: (
    targetBudget: number,
    currency: string,
    additionalConstraints: string,
  ) => Promise<boolean>
  confirmLocationForScene: (sceneNumber: number, candidate: LocationCandidate) => void
  clearPendingLocationBudgetOverride: () => void
  reset: () => void
  setBudgetValue: (key: string, value: number) => void
  rerunPlan: () => void
}

const ProductionContext = React.createContext<ProductionContextValue | null>(null)

export function ProductionProvider({ children }: { children: React.ReactNode }) {
  const [analyzed, setAnalyzed] = React.useState(false)
  const [agents, setAgents] = React.useState<AgentState>(IDLE_AGENTS)
  const [scriptText, setScriptText] = React.useState('')
  const [fileName, setFileName] = React.useState<string | null>(null)
  const [budgetResult, setBudgetResult] = React.useState<BudgetAgentOutput | null>(null)
  const [budgetError, setBudgetError] = React.useState<string | null>(null)
  const [budgetOverrides, setBudgetOverrides] = React.useState<Record<string, number>>({})
  const [budgetDirty, setBudgetDirty] = React.useState(false)
  const [budgetCurrency, setBudgetCurrency] = React.useState(DEFAULT_BUDGET_CURRENCY)
  const [budgetAdditionalConstraints, setBudgetAdditionalConstraints] = React.useState('')
  const [pendingLocationBudgetOverride, setPendingLocationBudgetOverride] =
    React.useState<PendingLocationBudgetOverride | null>(null)
  const [directorAnalysis, setDirectorAnalysis] = React.useState<DirectorAnalysis | null>(null)
  const [analysisError, setAnalysisError] = React.useState<string | null>(null)
  const [scheduleResult, setScheduleResult] = React.useState<SchedulerAgentOutput | null>(null)
  const [scheduleError, setScheduleError] = React.useState<string | null>(null)
  const [selectedLocationsByScene, setSelectedLocationsByScene] = React.useState<
    Record<number, LocationCandidate>
  >({})

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
          selected_locations: Object.values(selectedLocationsByScene),
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

  const confirmLocationForScene = React.useCallback(
    (sceneNumber: number, candidate: LocationCandidate) => {
      setSelectedLocationsByScene((previous) => ({
        ...previous,
        [sceneNumber]: candidate,
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

  const reset = React.useCallback(() => {
    setAnalyzed(false)
    setAgents(IDLE_AGENTS)
    setScriptText('')
    setFileName(null)
    setBudgetResult(null)
    setBudgetError(null)
    setBudgetOverrides({})
    setBudgetDirty(false)
    setBudgetCurrency(DEFAULT_BUDGET_CURRENCY)
    setBudgetAdditionalConstraints('')
    setPendingLocationBudgetOverride(null)
    setDirectorAnalysis(null)
    setAnalysisError(null)
    setScheduleResult(null)
    setScheduleError(null)
    setSelectedLocationsByScene({})
  }, [])

  const setBudgetValue = React.useCallback((key: string, value: number) => {
    setBudgetOverrides((prev) => ({ ...prev, [key]: value }))
    setBudgetDirty(true)
  }, [])

  const rerunPlan = React.useCallback(() => {
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

    const newTargetBudget = budgetResult.line_items.reduce(
      (sum, item) => sum + effectiveAmount(item.key, item.estimated_amount),
      0,
    )

    void runBudget(newTargetBudget, budgetResult.currency, budgetAdditionalConstraints)
  }, [budgetResult, budgetOverrides, budgetAdditionalConstraints, directorAnalysis, runBudget])

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
    pendingLocationBudgetOverride,
    directorAnalysis,
    analysisError,
    scheduleResult,
    scheduleError,
    selectedLocationsByScene,
    allScenesHaveSelectedLocation,
    setScriptText,
    setFileName,
    startAnalysis,
    runScheduler,
    runBudget,
    confirmLocationForScene,
    clearPendingLocationBudgetOverride,
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
