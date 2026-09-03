import type { DirectorScene } from '@/lib/director-api'
import type { LocationCandidate } from '@/lib/location-api'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1'

export type BudgetConstraintsPayload = {
  target_budget: number
  currency: string
  additional_constraints: string
}

export type BudgetGenerateRequest = {
  scenes: DirectorScene[]
  selected_locations: LocationCandidate[]
  total_shoot_days: number | null
  constraints: BudgetConstraintsPayload
  user_id: string
}

export type BudgetLineItem = {
  key:
    | 'locations'
    | 'equipment'
    | 'crew'
    | 'transportation'
    | 'contingency'
  label: string
  estimated_amount: number
  note: string
}

export type BudgetAgentOutput = {
  line_items: BudgetLineItem[]
  total_estimated_amount: number
  currency: string
}

export async function generateBudget(
  request: BudgetGenerateRequest,
): Promise<BudgetAgentOutput> {
  const response = await fetch(
    `${API_BASE_URL}/budget/generate`,
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
        `Budget generation failed with status ${response.status}.`,
    )
  }

  return response.json() as Promise<BudgetAgentOutput>
}
