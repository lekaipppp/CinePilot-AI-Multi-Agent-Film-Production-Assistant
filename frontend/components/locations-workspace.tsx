'use client'

import dynamic from 'next/dynamic'
import Link from 'next/link'
import * as React from 'react'
import {
  ArrowRight,
  Building2,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Crosshair,
  Loader2,
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
  type LocationCandidate,
} from '@/lib/location-api'
import {
  createDefaultRequirements,
  type EnvironmentPreference,
  type PermitPreference,
  type SceneLocationRequirements,
} from '@/lib/location-requirements'

const LocationMap = dynamic(
  () => import('@/components/location-map'),
  {
    ssr: false,
  },
)

const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CAD']

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

/*
 * Shared by the manual "Find locations for Scene N" button and the
 * automatic re-search loop below — the only place the
 * LocationSearchRequest payload is built, so the two flows can never
 * drift apart.
 */
function fetchLocationsForScene(
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

export function LocationsWorkspace() {
  const {
    directorAnalysis,
    selectedLocationsByScene,
    confirmLocationForScene,
    allScenesHaveSelectedLocation,
    pendingLocationBudgetOverride,
    clearPendingLocationBudgetOverride,
    autoRelocateRequestId,
    requirementsByScene,
    updateSceneRequirement,
  } = useProduction()
  const scenes = directorAnalysis?.scenes ?? []

  const [isAutoRelocating, setIsAutoRelocating] = React.useState(false)

  const [autoRelocateProgress, setAutoRelocateProgress] = React.useState<{
    current: number
    total: number
  } | null>(null)

  const [isSearching, setIsSearching] = React.useState(false)

  const [searchError, setSearchError] =
    React.useState<string | null>(null)

  const [locationResult, setLocationResult] =
    React.useState<LocationAgentOutput | null>(null)

  const [selectedLocationId, setSelectedLocationId] =
    React.useState<string | null>(null)

  const [activeSceneNumber, setActiveSceneNumber] =
    React.useState<number | null>(null)

  // Whether the active scene's already-confirmed candidate list is
  // expanded back open for reconsideration. Reset whenever the active
  // scene changes, so scene 2 never inherits scene 1's expanded state.
  const [isReconsidering, setIsReconsidering] =
    React.useState(false)

  React.useEffect(() => {
    setIsReconsidering(false)
  }, [activeSceneNumber])

  /*
   * requirementsByScene itself is now owned by production-provider.tsx
   * (seeded there whenever directorAnalysis changes) so it survives
   * navigating away from this page. This effect only needs to seed the
   * locally-scoped "which scene is on screen" cursor.
   */
  React.useEffect(() => {
    if (scenes.length === 0) return

    setActiveSceneNumber(
      (current) => current ?? scenes[0].scene_number,
    )
  }, [scenes])

  /*
   * When a Budget rerun tightens the locations envelope, overwrite every
   * scene's maximumDayRate/currency with the new per-scene cap — and
   * only those two fields, leaving region/radius/environment/every other
   * per-scene preference the user already set untouched.
   */
  React.useEffect(() => {
    if (!pendingLocationBudgetOverride) return

    for (const scene of scenes) {
      updateSceneRequirement(
        scene.scene_number,
        'maximumDayRate',
        String(Math.round(pendingLocationBudgetOverride.amount)),
      )
      updateSceneRequirement(
        scene.scene_number,
        'currency',
        pendingLocationBudgetOverride.currency,
      )
    }

    clearPendingLocationBudgetOverride()
  }, [
    pendingLocationBudgetOverride,
    scenes,
    updateSceneRequirement,
    clearPendingLocationBudgetOverride,
  ])

  /*
   * A budget rerun signals this by bumping autoRelocateRequestId (a
   * hackathon-demo tradeoff: fully automatic re-search beats making the
   * user manually re-trigger every scene). Re-search every scene
   * sequentially — one at a time, not in parallel, to keep this simple
   * and avoid hammering the backend — and auto-select the top match by
   * match_score for each. Skip on the initial-mount value of 0.
   */
  React.useEffect(() => {
    if (autoRelocateRequestId === 0) return

    let cancelled = false

    async function relocateAllScenes() {
      setIsAutoRelocating(true)

      for (let index = 0; index < scenes.length; index += 1) {
        if (cancelled) return

        const scene = scenes[index]
        setAutoRelocateProgress({ current: index + 1, total: scenes.length })

        const requirements =
          requirementsByScene[scene.scene_number] ??
          createDefaultRequirements(scene)

        try {
          const result = await fetchLocationsForScene(scene, requirements)

          const candidates =
            result.scene_recommendations.find(
              (recommendation) =>
                recommendation.scene_number === scene.scene_number,
            )?.candidates ?? []

          // The Location Agent is instructed to sort by match_score
          // descending, but that's a prompt instruction, not a
          // schema-enforced guarantee — sort defensively before
          // trusting candidates[0].
          const topCandidate = [...candidates].sort(
            (a, b) => b.match_score - a.match_score,
          )[0]

          if (!cancelled && topCandidate) {
            confirmLocationForScene(scene.scene_number, topCandidate)
          }
          // Zero candidates: leave this scene unselected and move on.
        } catch {
          // Search failed for this scene: skip it and continue rather
          // than aborting the whole loop.
        }
      }

      if (!cancelled) {
        setIsAutoRelocating(false)
        setAutoRelocateProgress(null)
      }
    }

    void relocateAllScenes()

    return () => {
      cancelled = true
    }
  }, [autoRelocateRequestId])

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

      updateSceneRequirement(activeScene.scene_number, key, value)
    },
    [activeScene, updateSceneRequirement],
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

  const handleConfirmLocation = (
    sceneNumber: number,
    candidate: LocationCandidate,
  ) => {
    confirmLocationForScene(sceneNumber, candidate)
    setSelectedLocationId(candidate.location_id)

    // Only auto-advance when the confirmed candidate belongs to the scene
    // currently on screen — a stale recommendation for a different scene
    // (not yet re-searched after switching) should not move the user off
    // the scene they're actually looking at.
    if (
      activeScene &&
      sceneNumber === activeScene.scene_number &&
      activeSceneIndex >= 0 &&
      activeSceneIndex < scenes.length - 1
    ) {
      selectNextScene()
    }
  }

  const handleSearch = async () => {
    if (!activeScene || !activeRequirements) return

    setIsSearching(true)
    setSearchError(null)
    setLocationResult(null)
    setSelectedLocationId(null)

    try {
      const result = await fetchLocationsForScene(activeScene, activeRequirements)

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

          {isAutoRelocating && (
            <Card className="border-amber/40 bg-amber/5">
              <CardContent className="flex items-center gap-3 py-5">
                <Loader2 className="size-4 shrink-0 animate-spin text-amber" />
                <div>
                  <p className="text-sm font-semibold">
                    Re-searching locations…
                    {autoRelocateProgress &&
                      ` scene ${autoRelocateProgress.current} of ${autoRelocateProgress.total}`}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Auto-selecting the top match for every scene against the new budget.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {allScenesHaveSelectedLocation && (
            <Card className="border-primary/40 bg-primary/5">
              <CardContent className="flex flex-col gap-3 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                    <Check className="size-4" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold">
                      Every scene has a selected location
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Ready to hand these off to the Scheduler Agent.
                    </p>
                  </div>
                </div>

                <Button
                  type="button"
                  nativeButton={false}
                  render={<Link href="/schedule" />}
                  className="shrink-0"
                >
                  Continue to Scheduler
                  <ArrowRight data-icon="inline-end" />
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.12fr)_minmax(340px,0.88fr)]">
            <div className="flex min-w-0 flex-col gap-5">
              <SceneSummary
                scene={activeScene}
                detectedRequirements={
                  detectedRequirements
                }
                selectedLocation={
                  selectedLocationsByScene[
                    activeScene.scene_number
                  ] ?? null
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

          {locationResult?.scene_recommendations
            .filter(
              (recommendation) =>
                // A search result stays in state until the next search
                // runs, but it should only ever be shown while its scene
                // is the one on screen — otherwise switching scenes still
                // shows the previous scene's stale recommendation card.
                recommendation.scene_number ===
                activeScene.scene_number,
            )
            .map(
            (recommendation) => {
              const isActiveRecommendation =
                recommendation.scene_number ===
                activeScene.scene_number

              const confirmedCandidate =
                selectedLocationsByScene[
                  recommendation.scene_number
                ]

              const showCollapsedView =
                isActiveRecommendation &&
                Boolean(confirmedCandidate) &&
                !isReconsidering

              return (
              <Card key={recommendation.scene_number}>
                <CardHeader>
                  <CardTitle>
                    Location recommendations for Scene{' '}
                    {recommendation.scene_number}
                  </CardTitle>
                </CardHeader>

                <CardContent className="space-y-4">
                  {showCollapsedView && confirmedCandidate ? (
                    <div className="flex flex-col gap-3">
                      <CandidateCard
                        candidate={confirmedCandidate}
                        isSelected
                        isMapHighlighted={
                          confirmedCandidate.location_id ===
                          selectedLocationId
                        }
                        onSelect={() => {}}
                        onShowOnMap={() =>
                          setSelectedLocationId(
                            confirmedCandidate.location_id,
                          )
                        }
                      />

                      <button
                        type="button"
                        onClick={() =>
                          setIsReconsidering(true)
                        }
                        className="self-start text-sm text-primary underline"
                      >
                        Change selection
                      </button>
                    </div>
                  ) : recommendation.candidates.length ===
                    0 ? (
                    <p>
                      No suitable locations were found.
                    </p>
                  ) : (
                    recommendation.candidates.map(
                      (candidate) => {
                        const isMapHighlighted =
                          candidate.location_id ===
                          selectedLocationId

                        const isSelected =
                          selectedLocationsByScene[
                            recommendation.scene_number
                          ]?.location_id ===
                          candidate.location_id

                        return (
                          <CandidateCard
                            key={candidate.location_id}
                            candidate={candidate}
                            isSelected={isSelected}
                            isMapHighlighted={
                              isMapHighlighted
                            }
                            onSelect={() => {
                              if (
                                isReconsidering &&
                                isActiveRecommendation
                              ) {
                                // Reconsidering an existing pick: update it
                                // and collapse back to the single-card view
                                // without jumping to the next scene.
                                confirmLocationForScene(
                                  recommendation.scene_number,
                                  candidate,
                                )
                                setSelectedLocationId(
                                  candidate.location_id,
                                )
                                setIsReconsidering(false)
                              } else {
                                handleConfirmLocation(
                                  recommendation.scene_number,
                                  candidate,
                                )
                              }
                            }}
                            onShowOnMap={() =>
                              setSelectedLocationId(
                                candidate.location_id,
                              )
                            }
                          />
                        )
                      },
                    )
                  )}
                </CardContent>
              </Card>
              )
            },
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

function CandidateCard({
  candidate,
  isSelected,
  isMapHighlighted,
  onSelect,
  onShowOnMap,
}: {
  candidate: LocationCandidate
  isSelected: boolean
  isMapHighlighted: boolean
  onSelect: () => void
  onShowOnMap: () => void
}) {
  return (
    <div
      className={`rounded-lg border p-4 transition-colors ${
        isSelected
          ? 'border-primary bg-primary/5'
          : isMapHighlighted
            ? 'border-amber/70 bg-amber/5'
            : 'border-border'
      }`}
    >
      <div className="flex justify-between gap-4">
        <h3 className="flex items-center gap-2 font-semibold">
          {candidate.place_name}
          {isSelected && (
            <Badge className="gap-1 border-primary/30 bg-primary text-primary-foreground">
              <Check className="size-3" />
              Selected
            </Badge>
          )}
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
        <Button
          type="button"
          size="sm"
          disabled={isSelected}
          onClick={onSelect}
          className="bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Check className="size-3.5" />
          {isSelected
            ? 'Selected for this scene'
            : 'Select this location'}
        </Button>

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
              onClick={onShowOnMap}
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
  const { selectedLocationsByScene } = useProduction()
  const selectedCount = scenes.filter(
    (scene) => selectedLocationsByScene[scene.scene_number] !== undefined,
  ).length

  return (
    <Card className="border-border/60 bg-card/70">
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-amber/10 text-amber">
            <Building2 className="size-5" />
          </div>

          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Location search scene · {selectedCount}/{scenes.length} selected
            </p>

            <p className="flex items-center gap-1.5 truncate text-sm font-semibold">
              {selectedLocationsByScene[activeScene.scene_number] && (
                <Check className="size-3.5 shrink-0 text-primary" />
              )}
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
                  <span className="flex items-center gap-1.5">
                    {selectedLocationsByScene[scene.scene_number] && (
                      <Check className="size-3.5 shrink-0 text-primary" />
                    )}
                    {getSceneLabel(scene)}
                  </span>
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
  selectedLocation,
}: {
  scene: DirectorScene
  detectedRequirements: string[]
  selectedLocation: LocationCandidate | null
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

          <div className="flex flex-wrap items-center justify-end gap-2">
            {selectedLocation && (
              <Badge className="border-primary/30 bg-primary text-primary-foreground">
                <Check className="mr-1 size-3" />
                Selected: {selectedLocation.place_name}
              </Badge>
            )}

            <Badge
              variant="outline"
              className="border-primary/30 bg-primary/10 text-primary"
            >
              <Sparkles className="mr-1 size-3" />
              Director analyzed
            </Badge>
          </div>
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