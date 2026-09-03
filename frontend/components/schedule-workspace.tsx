'use client'

import * as React from 'react'
import {
  AlertTriangle,
  CalendarRange,
  Clock,
  CloudRain,
  Loader2,
  MapPin,
  Moon,
  Sun,
  UserRound,
  Users,
} from 'lucide-react'
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
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { AnalysisGate } from '@/components/analysis-gate'
import { useProduction } from '@/components/production-provider'
import type { ScheduleBlock, SchedulingConstraint } from '@/lib/scheduler-api'
import { cn } from '@/lib/utils'

const KIND_ICON: Record<SchedulingConstraint['kind'], typeof UserRound> = {
  actor: UserRound,
  crew: Users,
  weather: CloudRain,
}

const KIND_LABEL: Record<SchedulingConstraint['kind'], string> = {
  actor: 'Actor',
  crew: 'Crew',
  weather: 'Weather',
}

const SEVERITY_STYLES: Record<SchedulingConstraint['severity'], string> = {
  high: 'border-destructive/40 bg-destructive/10 text-destructive',
  medium: 'border-amber/40 bg-amber/10 text-amber',
  low: 'border-border bg-muted/40 text-muted-foreground',
}

function isNightScene(block: ScheduleBlock) {
  const haystack = `${block.interior_exterior} ${block.time_of_day ?? ''}`
  return /night/i.test(haystack)
}

type DayGroup = {
  day: number
  blocks: ScheduleBlock[]
}

function groupByDay(schedule: ScheduleBlock[]): DayGroup[] {
  const byDay = new Map<number, ScheduleBlock[]>()

  for (const block of schedule) {
    const existing = byDay.get(block.shoot_day)
    if (existing) {
      existing.push(block)
    } else {
      byDay.set(block.shoot_day, [block])
    }
  }

  return Array.from(byDay.entries())
    .sort(([a], [b]) => a - b)
    .map(([day, blocks]) => ({ day, blocks }))
}

function dayLocationLabel(blocks: ScheduleBlock[]) {
  const names = Array.from(
    new Set(blocks.map((b) => b.location_name).filter((name): name is string => Boolean(name))),
  )

  if (names.length === 0) return 'Location not yet set'
  if (names.length === 1) return names[0]
  return `${names.length} locations`
}

