import type { DirectorScene } from '@/lib/director-api'
import type { LocationCandidate } from '@/lib/location-api'
import type { SchedulerAgentOutput } from '@/lib/scheduler-api'
import type { BudgetAgentOutput } from '@/lib/budget-api'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1'

export type RiskCategory =
  | 'Weather'
  | 'Permits'
  | 'Budget'
  | 'Scheduling'
  | 'Safety'

export type RiskSeverity = 'low' | 'medium' | 'high'

export type RiskItem = {
  id: string
  title: string
  category: RiskCategory
  severity: RiskSeverity
  scope: string
  likelihood: number
  impact: string
  recommendation: string
}

export type RiskAgentOutput = {
  risks: RiskItem[]
}

export type RiskGenerateRequest = {
  scenes: DirectorScene[]
  selected_locations: LocationCandidate[]
  schedule: SchedulerAgentOutput | null
  budget: BudgetAgentOutput | null
  user_id: string
}

export async function generateRisk(
  request: RiskGenerateRequest,
): Promise<RiskAgentOutput> {
  const response = await fetch(
    `${API_BASE_URL}/risk/generate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    },
  )

  if (!response.ok) {
    const body = await response.json().catch(() => null)

    throw new Error(
      body?.detail ??
        `Risk assessment failed with status ${response.status}.`,
    )
  }

  return response.json() as Promise<RiskAgentOutput>
}
