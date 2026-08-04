'use client'

import * as React from 'react'
import {
  AlertTriangle,
  CalendarRange,
  Clock,
  CloudRain,
  MapPin,
  Moon,
  Sun,
  UserRound,
  Users,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { AnalysisGate } from '@/components/analysis-gate'
import {
  CONSTRAINTS,
  LOCATIONS,
  SCENES,
  SCHEDULE,
  SHOOT_DAYS,
  TOTAL_PAGES,
  type Constraint,
} from '@/lib/production-data'
import { cn } from '@/lib/utils'

const KIND_ICON: Record<Constraint['kind'], typeof UserRound> = {
  actor: UserRound,
  crew: Users,
  weather: CloudRain,
}

const SEVERITY_STYLES: Record<Constraint['severity'], string> = {
  high: 'border-destructive/40 bg-destructive/10 text-destructive',
  medium: 'border-amber/40 bg-amber/10 text-amber',
  low: 'border-border bg-muted/40 text-muted-foreground',
}

function locationName(id: string) {
  return LOCATIONS.find((l) => l.id === id)?.name ?? 'Unassigned'
}

function isNightBlock(callTime: string) {
  const hour = Number(callTime.split(':')[0])
  return hour >= 15 || hour < 5
}

export function ScheduleWorkspace() {
  const [kinds, setKinds] = React.useState<string[]>(['actor', 'crew', 'weather'])

  const visibleConstraints = CONSTRAINTS.filter((c) => kinds.includes(c.kind))
  const conflicts = SCHEDULE.filter((b) => b.conflict)
  const nightDays = SCHEDULE.filter((b) => isNightBlock(b.callTime)).length

  return (
    <AnalysisGate agent="scheduler">
      <div className="flex flex-col gap-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryTile
            icon={CalendarRange}
            label="Shoot days"
            value={String(SHOOT_DAYS)}
            hint={`${TOTAL_PAGES.toFixed(2)} pages total`}
          />
          <SummaryTile
            icon={Moon}
            label="Night blocks"
            value={String(nightDays)}
            hint="Turnaround affects call times"
          />
          <SummaryTile
            icon={MapPin}
            label="Unit moves"
            value={String(new Set(SCHEDULE.map((b) => b.locationId)).size)}
            hint="Distinct locations in the plan"
          />
          <SummaryTile
            icon={AlertTriangle}
            label="Open conflicts"
            value={String(conflicts.length)}
            hint="Flagged for producer review"
            tone="warn"
          />
        </div>

        {conflicts.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle />
            <AlertTitle>
              {conflicts.length} scheduling conflicts need a decision before lock
            </AlertTitle>
            <AlertDescription>
              The scheduler produced a viable plan, but these days carry unresolved dependencies.
              Resolving them here prevents cascading changes in budget and risk.
            </AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Shooting schedule</CardTitle>
              <CardDescription>
                Day-by-day strip board grouped to minimise company moves and night turnarounds.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {SCHEDULE.map((block) => {
                const night = isNightBlock(block.callTime)
                return (
                  <div
                    key={block.id}
                    className={cn(
                      'flex flex-col gap-3 rounded-xl border bg-card/60 p-4 transition-colors',
                      block.conflict ? 'border-destructive/35' : 'border-border/70',
                    )}
                  >
                    <div className="flex flex-wrap items-start gap-3">
                      <div className="flex size-11 shrink-0 flex-col items-center justify-center rounded-lg bg-primary/12 font-mono text-primary">
                        <span className="text-[9px] uppercase leading-none opacity-70">day</span>
                        <span className="text-sm font-semibold leading-tight">{block.day}</span>
                      </div>

                      <div className="flex min-w-0 flex-1 flex-col gap-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold">{block.date}</span>
                          <Badge variant="outline" className="font-mono text-[10px]">
                            {block.unit}
                          </Badge>
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
                          {locationName(block.locationId)}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 font-mono text-xs text-muted-foreground">
                        <Clock className="size-3.5" />
                        {block.callTime} → {block.wrapTime}
                      </div>
                    </div>

                    <Separator />

                    <div className="flex flex-wrap gap-2">
                      {block.scenes.map((sceneId) => {
                        const scene = SCENES.find((s) => s.id === sceneId)
                        return (
                          <span
                            key={sceneId}
                            className="rounded-md border border-border/70 bg-muted/40 px-2 py-1 text-xs"
                          >
                            <span className="font-mono text-[10px] text-muted-foreground">
                              SC {sceneId}
                            </span>{' '}
                            {scene?.slug}
                          </span>
                        )
                      })}
                    </div>

                    {block.conflict && (
                      <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-2.5 text-xs text-destructive">
                        <AlertTriangle className="mt-px size-3.5 shrink-0" />
                        <span>{block.conflict}</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </CardContent>
          </Card>

          <Card className="xl:sticky xl:top-24 xl:self-start">
            <CardHeader>
              <CardTitle>Constraints</CardTitle>
              <CardDescription>
                Availability windows and environmental limits the scheduler solved against.
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

              <ul className="flex flex-col gap-3">
                {visibleConstraints.map((constraint) => {
                  const Icon = KIND_ICON[constraint.kind]
                  return (
                    <li
                      key={constraint.id}
                      className="flex gap-3 rounded-xl border border-border/70 bg-card/60 p-3"
                    >
                      <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md bg-muted/60 text-muted-foreground">
                        <Icon className="size-3.5" />
                      </span>
                      <div className="flex min-w-0 flex-col gap-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-medium">{constraint.name}</span>
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
                          {constraint.detail}
                        </p>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
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
