import type { DirectorScene } from '@/lib/director-api'

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
