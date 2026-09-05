import type { DirectorScene } from '@/lib/director-api'
import type { LocationCandidate } from '@/lib/location-api'
import type { SchedulerAgentOutput } from '@/lib/scheduler-api'
import type { BudgetAgentOutput } from '@/lib/budget-api'
import type { RiskAgentOutput } from '@/lib/risk-api'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1'

export type ReportAgentOutput = {
  executive_summary: string
  highlights: string[]
}

export type ReportGenerateRequest = {
  scenes: DirectorScene[]
  selected_locations: LocationCandidate[]
  schedule: SchedulerAgentOutput | null
  budget: BudgetAgentOutput | null
  risk: RiskAgentOutput | null
  user_id: string
}

export async function generateReport(
  request: ReportGenerateRequest,
): Promise<ReportAgentOutput> {
  const response = await fetch(
    `${API_BASE_URL}/report/generate`,
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
        `Report generation failed with status ${response.status}.`,
    )
  }

  return response.json() as Promise<ReportAgentOutput>
}
