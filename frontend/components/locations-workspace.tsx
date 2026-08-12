'use client'

import dynamic from 'next/dynamic'
import * as React from 'react'
import {
  Building2,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Crosshair,
  MapPin,
  Search,
  SlidersHorizontal,
  Sparkles,
} from 'lucide-react'

import { AnalysisGate } from '@/components/analysis-gate'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { useProduction } from '@/components/production-provider'
import type { DirectorScene } from '@/lib/director-api'
import {
  searchLocations,
  type LocationAgentOutput,
} from '@/lib/location-api'

const LocationMap = dynamic(
  () => import('@/components/location-map'),
  {
    ssr: false,
  },
)

type EnvironmentPreference =
  | 'Interior'
  | 'Exterior'
  | 'Interior/Exterior'
  | 'Either'

type PermitPreference =
  | 'any'
  | 'permit-free-preferred'
  | 'permit-free-required'

type SceneLocationRequirements = {
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

const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CAD']

function createDefaultRequirements(
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

function getDetectedRequirements(scene: DirectorScene): string[] {
  const requirements = [
    scene.interior_exterior !== 'Unspecified'
      ? scene.interior_exterior
      : null,
    scene.time_of_day,
    scene.weather_of_scene,
    ...scene.shooting_requirements,
  ]

  return Array.from(
    new Set(
      requirements.filter(
        (requirement): requirement is string =>
          Boolean(requirement?.trim()),
      ),
    ),
  )
}

function getSceneLabel(scene: DirectorScene): string {
  if (scene.location_setting) {
    return `Scene ${scene.scene_number} · ${scene.location_setting}`
  }

  return `Scene ${scene.scene_number}`
}

export function LocationsWorkspace() {
  const { directorAnalysis } = useProduction()
  const scenes = directorAnalysis?.scenes ?? []

  const [isSearching, setIsSearching] = React.useState(false)

  const [searchError, setSearchError] =
    React.useState<string | null>(null)

  const [locationResult, setLocationResult] =
    React.useState<LocationAgentOutput | null>(null)

  const [selectedLocationId, setSelectedLocationId] =
    React.useState<string | null>(null)

  const [activeSceneNumber, setActiveSceneNumber] =
    React.useState<number | null>(null)

  const [requirementsByScene, setRequirementsByScene] =
    React.useState<
      Record<number, SceneLocationRequirements>
    >({})

  /*
   * When Director Agent results arrive, create one independent requirements
   * form for every scene. Changing scenes will not erase the user's input.
   */
  React.useEffect(() => {
    if (scenes.length === 0) return

    setActiveSceneNumber(
      (current) => current ?? scenes[0].scene_number,
    )

    setRequirementsByScene((current) => {
      const next = { ...current }

      for (const scene of scenes) {
        if (!next[scene.scene_number]) {
          next[scene.scene_number] =
            createDefaultRequirements(scene)
        }
      }

      return next
    })
  }, [scenes])

  const activeScene =
    scenes.find(
      (scene) => scene.scene_number === activeSceneNumber,
    ) ?? scenes[0]

  const activeRequirements = activeScene
    ? requirementsByScene[activeScene.scene_number] ??
      createDefaultRequirements(activeScene)
    : null

  const activeSceneIndex = activeScene
    ? scenes.findIndex(
        (scene) =>
          scene.scene_number === activeScene.scene_number,
      )
    : -1

  const detectedRequirements = activeScene
    ? getDetectedRequirements(activeScene)
    : []

  const activeRecommendation =
    locationResult?.scene_recommendations.find(
      (recommendation) =>
        recommendation.scene_number ===
        activeScene?.scene_number,
    ) ?? null

  const activeCandidates =
    activeRecommendation?.candidates ?? []

  const updateRequirement = React.useCallback(
    <Key extends keyof SceneLocationRequirements>(
      key: Key,
      value: SceneLocationRequirements[Key],
    ) => {
      if (!activeScene) return

      setRequirementsByScene((current) => ({
        ...current,
        [activeScene.scene_number]: {
          ...(current[activeScene.scene_number] ??
            createDefaultRequirements(activeScene)),
          [key]: value,
        },
      }))
    },
    [activeScene],
  )

  const selectPreviousScene = () => {
    if (activeSceneIndex <= 0) return

    setActiveSceneNumber(
      scenes[activeSceneIndex - 1].scene_number,
    )
  }

  const selectNextScene = () => {
    if (
      activeSceneIndex < 0 ||
      activeSceneIndex >= scenes.length - 1
    ) {
      return
    }

    setActiveSceneNumber(
      scenes[activeSceneIndex + 1].scene_number,
    )
  }

  const handleSearch = async () => {
    if (!activeScene || !activeRequirements) return

    const requestPayload = {
      scene: activeScene,
      user_requirements: {
        preferred_region:
          activeRequirements.preferredRegion.trim(),

        maximum_day_rate: Number(
          activeRequirements.maximumDayRate,
        ),

        currency: activeRequirements.currency,

        maximum_distance_km: Number(
          activeRequirements.searchRadiusKm,
        ),

        environment: activeRequirements.environment,

        permit_preference:
          activeRequirements.permitPreference,

        location_type:
          activeRequirements.practicalOrStudio,

        filming_date:
          activeRequirements.filmingDate || null,

        additional_requirements:
          activeRequirements.additionalRequirements.trim(),
      },

      user_id: 'web_user',
    }

    setIsSearching(true)
    setSearchError(null)
    setLocationResult(null)
    setSelectedLocationId(null)

    try {
      const result = await searchLocations(requestPayload)

      setLocationResult(result)

      const returnedCandidates =
        result.scene_recommendations.find(
          (recommendation) =>
            recommendation.scene_number ===
            activeScene.scene_number,
        )?.candidates ?? []

      const firstMappableCandidate =
        returnedCandidates.find(
          (candidate) =>
            typeof candidate.latitude === 'number' &&
            Number.isFinite(candidate.latitude) &&
            typeof candidate.longitude === 'number' &&
            Number.isFinite(candidate.longitude),
        )

      setSelectedLocationId(
        firstMappableCandidate?.location_id ?? null,
      )
    } catch (error) {
      setSearchError(
        error instanceof Error
          ? error.message
          : 'Location search failed.',
      )
    } finally {
      setIsSearching(false)
    }
  }

  const searchDisabled =
    !activeRequirements?.preferredRegion.trim() ||
    !activeRequirements.maximumDayRate ||
    Number(activeRequirements.maximumDayRate) <= 0

  const markerCount = activeCandidates.filter(
    (candidate) =>
      typeof candidate.latitude === 'number' &&
      Number.isFinite(candidate.latitude) &&
      typeof candidate.longitude === 'number' &&
      Number.isFinite(candidate.longitude),
  ).length

  return (
    /*
     * Use the Director gate here because this form should appear as soon as
     * Director analysis is complete. The Location Agent has not run yet.
     */
    <AnalysisGate agent="director">
      {activeScene && activeRequirements ? (
        <div className="flex flex-col gap-5">
          <SceneSelector
            scenes={scenes}
            activeScene={activeScene}
            activeSceneIndex={activeSceneIndex}
            onSceneChange={setActiveSceneNumber}
            onPrevious={selectPreviousScene}
            onNext={selectNextScene}
          />

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.12fr)_minmax(340px,0.88fr)]">
            <div className="flex min-w-0 flex-col gap-5">
              <SceneSummary
                scene={activeScene}
                detectedRequirements={
                  detectedRequirements
                }
              />

              <LocationRequirementsForm
                scene={activeScene}
                requirements={activeRequirements}
                updateRequirement={updateRequirement}
                searchDisabled={searchDisabled}
                isSearching={isSearching}
                onSearch={handleSearch}
              />
            </div>

            {locationResult ? (
              <Card className="overflow-hidden border-border/60 bg-card/70 py-0 xl:sticky xl:top-24 xl:h-[calc(100vh-8rem)] xl:min-h-[620px]">
                <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <MapPin className="size-4 text-amber" />
                    Scout map
                  </div>

                  <Badge variant="outline">
                    {markerCount}{' '}
                    {markerCount === 1
                      ? 'marker'
                      : 'markers'}
                  </Badge>
                </div>

                <div className="h-[420px] xl:h-[calc(100%-3.25rem)]">
                  <LocationMap
                    candidates={activeCandidates}
                    selectedId={selectedLocationId}
                    onSelect={setSelectedLocationId}
                  />
                </div>
              </Card>
            ) : (
              <PreSearchMap
                region={
                  activeRequirements.preferredRegion
                }
                radius={
                  activeRequirements.searchRadiusKm
                }
                sceneNumber={activeScene.scene_number}
              />
            )}
          </div>

          {searchError && (
            <Card className="border-destructive/50">
              <CardContent className="pt-6 text-sm text-destructive">
                {searchError}
              </CardContent>
            </Card>
          )}

          {locationResult?.scene_recommendations.map(
            (recommendation) => (
              <Card key={recommendation.scene_number}>
                <CardHeader>
                  <CardTitle>
                    Location recommendations for Scene{' '}
                    {recommendation.scene_number}
                  </CardTitle>
                </CardHeader>

                <CardContent className="space-y-4">
                  {recommendation.candidates.length ===
                  0 ? (
                    <p>
                      No suitable locations were found.
                    </p>
                  ) : (
                    recommendation.candidates.map(
                      (candidate) => (
                        <div
                          key={candidate.location_id}
                          className={`rounded-lg border p-4 transition-colors ${
                            candidate.location_id ===
                            selectedLocationId
                              ? 'border-amber/70 bg-amber/5'
                              : 'border-border'
                          }`}
                        >
                          <div className="flex justify-between gap-4">
                            <h3 className="font-semibold">
                              {candidate.place_name}
                            </h3>

                            <Badge>
                              {candidate.match_score}%
                              match
                            </Badge>
                          </div>

                          <p className="mt-2 text-sm text-muted-foreground">
                            {candidate.address ??
                              'Address unavailable'}
                          </p>

                          <p className="mt-2 text-sm">
                            {candidate.match_reason}
                          </p>

                          <div className="mt-3 flex flex-wrap items-center gap-3">
                            {typeof candidate.latitude ===
                              'number' &&
                              Number.isFinite(
                                candidate.latitude,
                              ) &&
                              typeof candidate.longitude ===
                                'number' &&
                              Number.isFinite(
                                candidate.longitude,
                              ) && (
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() =>
                                    setSelectedLocationId(
                                      candidate.location_id,
                                    )
                                  }
                                >
                                  <MapPin className="size-3.5" />
                                  Show on map
                                </Button>
                              )}

                            <a
                              href={candidate.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sm text-primary underline"
                            >
                              View source
                            </a>
                          </div>
                        </div>
                      ),
                    )
                  )}
                </CardContent>
              </Card>
            ),
          )}
        </div>
      ) : (
        <Card className="border-dashed border-border/70 bg-card/40">
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground">
              No scenes were returned by the Director
              Agent.
            </p>
          </CardContent>
        </Card>
      )}
    </AnalysisGate>
  )
}

