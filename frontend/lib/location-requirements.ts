import type { DirectorScene } from '@/lib/director-api'
import {
  searchLocations,
  type LocationAgentOutput,
} from '@/lib/location-api'

export type EnvironmentPreference =
  | 'Interior'
  | 'Exterior'
  | 'Interior/Exterior'
  | 'Either'

export type PermitPreference =
  | 'any'
  | 'permit-free-preferred'
  | 'permit-free-required'

export type SceneLocationRequirements = {
  preferredRegion: string
  maximumDayRate: string
  currency: string
  searchRadiusKm: string
  environment: EnvironmentPreference
  permitPreference: PermitPreference
  practicalOrStudio: 'either' | 'practical' | 'studio'
  filmingDate: string
  additionalRequirements: string
}

export function createDefaultRequirements(
  scene: DirectorScene,
): SceneLocationRequirements {
  const environment =
    scene.interior_exterior === 'Unspecified'
      ? 'Either'
      : scene.interior_exterior

  return {
    preferredRegion: '',
    maximumDayRate: '1500',
    currency: 'EUR',
    searchRadiusKm: '50',
    environment,
    permitPreference: 'any',
    practicalOrStudio: 'either',
    filmingDate: '',
    additionalRequirements: '',
  }
}

/*
 * Shared by the manual "Find locations for Scene N" button
 * (locations-workspace.tsx) and the automatic re-search loop
 * (production-provider.tsx) — the only place the LocationSearchRequest
 * payload is built, so the two flows can never drift apart.
 */
export function fetchLocationsForScene(
  scene: DirectorScene,
  requirements: SceneLocationRequirements,
): Promise<LocationAgentOutput> {
  return searchLocations({
    scene,
    user_requirements: {
      preferred_region: requirements.preferredRegion.trim(),
      maximum_day_rate: Number(requirements.maximumDayRate),
      currency: requirements.currency,
      maximum_distance_km: Number(requirements.searchRadiusKm),
      environment: requirements.environment,
      permit_preference: requirements.permitPreference,
      location_type: requirements.practicalOrStudio,
      filming_date: requirements.filmingDate || null,
      additional_requirements: requirements.additionalRequirements.trim(),
    },
    user_id: 'web_user',
  })
}
