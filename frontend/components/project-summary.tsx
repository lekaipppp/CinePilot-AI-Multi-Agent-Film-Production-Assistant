'use client'

import Image from 'next/image'
import Link from 'next/link'
import { ArrowRight, Clock, Film, Layers, User } from 'lucide-react'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { Separator } from '@/components/ui/separator'
import { useProduction } from '@/components/production-provider'
import {
  RUNTIME_MINUTES,
  SCENES,
  SCRIPT_TITLE,
  SCRIPT_WRITER,
  TOTAL_PAGES,
} from '@/lib/production-data'

export function ProjectSummary() {
  const { analyzed } = useProduction()

  if (!analyzed) {
    return (
      <Card className="border-border/60 bg-card/50">
        <CardContent>
          <Empty className="border-0 bg-transparent">
            <EmptyHeader>
              <EmptyMedia variant="default" className="bg-transparent">
                <Image
                  src="/empty-clapperboard.png"
                  alt="Illustration of a clapperboard and rolled script"
                  width={200}
                  height={200}
                  className="h-32 w-auto rounded-xl object-contain"
                />
              </EmptyMedia>
              <EmptyTitle>No script analyzed yet</EmptyTitle>
              <EmptyDescription>
                Paste a screenplay above or upload a file, then hit{' '}
                <span className="font-medium text-foreground">Start Analysis</span>. Your project
                summary, locations, schedule, budget and risk report will populate here.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        </CardContent>
      </Card>
    )
  }

  const characters = new Set(SCENES.flatMap((s) => s.characters))
  const exteriors = SCENES.filter((s) => s.intExt === 'EXT').length

  const facts = [
    { icon: Layers, label: 'Total scenes', value: String(SCENES.length) },
    { icon: Clock, label: 'Runtime estimate', value: `${RUNTIME_MINUTES} min` },
    { icon: Film, label: 'Script pages', value: TOTAL_PAGES.toFixed(2) },
    { icon: User, label: 'Speaking roles', value: String(characters.size) },
  ]

  return (
    <Card className="border-border/60 bg-card/70">
      <CardHeader>
        <CardDescription className="font-mono text-xs uppercase tracking-wider text-amber">
          Project summary
        </CardDescription>
        <CardTitle className="text-xl">{SCRIPT_TITLE}</CardTitle>
        <CardDescription>
          Written by {SCRIPT_WRITER} · Feature · Draft 4 · {exteriors} exterior scenes
        </CardDescription>
        <CardAction>
          <Badge className="bg-success/15 text-success">Breakdown ready</Badge>
        </CardAction>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {facts.map((fact) => (
            <div key={fact.label} className="flex flex-col gap-1">
              <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <fact.icon className="size-3.5" />
                {fact.label}
              </dt>
              <dd className="text-xl font-semibold tabular-nums">{fact.value}</dd>
            </div>
          ))}
        </dl>
        <Separator className="my-5" />
        <p className="text-pretty text-sm leading-relaxed text-muted-foreground">
          A hydrologist retraces a vanished aquifer across the Mojave and uncovers four decades of
          redacted water rights. Heavy exterior load, four night units, and one aerial climax on the
          salt basin.
        </p>
      </CardContent>
      <CardFooter>
        <Button
          variant="outline"
          size="sm"
          nativeButton={false}
          render={<Link href="/director" />}
        >
          Open scene breakdown
          <ArrowRight data-icon="inline-end" />
        </Button>
      </CardFooter>
    </Card>
  )
}
