import type { DirectorScene } from '@/lib/director-api'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export type LocationRequirementsPayload = {
  preferred_region: string
  maximum_day_rate: number
  currency: string
  maximum_distance_km: number
  environment:
    | 'Interior'
    | 'Exterior'
    | 'Interior/Exterior'
    | 'Either'
  permit_preference:
    | 'any'
    | 'permit-free-preferred'
    | 'permit-free-required'
  location_type: 'either' | 'practical' | 'studio'
  filming_date: string | null
  additional_requirements: string
}

export type LocationSearchRequest = {
  scene: DirectorScene
  user_requirements: LocationRequirementsPayload
  user_id: string
}

export type LocationCandidate = {
  location_id: string
  place_name: string
  address: string | null
  latitude: number | null
  longitude: number | null
  price: number | null
  currency: string | null
  price_unit: 'hour' | 'day' | 'week' | 'unknown' | null
  availability_status:
    | 'publicly_available'
    | 'publicly_unavailable'
    | 'requires_confirmation'
    | 'unknown'
  availability_note: string | null
  image_urls: string[]
  amenities: string[]
  match_score: number
  match_reason: string
  source_url: string
  source_excerpt: string | null
}

export type SceneLocationRecommendation = {
  scene_number: number
  scene_heading: string
  scene_setting: string | null
  candidates: LocationCandidate[]
}

export type LocationAgentOutput = {
  scene_recommendations: SceneLocationRecommendation[]
}

export async function searchLocations(
  request: LocationSearchRequest,
): Promise<LocationAgentOutput> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/locations/search`,
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
        `Location search failed with status ${response.status}.`,
    )
  }

  return response.json() as Promise<LocationAgentOutput>
}