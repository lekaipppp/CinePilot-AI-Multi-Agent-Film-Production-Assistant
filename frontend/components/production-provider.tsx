'use client'

import * as React from 'react'
import {
  AGENT_SEQUENCE,
  BUDGET_CATEGORIES,
  type AgentKey,
  type AgentStatus,
} from '@/lib/production-data'
import { analyzeScreenplay, type DirectorAnalysis } from '@/lib/director-api'

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

type BudgetState = Record<string, number>

const INITIAL_BUDGET: BudgetState = Object.fromEntries(
  BUDGET_CATEGORIES.map((c) => [c.key, c.amount]),
)

type ProductionContextValue = {
  analyzed: boolean
  agents: AgentState
  isRunning: boolean
  activeAgent: AgentKey | null
  scriptText: string
  fileName: string | null
  budget: BudgetState
  budgetTotal: number
  budgetDirty: boolean
  directorAnalysis: DirectorAnalysis | null
  analysisError: string | null
  setScriptText: (value: string) => void
  setFileName: (value: string | null) => void
  startAnalysis: () => Promise<boolean>
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
  const [budget, setBudget] = React.useState<BudgetState>(INITIAL_BUDGET)
  const [budgetDirty, setBudgetDirty] = React.useState(false)
  const [directorAnalysis, setDirectorAnalysis] = React.useState<DirectorAnalysis | null>(null)
  const [analysisError, setAnalysisError] = React.useState<string | null>(null)
  const timers = React.useRef<ReturnType<typeof setTimeout>[]>([])

  const clearTimers = React.useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])

  React.useEffect(() => clearTimers, [clearTimers])

  const runPipeline = React.useCallback(
    (from: number) => {
      clearTimers()
      const step = 900
      AGENT_SEQUENCE.forEach(({ key }, index) => {
        if (index < from) return
        const order = index - from
        timers.current.push(
          setTimeout(() => {
            setAgents((prev) => ({ ...prev, [key]: 'running' }))
          }, order * step),
        )
        timers.current.push(
          setTimeout(() => {
            setAgents((prev) => ({ ...prev, [key]: 'complete' }))
          }, order * step + step - 120),
        )
      })
    },
    [clearTimers],
  )

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

  const reset = React.useCallback(() => {
    clearTimers()
    setAnalyzed(false)
    setAgents(IDLE_AGENTS)
    setScriptText('')
    setFileName(null)
    setBudget(INITIAL_BUDGET)
    setBudgetDirty(false)
    setDirectorAnalysis(null)
    setAnalysisError(null)
  }, [clearTimers])

  const setBudgetValue = React.useCallback((key: string, value: number) => {
    setBudget((prev) => ({ ...prev, [key]: value }))
    setBudgetDirty(true)
  }, [])

  const rerunPlan = React.useCallback(() => {
    setBudgetDirty(false)
    setAgents((prev) => ({ ...prev, location: 'idle', scheduler: 'idle', budget: 'idle', risk: 'idle' }))
    runPipeline(1)
  }, [runPipeline])

  const budgetTotal = React.useMemo(
    () => Object.values(budget).reduce((sum, v) => sum + v, 0),
    [budget],
  )

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
    budget,
    budgetTotal,
    budgetDirty,
    directorAnalysis,
    analysisError,
    setScriptText,
    setFileName,
    startAnalysis,
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
