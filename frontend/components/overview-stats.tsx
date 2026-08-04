'use client'

import Link from 'next/link'
import { ArrowUpRight, CalendarRange, Gauge, MapPin, Wallet } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useProduction } from '@/components/production-provider'
import {
  LOCATIONS,
  RISK_SCORE,
  SHOOT_DAYS,
  formatCurrency,
} from '@/lib/production-data'
import { cn } from '@/lib/utils'

export function OverviewStats() {
  const { analyzed, budgetTotal, agents } = useProduction()

  const stats = [
    {
      key: 'budget',
      label: 'Budget estimate',
      value: formatCurrency(budgetTotal, true),
      sub: 'across 5 categories',
      icon: Wallet,
      href: '/budget',
      ready: agents.budget === 'complete',
      tone: 'text-primary',
    },
    {
      key: 'locations',
      label: 'Locations',
      value: String(LOCATIONS.length),
      sub: '3 outdoor · 3 indoor',
      icon: MapPin,
      href: '/locations',
      ready: agents.location === 'complete',
      tone: 'text-amber',
    },
    {
      key: 'days',
      label: 'Shoot days',
      value: String(SHOOT_DAYS),
      sub: '4 night units',
      icon: CalendarRange,
      href: '/schedule',
      ready: agents.scheduler === 'complete',
      tone: 'text-primary',
    },
    {
      key: 'risk',
      label: 'Risk score',
      value: `${RISK_SCORE}`,
      sub: 'moderate exposure',
      icon: Gauge,
      href: '/risk',
      ready: agents.risk === 'complete',
      tone: 'text-destructive',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <Card
          key={stat.key}
          className="group relative gap-0 overflow-hidden border-border/60 bg-card/70 py-0 transition-colors hover:border-primary/40"
        >
          <CardHeader className="gap-1 px-4 pt-4 pb-0">
            <CardDescription className="flex items-center gap-2 text-xs">
              <stat.icon className={cn('size-3.5', stat.tone)} />
              {stat.label}
            </CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums">
              {analyzed && stat.ready ? (
                stat.value
              ) : analyzed ? (
                <Skeleton className="h-7 w-20" />
              ) : (
                <span className="text-muted-foreground">—</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between gap-2 px-4 pt-2 pb-4">
            <span className="text-xs text-muted-foreground">
              {analyzed && stat.ready ? stat.sub : 'awaiting analysis'}
            </span>
            {analyzed && stat.ready ? (
              <Link
                href={stat.href}
                className="flex items-center gap-0.5 text-xs font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
              >
                View
                <ArrowUpRight className="size-3" />
              </Link>
            ) : (
              <Badge variant="outline" className="font-mono text-[10px]">
                queued
              </Badge>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
