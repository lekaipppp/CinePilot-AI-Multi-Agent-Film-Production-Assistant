'use client'

import * as React from 'react'
import { Cell, Pie, PieChart } from 'recharts'
import {
  Loader2,
  RefreshCw,
  RotateCcw,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { AnalysisGate } from '@/components/analysis-gate'
import { useProduction } from '@/components/production-provider'
import type { BudgetLineItem } from '@/lib/budget-api'
import { formatCurrency } from '@/lib/production-data'
import { cn } from '@/lib/utils'

const CATEGORY_META: { key: BudgetLineItem['key']; label: string; color: string }[] = [
  { key: 'locations', label: 'Locations', color: 'var(--chart-1)' },
  { key: 'equipment', label: 'Equipment', color: 'var(--chart-2)' },
  { key: 'crew', label: 'Crew', color: 'var(--chart-3)' },
  { key: 'transportation', label: 'Transportation', color: 'var(--chart-4)' },
  { key: 'contingency', label: 'Contingency', color: 'var(--chart-5)' },
]

const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CAD']

const chartConfig = Object.fromEntries(
  CATEGORY_META.map((c) => [c.key, { label: c.label, color: c.color }]),
)

export function BudgetWorkspace() {
  const {
    directorAnalysis,
    scheduleResult,
    budgetResult,
    budgetError,
    budgetOverrides,
    budgetDirty,
    setBudgetValue,
    runBudget,
    rerunPlan,
    agents,
    isRunning,
    reset,
  } = useProduction()

  const scenes = directorAnalysis?.scenes ?? []

  const [targetBudget, setTargetBudget] = React.useState('150000')
  const [currency, setCurrency] = React.useState('EUR')
  const [additionalConstraints, setAdditionalConstraints] = React.useState('')

  const isGenerating = agents.budget === 'running'

  const lineItemByKey = React.useMemo(() => {
    const map = new Map<string, BudgetLineItem>()
    for (const item of budgetResult?.line_items ?? []) {
      map.set(item.key, item)
    }
    return map
  }, [budgetResult])

  const effectiveAmount = (key: string, fallback: number) => budgetOverrides[key] ?? fallback

  const budgetTotal = CATEGORY_META.reduce((sum, category) => {
    const item = lineItemByKey.get(category.key)
    return sum + effectiveAmount(category.key, item?.estimated_amount ?? 0)
  }, 0)

  const targetBudgetNumber = Number(targetBudget)
  const delta = budgetResult ? budgetTotal - targetBudgetNumber : 0
  const perDay =
    budgetResult && scheduleResult?.total_shoot_days
      ? budgetTotal / scheduleResult.total_shoot_days
      : null

  const chartData = CATEGORY_META.map((category) => {
    const item = lineItemByKey.get(category.key)
    return {
      key: category.key,
      label: category.label,
      value: effectiveAmount(category.key, item?.estimated_amount ?? 0),
      fill: category.color,
    }
  })

  const generateDisabled = scenes.length === 0 || !targetBudgetNumber || targetBudgetNumber <= 0

  const handleGenerate = () => {
    void runBudget(targetBudgetNumber, currency, additionalConstraints.trim())
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
              <CardTitle className="text-base">Budget preferences</CardTitle>
              <CardDescription>
                Set a target budget and currency, and any known costs or discounts the Budget
                Agent should treat as constraints.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="target-budget" className="text-sm font-medium">
                    Target budget
                  </label>
                  <div className="flex gap-2">
                    <div className="relative min-w-0 flex-1">
                      <Wallet className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="target-budget"
                        type="number"
                        min="0"
                        step="1000"
                        value={targetBudget}
                        onChange={(event) => setTargetBudget(event.target.value)}
                        className="pl-9"
                      />
                    </div>
                    <Select value={currency} onValueChange={(value) => setCurrency(String(value))}>
                      <SelectTrigger className="w-24" aria-label="Budget currency">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CURRENCIES.map((c) => (
                          <SelectItem key={c} value={c}>
                            {c}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Treated as a soft goal — the agent will not hide real costs to fit it.
                  </p>
                </div>

                <div className="space-y-2">
                  <label htmlFor="budget-additional-constraints" className="text-sm font-medium">
                    Additional constraints
                    <span className="ml-1 font-normal text-muted-foreground">(optional)</span>
                  </label>
                  <Textarea
                    id="budget-additional-constraints"
                    value={additionalConstraints}
                    onChange={(event) => setAdditionalConstraints(event.target.value)}
                    maxLength={500}
                    rows={2}
                    placeholder="For example: aerial unit is donated, exclude catering, crew day rate fixed at €450."
                    className="resize-none"
                  />
                </div>
              </div>

              <Separator />

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  The Budget Agent grounds the locations line in your confirmed candidates'
                  pricing and estimates the rest from production scale.
                </p>

                <Button
                  type="button"
                  disabled={generateDisabled || isGenerating}
                  onClick={handleGenerate}
                  className="shrink-0 bg-amber text-amber-foreground hover:bg-amber/90"
                >
                  {isGenerating && <Loader2 className="size-4 animate-spin" />}
                  {isGenerating ? 'Generating budget...' : 'Generate budget'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {budgetError && (
            <Card className="border-destructive/50">
              <CardContent className="pt-6 text-sm text-destructive">{budgetError}</CardContent>
            </Card>
          )}

          {!budgetResult && !isGenerating && !budgetError && (
            <Card className="border-dashed border-border/70 bg-card/40">
              <CardContent className="flex flex-col items-center gap-2 py-14 text-center">
                <Wallet className="size-8 text-muted-foreground" />
                <p className="text-sm font-medium">No budget generated yet</p>
                <p className="max-w-sm text-xs text-muted-foreground">
                  Set your target budget above and click &ldquo;Generate budget&rdquo; to have
                  the Budget Agent estimate costs from the {scenes.length} scenes Director Agent
                  extracted.
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

          {budgetResult && (
            <>
              {budgetDirty && (
                <Alert>
                  <RefreshCw />
                  <AlertTitle>Budget changed — Location and Scheduler are marked stale</AlertTitle>
                  <AlertDescription>
                    Re-running builds a fresh budget from your new envelope and pre-fills the
                    Locations page with a tighter per-scene day-rate cap. Location and Scheduler
                    are marked for review — re-run each of them manually on their own pages when
                    you're ready.
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid gap-6 xl:grid-cols-[1fr_1.4fr]">
                <div className="flex flex-col gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Total budget</CardTitle>
                      <CardDescription>Live total across all five categories.</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-4">
                      <div className="flex flex-col gap-1">
                        <span className="font-mono text-3xl font-semibold tracking-tight">
                          {formatCurrency(budgetTotal)}
                        </span>
                        <span
                          className={cn(
                            'flex items-center gap-1.5 text-sm',
                            delta > 0
                              ? 'text-destructive'
                              : delta < 0
                                ? 'text-success'
                                : 'text-muted-foreground',
                          )}
                        >
                          {delta > 0 ? (
                            <TrendingUp className="size-4" />
                          ) : delta < 0 ? (
                            <TrendingDown className="size-4" />
                          ) : (
                            <Wallet className="size-4" />
                          )}
                          {delta === 0
                            ? 'Matches your target'
                            : `${delta > 0 ? '+' : '−'}${formatCurrency(Math.abs(delta))} vs target`}
                        </span>
                      </div>

                      <Separator />

                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
                            Per shoot day
                          </span>
                          <span className="font-mono text-lg font-semibold">
                            {perDay !== null ? (
                              formatCurrency(perDay, true)
                            ) : (
                              <span className="text-sm font-normal text-muted-foreground">
                                Generate a schedule first
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
                            Target
                          </span>
                          <span className="font-mono text-lg font-semibold text-muted-foreground">
                            {formatCurrency(targetBudgetNumber, true)}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                    <CardFooter className="flex-col items-stretch gap-2">
                      <Button onClick={rerunPlan} disabled={isRunning || !budgetDirty}>
                        {isRunning ? (
                          <Loader2 data-icon="inline-start" className="animate-spin" />
                        ) : (
                          <RefreshCw data-icon="inline-start" />
                        )}
                        {isRunning ? 'Re-planning…' : 'Re-run downstream plan'}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={reset}>
                        <RotateCcw data-icon="inline-start" />
                        Reset project
                      </Button>
                    </CardFooter>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Allocation</CardTitle>
                      <CardDescription>Share of spend by category.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-[240px]">
                        <PieChart>
                          <ChartTooltip
                            content={
                              <ChartTooltipContent
                                nameKey="label"
                                formatter={(value) => formatCurrency(Number(value))}
                              />
                            }
                          />
                          <Pie data={chartData} dataKey="value" nameKey="label" innerRadius={55} strokeWidth={2}>
                            {chartData.map((entry) => (
                              <Cell key={entry.key} fill={entry.fill} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ChartContainer>
                      <ul className="mt-2 flex flex-col gap-2">
                        {chartData.map((entry) => (
                          <li key={entry.key} className="flex items-center gap-2 text-sm">
                            <span
                              aria-hidden
                              className="size-2.5 shrink-0 rounded-sm"
                              style={{ backgroundColor: entry.fill }}
                            />
                            <span className="flex-1 truncate">{entry.label}</span>
                            <span className="font-mono text-xs text-muted-foreground">
                              {budgetTotal > 0 ? ((entry.value / budgetTotal) * 100).toFixed(1) : '0.0'}%
                            </span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle>Category controls</CardTitle>
                    <CardDescription>
                      Drag any line to test a scenario. Every change marks the downstream plan
                      stale.
                    </CardDescription>
                    <CardAction>
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {CATEGORY_META.length} LINES
                      </Badge>
                    </CardAction>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-6">
                    {CATEGORY_META.map((category) => {
                      const item = lineItemByKey.get(category.key)
                      const baseline = item?.estimated_amount ?? 0
                      const value = effectiveAmount(category.key, baseline)
                      const categoryDelta = value - baseline
                      const maxSlider = Math.max(baseline * 2, value, 1000)

                      return (
                        <div key={category.key} className="flex flex-col gap-3">
                          <div className="flex flex-wrap items-baseline justify-between gap-2">
                            <div className="flex flex-col gap-0.5">
                              <label htmlFor={`budget-${category.key}`} className="text-sm font-medium">
                                {category.label}
                              </label>
                              <span className="text-xs text-muted-foreground">
                                {item?.note ?? 'No estimate returned for this category.'}
                              </span>
                            </div>
                            <div className="flex flex-col items-end gap-0.5">
                              <span className="font-mono text-base font-semibold">
                                {formatCurrency(value)}
                              </span>
                              {categoryDelta !== 0 && (
                                <span
                                  className={cn(
                                    'font-mono text-[11px]',
                                    categoryDelta > 0 ? 'text-destructive' : 'text-success',
                                  )}
                                >
                                  {categoryDelta > 0 ? '+' : '−'}
                                  {formatCurrency(Math.abs(categoryDelta), true)}
                                </span>
                              )}
                            </div>
                          </div>
                          <Slider
                            id={`budget-${category.key}`}
                            value={value}
                            min={0}
                            max={maxSlider}
                            step={1000}
                            aria-label={`${category.label} budget`}
                            onValueChange={(next) =>
                              setBudgetValue(category.key, Array.isArray(next) ? next[0] : next)
                            }
                          />
                          <div className="flex justify-between font-mono text-[10px] text-muted-foreground">
                            <span>{formatCurrency(0, true)}</span>
                            <span>{formatCurrency(maxSlider, true)}</span>
                          </div>
                        </div>
                      )
                    })}
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
