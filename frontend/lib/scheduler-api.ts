import type { DirectorScene } from '@/lib/director-api'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1'

export type SchedulerConstraintsPayload = {
  target_shoot_days: number
  additional_constraints: string
}

export type SchedulerGenerateRequest = {
  scenes: DirectorScene[]
  constraints: SchedulerConstraintsPayload
  user_id: string
}

export type ScheduleBlock = {
  scene_number: number
  scene_heading: string
  shoot_day: number
  call_time: string
  interior_exterior:
    | 'Interior'
    | 'Exterior'
    | 'Interior/Exterior'
    | 'Unspecified'
  time_of_day: string | null
  location_name: string | null
  cast_needed: string[]
  has_conflict: boolean
  conflict_reason: string | null
}

export type SchedulingConstraint = {
  kind: 'actor' | 'crew' | 'weather'
  description: string
  severity: 'low' | 'medium' | 'high'
  affected_scene_numbers: number[]
}

export type SchedulerAgentOutput = {
  schedule: ScheduleBlock[]
  constraints: SchedulingConstraint[]
  total_shoot_days: number
  night_block_count: number
}

export async function generateSchedule(
  request: SchedulerGenerateRequest,
): Promise<SchedulerAgentOutput> {
  const response = await fetch(
    `${API_BASE_URL}/scheduler/generate`,
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
        `Schedule generation failed with status ${response.status}.`,
    )
  }

  return response.json() as Promise<SchedulerAgentOutput>
}