function SceneSelector({
  scenes,
  activeScene,
  activeSceneIndex,
  onSceneChange,
  onPrevious,
  onNext,
}: {
  scenes: DirectorScene[]
  activeScene: DirectorScene
  activeSceneIndex: number
  onSceneChange: (sceneNumber: number) => void
  onPrevious: () => void
  onNext: () => void
}) {
  return (
    <Card className="border-border/60 bg-card/70">
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-amber/10 text-amber">
            <Building2 className="size-5" />
          </div>

          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Location search scene
            </p>

            <p className="truncate text-sm font-semibold">
              {activeScene.scene_heading}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Previous scene"
            disabled={activeSceneIndex <= 0}
            onClick={onPrevious}
          >
            <ChevronLeft className="size-4" />
          </Button>

          <Select
            value={String(activeScene.scene_number)}
            onValueChange={(value) =>
              onSceneChange(Number(value))
            }
          >
            <SelectTrigger
              className="w-[220px]"
              aria-label="Select screenplay scene"
            >
              <SelectValue />
            </SelectTrigger>

            <SelectContent>
              {scenes.map((scene) => (
                <SelectItem
                  key={scene.scene_number}
                  value={String(
                    scene.scene_number,
                  )}
                >
                  {getSceneLabel(scene)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Next scene"
            disabled={
              activeSceneIndex >=
              scenes.length - 1
            }
            onClick={onNext}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function SceneSummary({
  scene,
  detectedRequirements,
}: {
  scene: DirectorScene
  detectedRequirements: string[]
}) {
  return (
    <Card className="overflow-hidden border-border/60 bg-card/70">
      <CardHeader className="border-b border-border/50 bg-muted/20">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardDescription>
              Scene {scene.scene_number}
            </CardDescription>

            <CardTitle className="mt-1 text-lg">
              {scene.scene_heading}
            </CardTitle>
          </div>

          <Badge
            variant="outline"
            className="border-primary/30 bg-primary/10 text-primary"
          >
            <Sparkles className="mr-1 size-3" />
            Director analyzed
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-5">
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Required setting
          </p>

          <p className="text-sm font-medium">
            {scene.location_setting ||
              'No specific setting detected'}
          </p>
        </div>

        <Separator />

        <div>
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="size-4 text-amber" />

            <p className="text-sm font-medium">
              AI-detected requirements
            </p>
          </div>

          {detectedRequirements.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {detectedRequirements.map(
                (requirement) => (
                  <Badge
                    key={requirement}
                    variant="secondary"
                    className="font-normal"
                  >
                    {requirement}
                  </Badge>
                ),
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No special production requirements were
              detected.
            </p>
          )}

          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
            CinePilot extracted these requirements from the
            screenplay. Your preferences below will be
            combined with them automatically.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

type UpdateRequirement = <
  Key extends keyof SceneLocationRequirements,
>(
  key: Key,
  value: SceneLocationRequirements[Key],
) => void

function LocationRequirementsForm({
  scene,
  requirements,
  updateRequirement,
  searchDisabled,
  isSearching,
  onSearch,
}: {
  scene: DirectorScene
  requirements: SceneLocationRequirements
  updateRequirement: UpdateRequirement
  searchDisabled: boolean
  isSearching: boolean
  onSearch: () => Promise<void>
}) {
  return (
    <Card className="border-border/60 bg-card/70">
      <CardHeader>
        <CardTitle className="text-base">
          Your location preferences
        </CardTitle>

        <CardDescription>
          Add only the real-world constraints the agents
          cannot determine from the screenplay.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <label
              htmlFor="preferred-region"
              className="text-sm font-medium"
            >
              Preferred filming region
            </label>

            <div className="relative">
              <MapPin className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

              <Input
                id="preferred-region"
                value={
                  requirements.preferredRegion
                }
                onChange={(event) =>
                  updateRequirement(
                    'preferredRegion',
                    event.target.value,
                  )
                }
                placeholder="For example: Bratislava, Slovakia"
                className="pl-9"
                autoComplete="off"
              />
            </div>

            <p className="text-xs text-muted-foreground">
              Enter a city, region, or country as the
              center of the search.
            </p>
          </div>

          <div className="space-y-2">
            <label
              htmlFor="maximum-day-rate"
              className="text-sm font-medium"
            >
              Maximum location day rate
            </label>

            <div className="flex gap-2">
              <div className="relative min-w-0 flex-1">
                <CircleDollarSign className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

                <Input
                  id="maximum-day-rate"
                  type="number"
                  min="0"
                  step="50"
                  value={
                    requirements.maximumDayRate
                  }
                  onChange={(event) =>
                    updateRequirement(
                      'maximumDayRate',
                      event.target.value,
                    )
                  }
                  className="pl-9"
                />
              </div>

              <Select
                value={requirements.currency}
                onValueChange={(value) =>
                  updateRequirement(
                    'currency',
                    String(value),
                  )
                }
              >
                <SelectTrigger
                  className="w-24"
                  aria-label="Budget currency"
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  {CURRENCIES.map((currency) => (
                    <SelectItem
                      key={currency}
                      value={currency}
                    >
                      {currency}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <p className="text-xs text-muted-foreground">
              Location fee per filming day.
            </p>
          </div>

          <div className="space-y-2">
            <label
              htmlFor="search-radius"
              className="text-sm font-medium"
            >
              Search radius
            </label>

            <div className="relative">
              <Crosshair className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

              <Input
                id="search-radius"
                type="number"
                min="1"
                max="500"
                value={
                  requirements.searchRadiusKm
                }
                onChange={(event) =>
                  updateRequirement(
                    'searchRadiusKm',
                    event.target.value,
                  )
                }
                className="pl-9 pr-12"
              />

              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                km
              </span>
            </div>

            <p className="text-xs text-muted-foreground">
              Distance from the preferred region.
            </p>
          </div>

          <div className="space-y-2 sm:col-span-2">
            <label
              htmlFor="additional-requirements"
              className="text-sm font-medium"
            >
              Additional requirements

              <span className="ml-1 font-normal text-muted-foreground">
                (optional)
              </span>
            </label>

            <Textarea
              id="additional-requirements"
              value={
                requirements.additionalRequirements
              }
              onChange={(event) =>
                updateRequirement(
                  'additionalRequirements',
                  event.target.value,
                )
              }
              maxLength={500}
              rows={4}
              placeholder="For example: Must resemble an abandoned 1980s motel, allow filming after midnight, and have space for two vehicles."
              className="resize-none"
            />

            <div className="flex justify-between gap-3 text-xs text-muted-foreground">
              <span>
                Describe anything not already detected by
                the Director Agent.
              </span>

              <span className="shrink-0 tabular-nums">
                {
                  requirements
                    .additionalRequirements.length
                }
                /500
              </span>
            </div>
          </div>
        </div>

        <details className="group rounded-xl border border-border/60 bg-muted/15">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-medium">
            <span className="flex items-center gap-2">
              <SlidersHorizontal className="size-4 text-muted-foreground" />
              Advanced requirements
            </span>

            <ChevronRight className="size-4 text-muted-foreground transition-transform group-open:rotate-90" />
          </summary>

          <div className="grid gap-5 border-t border-border/60 p-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Scene environment
              </label>

              <Select
                value={requirements.environment}
                onValueChange={(value) =>
                  updateRequirement(
                    'environment',
                    value as EnvironmentPreference,
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="Interior">
                    Interior
                  </SelectItem>

                  <SelectItem value="Exterior">
                    Exterior
                  </SelectItem>

                  <SelectItem value="Interior/Exterior">
                    Interior and exterior
                  </SelectItem>

                  <SelectItem value="Either">
                    Either
                  </SelectItem>
                </SelectContent>
              </Select>

              <p className="text-xs text-muted-foreground">
                Prefilled from the Director Agent.
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Permit preference
              </label>

              <Select
                value={
                  requirements.permitPreference
                }
                onValueChange={(value) =>
                  updateRequirement(
                    'permitPreference',
                    value as PermitPreference,
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="any">
                    No preference
                  </SelectItem>

                  <SelectItem value="permit-free-preferred">
                    Permit-free preferred
                  </SelectItem>

                  <SelectItem value="permit-free-required">
                    Permit-free required
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Location type
              </label>

              <Select
                value={
                  requirements.practicalOrStudio
                }
                onValueChange={(value) =>
                  updateRequirement(
                    'practicalOrStudio',
                    value as SceneLocationRequirements['practicalOrStudio'],
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="either">
                    Practical location or studio
                  </SelectItem>

                  <SelectItem value="practical">
                    Practical location only
                  </SelectItem>

                  <SelectItem value="studio">
                    Studio or constructed set
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="filming-date"
                className="text-sm font-medium"
              >
                Preferred filming date
              </label>

              <Input
                id="filming-date"
                type="date"
                value={requirements.filmingDate}
                onChange={(event) =>
                  updateRequirement(
                    'filmingDate',
                    event.target.value,
                  )
                }
              />
            </div>
          </div>
        </details>

        <Separator />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-relaxed text-muted-foreground">
            Parallel will search real sources, then the
            Location Agent will evaluate and rank the
            candidates.
          </p>

          <Button
            type="button"
            disabled={
              searchDisabled || isSearching
            }
            onClick={() => void onSearch()}
            className="shrink-0 bg-amber text-amber-foreground hover:bg-amber/90"
          >
            <Search className="size-4" />

            {isSearching
              ? 'Searching and evaluating...'
              : `Find locations for Scene ${scene.scene_number}`}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function PreSearchMap({
  region,
  radius,
  sceneNumber,
}: {
  region: string
  radius: string
  sceneNumber: number
}) {
  return (
    <Card className="overflow-hidden border-border/60 bg-card/70 py-0 xl:sticky xl:top-24 xl:h-[calc(100vh-8rem)] xl:min-h-[620px]">
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          <MapPin className="size-4 text-amber" />
          Scout map
        </div>

        <Badge variant="outline">
          Scene {sceneNumber}
        </Badge>
      </div>

      <div className="relative flex h-[420px] items-center justify-center overflow-hidden bg-[#101820] xl:h-[calc(100%-3.25rem)]">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px)',
            backgroundSize: '42px 42px',
          }}
        />

        <div className="absolute left-[18%] top-[24%] size-28 rounded-full border border-primary/20" />

        <div className="absolute bottom-[20%] right-[12%] size-44 rounded-full border border-amber/15" />

        <div className="relative mx-6 max-w-sm rounded-2xl border border-white/10 bg-black/45 p-6 text-center shadow-2xl backdrop-blur-md">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-amber/15 text-amber">
            <MapPin className="size-6" />
          </div>

          <h3 className="mt-4 text-sm font-semibold text-white">
            Your scout map is ready
          </h3>

          <p className="mt-2 text-xs leading-relaxed text-white/60">
            {region.trim()
              ? `CinePilot will search within ${
                  radius || '50'
                } km of ${region}.`
              : 'Enter a preferred region to define the center of the search.'}
          </p>

          <div className="mt-4 flex items-center justify-center gap-2 text-[11px] text-white/45">
            <span className="size-2 rounded-full bg-amber" />
            Candidate markers appear after the search
          </div>
        </div>
      </div>
    </Card>
  )
}