'use client'

import * as React from 'react'
import {
  CalendarClock,
  CloudRain,
  FileCheck2,
  HardHat,
  Lightbulb,
  ShieldAlert,
  Wallet,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
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
import { RISKS, RISK_SCORE, type Risk } from '@/lib/production-data'
import { cn } from '@/lib/utils'

const CATEGORY_ICON: Record<Risk['category'], typeof ShieldAlert> = {
  Weather: CloudRain,
  Permits: FileCheck2,
  Budget: Wallet,
  Scheduling: CalendarClock,
  Safety: HardHat,
}

const SEVERITY_ORDER: Record<Risk['severity'], number> = { high: 0, medium: 1, low: 2 }

const SEVERITY_BADGE: Record<Risk['severity'], string> = {
  high: 'border-destructive/40 bg-destructive/12 text-destructive',
  medium: 'border-amber/40 bg-amber/12 text-amber',
  low: 'border-success/35 bg-success/10 text-success',
}

const SEVERITY_BAR: Record<Risk['severity'], string> = {
  high: 'bg-destructive',
  medium: 'bg-amber',
  low: 'bg-success',
}

const CATEGORIES = ['All', 'Weather', 'Permits', 'Budget', 'Scheduling', 'Safety'] as const

export function RiskWorkspace() {
  const [category, setCategory] = React.useState<string>('All')
  const [severity, setSeverity] = React.useState<string>('All')

  const visible = RISKS.filter(
    (r) =>
      (category === 'All' || r.category === category) &&
      (severity === 'All' || r.severity === severity),
  ).sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])

  const counts = {
    high: RISKS.filter((r) => r.severity === 'high').length,
    medium: RISKS.filter((r) => r.severity === 'medium').length,
    low: RISKS.filter((r) => r.severity === 'low').length,
  }

  const scoreLabel = RISK_SCORE >= 70 ? 'Critical' : RISK_SCORE >= 45 ? 'Elevated' : 'Manageable'
  const scoreTone =
    RISK_SCORE >= 70 ? 'text-destructive' : RISK_SCORE >= 45 ? 'text-amber' : 'text-success'

  return (
    <AnalysisGate agent="risk">
      <div className="flex flex-col gap-6">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_2fr]">
          <Card>
            <CardHeader>
              <CardTitle>Composite risk score</CardTitle>
              <CardDescription>Weighted across likelihood, cost and schedule impact.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex items-end gap-3">
                <span className={cn('font-mono text-4xl font-semibold leading-none', scoreTone)}>
                  {RISK_SCORE}
                </span>
                <span className="pb-1 text-sm text-muted-foreground">/ 100</span>
                <Badge
                  variant="outline"
                  className={cn(
                    'ml-auto font-mono text-[10px] uppercase',
                    RISK_SCORE >= 70
                      ? SEVERITY_BADGE.high
                      : RISK_SCORE >= 45
                        ? SEVERITY_BADGE.medium
                        : SEVERITY_BADGE.low,
                  )}
                >
                  {scoreLabel}
                </Badge>
              </div>
              <Progress value={RISK_SCORE} />
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
                const items = RISKS.filter((r) => r.category === cat)
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
      </div>
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
  tone: Risk['severity']
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
