export type DirectorScene = {
  scene_number: number
  scene_heading: string
  location_setting: string | null
  interior_exterior: 'Interior' | 'Exterior' | 'Interior/Exterior' | 'Unspecified'
  time_of_day: string | null
  weather_of_scene: string | null
  characters_in_scene: string[]
  props_in_scene: string[]
  shooting_requirements: string[]
  source_evidence: string[]
  location_features: string[]
}

export type DirectorAnalysis = {
  scenes: DirectorScene[]
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

export async function analyzeScreenplay(screenplayText: string): Promise<DirectorAnalysis> {
  const response = await fetch(`${API_BASE_URL}/screenplay/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ screenplay_text: screenplayText, user_id: 'web_user' }),
  })

  if (!response.ok) {
    let message = `Director Agent failed (${response.status})`
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Keep the status-based fallback when the server did not return JSON.
    }
    throw new Error(message)
  }

  return (await response.json()) as DirectorAnalysis
}
