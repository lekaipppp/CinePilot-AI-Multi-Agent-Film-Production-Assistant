'use client'

import * as React from 'react'
import {
  CalendarClock,
  CloudRain,
  FileCheck2,
  HardHat,
  Lightbulb,
  Loader2,
  ShieldAlert,
  Wallet,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { AnalysisGate } from '@/components/analysis-gate'
import { useProduction } from '@/components/production-provider'
import type { RiskItem } from '@/lib/risk-api'
import { cn } from '@/lib/utils'

const CATEGORY_ICON: Record<RiskItem['category'], typeof ShieldAlert> = {
  Weather: CloudRain,
  Permits: FileCheck2,
  Budget: Wallet,
  Scheduling: CalendarClock,
  Safety: HardHat,
}

const SEVERITY_ORDER: Record<RiskItem['severity'], number> = { high: 0, medium: 1, low: 2 }

const SEVERITY_BADGE: Record<RiskItem['severity'], string> = {
  high: 'border-destructive/40 bg-destructive/12 text-destructive',
  medium: 'border-amber/40 bg-amber/12 text-amber',
  low: 'border-success/35 bg-success/10 text-success',
}

const SEVERITY_BAR: Record<RiskItem['severity'], string> = {
  high: 'bg-destructive',
  medium: 'bg-amber',
  low: 'bg-success',
}

const CATEGORIES = ['All', 'Weather', 'Permits', 'Budget', 'Scheduling', 'Safety'] as const

const SEVERITY_WEIGHT: Record<RiskItem['severity'], number> = { high: 3, medium: 2, low: 1 }

function computeRiskScore(risks: RiskItem[]): number {
  if (risks.length === 0) return 0

  const rawScore = risks.reduce((sum, r) => sum + SEVERITY_WEIGHT[r.severity], 0)

  return Math.min(100, Math.round((rawScore / (risks.length * 3)) * 100))
}

export function RiskWorkspace() {
  const {
    directorAnalysis,
    scheduleResult,
    budgetResult,
    riskResult,
    riskError,
    agents,
    runRisk,
  } = useProduction()
  const scenes = directorAnalysis?.scenes ?? []

  const [category, setCategory] = React.useState<string>('All')
  const [severity, setSeverity] = React.useState<string>('All')

  const isGenerating = agents.risk === 'running'

  const risks = riskResult?.risks ?? []
  const riskScore = computeRiskScore(risks)

  const visible = risks
    .filter(
      (r) =>
        (category === 'All' || r.category === category) &&
        (severity === 'All' || r.severity === severity),
    )
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])

  const counts = {
    high: risks.filter((r) => r.severity === 'high').length,
    medium: risks.filter((r) => r.severity === 'medium').length,
    low: risks.filter((r) => r.severity === 'low').length,
  }

  const scoreLabel = riskScore >= 70 ? 'Critical' : riskScore >= 45 ? 'Elevated' : 'Manageable'
  const scoreTone =
    riskScore >= 70 ? 'text-destructive' : riskScore >= 45 ? 'text-amber' : 'text-success'

  return (
    /*
     * Use the Director gate here, same as Schedule/Budget/Locations —
     * this workspace should be reachable as soon as script analysis is
     * complete, not only once the Risk Agent has already run (which
     * would make the "Generate risk assessment" button unreachable).
     */
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
              <CardTitle className="text-base">Risk assessment</CardTitle>
              <CardDescription>
                The Risk Agent cross-references your scenes, confirmed locations, schedule, and
                budget to surface production risks across five categories.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-col gap-1">
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    Weather, permits, and safety risks only need your scenes and locations.
                    Scheduling and budget risks need those agents to have run first.
                  </p>
                  {(!scheduleResult || !budgetResult) && (
                    <p className="text-xs text-amber">
                      Run Scheduler/Budget first for a more complete assessment.
                    </p>
                  )}
                </div>

                <Button
                  type="button"
                  disabled={isGenerating}
                  onClick={() => void runRisk()}
                  className="shrink-0 bg-amber text-amber-foreground hover:bg-amber/90"
                >
                  {isGenerating && <Loader2 className="size-4 animate-spin" />}
                  {isGenerating ? 'Generating risk assessment...' : 'Generate risk assessment'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {riskError && (
            <Card className="border-destructive/50">
              <CardContent className="pt-6 text-sm text-destructive">{riskError}</CardContent>
            </Card>
          )}

          {!riskResult && !isGenerating && !riskError && (
            <Card className="border-dashed border-border/70 bg-card/40">
              <CardContent className="flex flex-col items-center gap-2 py-14 text-center">
                <ShieldAlert className="size-8 text-muted-foreground" />
                <p className="text-sm font-medium">No risk assessment generated yet</p>
                <p className="max-w-sm text-xs text-muted-foreground">
                  Click &ldquo;Generate risk assessment&rdquo; above to have the Risk Agent
                  identify production risks from the {scenes.length}{' '}
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

          {riskResult && (
            <>
              <div className="grid gap-4 lg:grid-cols-[1.2fr_2fr]">
                <Card>
                  <CardHeader>
                    <CardTitle>Composite risk score</CardTitle>
                    <CardDescription>Weighted across likelihood, cost and schedule impact.</CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-4">
                    <div className="flex items-end gap-3">
                      <span className={cn('font-mono text-4xl font-semibold leading-none', scoreTone)}>
                        {riskScore}
                      </span>
                      <span className="pb-1 text-sm text-muted-foreground">/ 100</span>
                      <Badge
                        variant="outline"
                        className={cn(
                          'ml-auto font-mono text-[10px] uppercase',
                          riskScore >= 70
                            ? SEVERITY_BADGE.high
                            : riskScore >= 45
                              ? SEVERITY_BADGE.medium
                              : SEVERITY_BADGE.low,
                        )}
                      >
                        {scoreLabel}
                      </Badge>
                    </div>
                    <Progress value={riskScore} />
                    <Separator />
                    <div className="grid grid-cols-3 gap-3">
                      <CountTile label="High" value={counts.high} tone="high" />
                      <CountTile label="Medium" value={counts.medium} tone="medium" />
                      <CountTile label="Low" value={counts.low} tone="low" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Exposure by category</CardTitle>
                    <CardDescription>
                      Where the production is most likely to lose days or money.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-4">
                    {(['Weather', 'Permits', 'Scheduling', 'Budget', 'Safety'] as const).map((cat) => {
                      const items = risks.filter((r) => r.category === cat)
                      const avg = items.length
                        ? Math.round(items.reduce((s, r) => s + r.likelihood, 0) / items.length)
                        : 0
                      const Icon = CATEGORY_ICON[cat]
                      return (
                        <div key={cat} className="flex flex-col gap-1.5">
                          <div className="flex items-center gap-2 text-sm">
                            <Icon className="size-4 text-muted-foreground" />
                            <span className="flex-1">{cat}</span>
                            <span className="font-mono text-xs text-muted-foreground">
                              {items.length} {items.length === 1 ? 'item' : 'items'} · {avg}% avg
                            </span>
                          </div>
                          <Progress value={avg} />
                        </div>
                      )
                    })}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Risk register</CardTitle>
                  <CardDescription>
                    Each entry pairs the exposure with the mitigation the agent recommends.
                  </CardDescription>
                  <CardAction className="flex flex-wrap gap-2">
                    <Select value={category} onValueChange={(v) => setCategory(String(v))}>
                      <SelectTrigger size="sm" className="w-[140px]">
                        <SelectValue placeholder="Category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {CATEGORIES.map((c) => (
                            <SelectItem key={c} value={c}>
                              {c === 'All' ? 'All categories' : c}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                    <Select value={severity} onValueChange={(v) => setSeverity(String(v))}>
                      <SelectTrigger size="sm" className="w-[130px]">
                        <SelectValue placeholder="Severity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectItem value="All">All severities</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="low">Low</SelectItem>
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </CardAction>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  {visible.length === 0 ? (
                    <p className="py-8 text-center text-sm text-muted-foreground">
                      No risks match the current filters.
                    </p>
                  ) : (
                    visible.map((risk) => {
                      const Icon = CATEGORY_ICON[risk.category]
                      return (
                        <article
                          key={risk.id}
                          className="flex gap-0 overflow-hidden rounded-xl border border-border/70 bg-card/60"
                        >
                          <span
                            aria-hidden
                            className={cn('w-1 shrink-0', SEVERITY_BAR[risk.severity])}
                          />
                          <div className="flex min-w-0 flex-1 flex-col gap-3 p-4">
                            <div className="flex flex-wrap items-start gap-2">
                              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted/60 text-muted-foreground">
                                <Icon className="size-4" />
                              </span>
                              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                                <h3 className="text-sm font-semibold">{risk.title}</h3>
                                <span className="font-mono text-[11px] text-muted-foreground">
                                  {risk.scope}
                                </span>
                              </div>
                              <div className="flex shrink-0 items-center gap-2">
                                <Badge variant="outline" className="font-mono text-[10px]">
                                  {risk.category}
                                </Badge>
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    'font-mono text-[10px] uppercase',
                                    SEVERITY_BADGE[risk.severity],
                                  )}
                                >
                                  {risk.severity}
                                </Badge>
                              </div>
                            </div>

                            <div className="flex flex-col gap-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Likelihood</span>
                                <span className="font-mono">{risk.likelihood}%</span>
                              </div>
                              <Progress value={risk.likelihood} />
                            </div>

                            <p className="text-xs leading-relaxed text-muted-foreground">{risk.impact}</p>

                            <div className="flex items-start gap-2 rounded-lg border border-primary/25 bg-primary/8 p-3">
                              <Lightbulb className="mt-px size-4 shrink-0 text-primary" />
                              <div className="flex flex-col gap-0.5">
                                <span className="text-[11px] font-semibold uppercase tracking-wide text-primary">
                                  Recommended mitigation
                                </span>
                                <p className="text-xs leading-relaxed text-foreground/90">
                                  {risk.recommendation}
                                </p>
                              </div>
                            </div>
                          </div>
                        </article>
                      )
                    })
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}
    </AnalysisGate>
  )
}

function CountTile({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone: RiskItem['severity']
}) {
  return (
    <div className="flex flex-col gap-0.5 rounded-lg border border-border/70 bg-muted/30 p-3">
      <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</span>
      <span
        className={cn(
          'font-mono text-xl font-semibold leading-tight',
          tone === 'high' ? 'text-destructive' : tone === 'medium' ? 'text-amber' : 'text-success',
        )}
      >
        {value}
      </span>
    </div>
  )
}
