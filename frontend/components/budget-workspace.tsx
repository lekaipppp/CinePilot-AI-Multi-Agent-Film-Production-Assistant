'use client'

import * as React from 'react'
import { Cell, Pie, PieChart } from 'recharts'
import { Loader2, RefreshCw, RotateCcw, TrendingDown, TrendingUp, Wallet } from 'lucide-react'
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
import { Slider } from '@/components/ui/slider'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AnalysisGate } from '@/components/analysis-gate'
import { useProduction } from '@/components/production-provider'
import {
  BUDGET_CATEGORIES,
  SHOOT_DAYS,
  formatCurrency,
} from '@/lib/production-data'
import { cn } from '@/lib/utils'

const APPROVED_TOTAL = BUDGET_CATEGORIES.reduce((sum, c) => sum + c.amount, 0)

const CHART_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
]

const chartConfig = Object.fromEntries(
  BUDGET_CATEGORIES.map((c, i) => [c.key, { label: c.label, color: CHART_COLORS[i] }]),
)

export function BudgetWorkspace() {
  const { budget, budgetTotal, budgetDirty, setBudgetValue, rerunPlan, isRunning, reset } =
    useProduction()

  const delta = budgetTotal - APPROVED_TOTAL
  const perDay = budgetTotal / SHOOT_DAYS

  const chartData = BUDGET_CATEGORIES.map((c) => ({
    key: c.key,
    label: c.label,
    value: budget[c.key] ?? c.amount,
    fill: chartConfig[c.key].color,
  }))

  return (
    <AnalysisGate agent="budget">
      <div className="flex flex-col gap-6">
        {budgetDirty && (
          <Alert>
            <RefreshCw />
            <AlertTitle>Budget changed — downstream agents are out of date</AlertTitle>
            <AlertDescription>
              Locations, schedule and risk were planned against the previous figures. Re-run the
              plan so the Location, Scheduler and Risk agents solve against your new envelope.
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
                      delta > 0 ? 'text-destructive' : delta < 0 ? 'text-success' : 'text-muted-foreground',
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
                      ? 'Matches the approved envelope'
                      : `${delta > 0 ? '+' : '−'}${formatCurrency(Math.abs(delta))} vs approved`}
                  </span>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      Per shoot day
                    </span>
                    <span className="font-mono text-lg font-semibold">
                      {formatCurrency(perDay, true)}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      Approved
                    </span>
                    <span className="font-mono text-lg font-semibold text-muted-foreground">
                      {formatCurrency(APPROVED_TOTAL, true)}
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
                        {((entry.value / budgetTotal) * 100).toFixed(1)}%
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
                Drag any line to test a scenario. Every change marks the downstream plan stale.
              </CardDescription>
              <CardAction>
                <Badge variant="outline" className="font-mono text-[10px]">
                  {BUDGET_CATEGORIES.length} LINES
                </Badge>
              </CardAction>
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              {BUDGET_CATEGORIES.map((category) => {
                const value = budget[category.key] ?? category.amount
                const categoryDelta = value - category.amount
                return (
                  <div key={category.key} className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <div className="flex flex-col gap-0.5">
                        <label
                          htmlFor={`budget-${category.key}`}
                          className="text-sm font-medium"
                        >
                          {category.label}
                        </label>
                        <span className="text-xs text-muted-foreground">{category.note}</span>
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
                      min={category.min}
                      max={category.max}
                      step={1000}
                      aria-label={`${category.label} budget`}
                      onValueChange={(next) =>
                        setBudgetValue(category.key, Array.isArray(next) ? next[0] : next)
                      }
                    />
                    <div className="flex justify-between font-mono text-[10px] text-muted-foreground">
                      <span>{formatCurrency(category.min, true)}</span>
                      <span>{formatCurrency(category.max, true)}</span>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </AnalysisGate>
  )
}