export function ScheduleWorkspace() {
  const { directorAnalysis, agents, scheduleResult, scheduleError, runScheduler } = useProduction()
  const scenes = directorAnalysis?.scenes ?? []

  const [kinds, setKinds] = React.useState<string[]>(['actor', 'crew', 'weather'])
  const [targetShootDays, setTargetShootDays] = React.useState('7')
  const [additionalConstraints, setAdditionalConstraints] = React.useState('')

  const isGenerating = agents.scheduler === 'running'

  const schedule = scheduleResult?.schedule ?? []
  const constraints = scheduleResult?.constraints ?? []
  const dayGroups = React.useMemo(() => groupByDay(schedule), [schedule])

  const visibleConstraints = constraints.filter((c) => kinds.includes(c.kind))

  const conflictDays = new Set(
    schedule.filter((b) => b.has_conflict).map((b) => b.shoot_day),
  ).size

  const unitMoves = new Set(
    schedule.map((b) => b.location_name).filter((name): name is string => Boolean(name)),
  ).size

  const targetDaysNumber = Number(targetShootDays)
  const generateDisabled = scenes.length === 0 || !targetDaysNumber || targetDaysNumber <= 0

  const handleGenerate = () => {
    void runScheduler(targetDaysNumber, additionalConstraints.trim())
  }

  return (
    <AnalysisGate agent="director">
      {scenes.length === 0 ? (
        <Card className="border-dashed border-border/70 bg-card/40">
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground">
              No scenes were returned by the Director Agent.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-6">
          <Card className="border-border/60 bg-card/70">
            <CardHeader>
              <CardTitle className="text-base">Scheduling preferences</CardTitle>
              <CardDescription>
                Set a target day count and any actor, crew, or weather notes the Scheduler
                Agent should treat as constraints.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="target-shoot-days" className="text-sm font-medium">
                    Target shoot days
                  </label>
                  <div className="relative">
                    <CalendarRange className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="target-shoot-days"
                      type="number"
                      min="1"
                      value={targetShootDays}
                      onChange={(event) => setTargetShootDays(event.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Treated as a soft goal — the agent will not cut scenes to hit it.
                  </p>
                </div>

                <div className="space-y-2 sm:col-span-1">
                  <label htmlFor="additional-constraints" className="text-sm font-medium">
                    Additional constraints
                    <span className="ml-1 font-normal text-muted-foreground">(optional)</span>
                  </label>
                  <Textarea
                    id="additional-constraints"
                    value={additionalConstraints}
                    onChange={(event) => setAdditionalConstraints(event.target.value)}
                    maxLength={500}
                    rows={2}
                    placeholder="For example: lead actor unavailable Sept 12, aerial unit booked one day only."
                    className="resize-none"
                  />
                </div>
              </div>

              <Separator />

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  The Scheduler Agent groups scenes by location and night/day, flags
                  turnaround and cast conflicts, and respects your target day count.
                </p>

                <Button
                  type="button"
                  disabled={generateDisabled || isGenerating}
                  onClick={handleGenerate}
                  className="shrink-0 bg-amber text-amber-foreground hover:bg-amber/90"
                >
                  {isGenerating && <Loader2 className="size-4 animate-spin" />}
                  {isGenerating ? 'Generating schedule...' : 'Generate schedule'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {scheduleError && (
            <Card className="border-destructive/50">
              <CardContent className="pt-6 text-sm text-destructive">{scheduleError}</CardContent>
            </Card>
          )}

          {!scheduleResult && !isGenerating && !scheduleError && (
            <Card className="border-dashed border-border/70 bg-card/40">
              <CardContent className="flex flex-col items-center gap-2 py-14 text-center">
                <CalendarRange className="size-8 text-muted-foreground" />
                <p className="text-sm font-medium">No schedule generated yet</p>
                <p className="max-w-sm text-xs text-muted-foreground">
                  Set your target shoot days above and click &ldquo;Generate schedule&rdquo; to
                  have the Scheduler Agent build a day-by-day plan from the {scenes.length}{' '}
                  scenes Director Agent extracted.
                </p>
              </CardContent>
            </Card>
          )}

          {isGenerating && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="h-40 animate-pulse rounded-xl bg-muted/40" />
              <div className="h-40 animate-pulse rounded-xl bg-muted/40" />
            </div>
          )}

          {scheduleResult && (
            <>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <SummaryTile
                  icon={CalendarRange}
                  label="Shoot days"
                  value={String(scheduleResult.total_shoot_days)}
                  hint={`${scenes.length} scenes scheduled`}
                />
                <SummaryTile
                  icon={Moon}
                  label="Night blocks"
                  value={String(scheduleResult.night_block_count)}
                  hint="Turnaround affects call times"
                />
                <SummaryTile
                  icon={MapPin}
                  label="Unit moves"
                  value={String(unitMoves)}
                  hint="Distinct locations in the plan"
                />
                <SummaryTile
                  icon={AlertTriangle}
                  label="Open conflicts"
                  value={String(conflictDays)}
                  hint="Flagged for producer review"
                  tone="warn"
                />
              </div>

              {conflictDays > 0 && (
                <Alert variant="destructive">
                  <AlertTriangle />
                  <AlertTitle>
                    {conflictDays} shoot {conflictDays === 1 ? 'day carries' : 'days carry'} unresolved
                    scheduling conflicts
                  </AlertTitle>
                  <AlertDescription>
                    The scheduler produced a viable plan, but these days carry unresolved
                    dependencies. Resolving them here prevents cascading changes in budget and risk.
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
                <Card>
                  <CardHeader>
                    <CardTitle>Shooting schedule</CardTitle>
                    <CardDescription>
                      Day-by-day strip board grouped to minimise company moves and night
                      turnarounds.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-3">
                    {dayGroups.map((group) => {
                      const night = group.blocks.some(isNightScene)
                      const hasConflict = group.blocks.some((b) => b.has_conflict)
                      const conflictReasons = Array.from(
                        new Set(
                          group.blocks
                            .map((b) => b.conflict_reason)
                            .filter((reason): reason is string => Boolean(reason)),
                        ),
                      )
                      const earliestCall = group.blocks
                        .map((b) => b.call_time)
                        .sort()[0]

                      return (
                        <div
                          key={group.day}
                          className={cn(
                            'flex flex-col gap-3 rounded-xl border bg-card/60 p-4 transition-colors',
                            hasConflict ? 'border-destructive/35' : 'border-border/70',
                          )}
                        >
                          <div className="flex flex-wrap items-start gap-3">
                            <div className="flex size-11 shrink-0 flex-col items-center justify-center rounded-lg bg-primary/12 font-mono text-primary">
                              <span className="text-[9px] uppercase leading-none opacity-70">
                                day
                              </span>
                              <span className="text-sm font-semibold leading-tight">
                                {group.day}
                              </span>
                            </div>

                            <div className="flex min-w-0 flex-1 flex-col gap-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    'gap-1 font-mono text-[10px]',
                                    night
                                      ? 'border-primary/40 bg-primary/10 text-primary'
                                      : 'border-amber/40 bg-amber/10 text-amber',
                                  )}
                                >
                                  {night ? <Moon /> : <Sun />}
                                  {night ? 'NIGHT' : 'DAY'}
                                </Badge>
                              </div>
                              <span className="flex items-center gap-1.5 truncate text-xs text-muted-foreground">
                                <MapPin className="size-3.5 shrink-0" />
                                {dayLocationLabel(group.blocks)}
                              </span>
                            </div>

                            {earliestCall && (
                              <div className="flex items-center gap-1.5 font-mono text-xs text-muted-foreground">
                                <Clock className="size-3.5" />
                                Call {earliestCall}
                              </div>
                            )}
                          </div>

                          <Separator />

                          <div className="flex flex-wrap gap-2">
                            {group.blocks.map((block) => (
                              <span
                                key={block.scene_number}
                                className="rounded-md border border-border/70 bg-muted/40 px-2 py-1 text-xs"
                              >
                                <span className="font-mono text-[10px] text-muted-foreground">
                                  SC {block.scene_number} · {block.call_time}
                                </span>{' '}
                                {block.scene_heading}
                              </span>
                            ))}
                          </div>

                          {conflictReasons.map((reason) => (
                            <div
                              key={reason}
                              className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-2.5 text-xs text-destructive"
                            >
                              <AlertTriangle className="mt-px size-3.5 shrink-0" />
                              <span>{reason}</span>
                            </div>
                          ))}
                        </div>
                      )
                    })}
                  </CardContent>
                </Card>

                <Card className="xl:sticky xl:top-24 xl:self-start">
                  <CardHeader>
                    <CardTitle>Constraints</CardTitle>
                    <CardDescription>
                      Availability windows and environmental limits the scheduler solved
                      against.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-4">
                    <ToggleGroup
                      value={kinds}
                      onValueChange={(value) =>
                        setKinds((value as string[]).length ? (value as string[]) : kinds)
                      }
                      variant="outline"
                      className="w-full"
                    >
                      <ToggleGroupItem value="actor" className="flex-1">
                        Actors
                      </ToggleGroupItem>
                      <ToggleGroupItem value="crew" className="flex-1">
                        Crew
                      </ToggleGroupItem>
                      <ToggleGroupItem value="weather" className="flex-1">
                        Weather
                      </ToggleGroupItem>
                    </ToggleGroup>

                    {visibleConstraints.length === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        No constraints in this category.
                      </p>
                    ) : (
                      <ul className="flex flex-col gap-3">
                        {visibleConstraints.map((constraint, index) => {
                          const Icon = KIND_ICON[constraint.kind]
                          return (
                            <li
                              key={index}
                              className="flex gap-3 rounded-xl border border-border/70 bg-card/60 p-3"
                            >
                              <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md bg-muted/60 text-muted-foreground">
                                <Icon className="size-3.5" />
                              </span>
                              <div className="flex min-w-0 flex-col gap-1">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="text-sm font-medium">
                                    {KIND_LABEL[constraint.kind]}
                                  </span>
                                  <Badge
                                    variant="outline"
                                    className={cn(
                                      'font-mono text-[10px] uppercase',
                                      SEVERITY_STYLES[constraint.severity],
                                    )}
                                  >
                                    {constraint.severity}
                                  </Badge>
                                </div>
                                <p className="text-xs leading-relaxed text-muted-foreground">
                                  {constraint.description}
                                </p>
                                {constraint.affected_scene_numbers.length > 0 && (
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {constraint.affected_scene_numbers.map((n) => (
                                      <Badge key={n} variant="secondary" className="font-mono text-[10px]">
                                        SC {n}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </div>
      )}
    </AnalysisGate>
  )
}

function SummaryTile({
  icon: Icon,
  label,
  value,
  hint,
  tone = 'default',
}: {
  icon: typeof CalendarRange
  label: string
  value: string
  hint: string
  tone?: 'default' | 'warn'
}) {
  return (
    <Card className="gap-0 py-4">
      <CardContent className="flex items-center gap-3">
        <span
          className={cn(
            'flex size-10 shrink-0 items-center justify-center rounded-lg',
            tone === 'warn' ? 'bg-amber/12 text-amber' : 'bg-primary/12 text-primary',
          )}
        >
          <Icon className="size-5" />
        </span>
        <div className="flex min-w-0 flex-col">
          <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</span>
          <span className="font-mono text-xl font-semibold leading-tight">{value}</span>
          <span className="truncate text-xs text-muted-foreground">{hint}</span>
        </div>
      </CardContent>
    </Card>
  )
}
