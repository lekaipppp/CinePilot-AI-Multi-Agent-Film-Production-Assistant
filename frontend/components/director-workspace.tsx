'use client'

import * as React from 'react'
import { LayoutGrid, Rows3, Sun, Moon, Sunrise, Sunset } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Separator } from '@/components/ui/separator'
import { AnalysisGate } from '@/components/analysis-gate'
import type { DirectorScene } from '@/lib/director-api'
import { useProduction } from '@/components/production-provider'

const TIME_ICON = {
  DAY: Sun,
  NIGHT: Moon,
  DAWN: Sunrise,
  DUSK: Sunset,
} as const

function TimeBadge({ scene }: { scene: DirectorScene }) {
  const normalized = scene.time_of_day?.toUpperCase()
  const Icon = normalized && normalized in TIME_ICON ? TIME_ICON[normalized as keyof typeof TIME_ICON] : Sun
  return (
    <Badge variant={normalized === 'NIGHT' ? 'secondary' : 'outline'} className="gap-1">
      <Icon className="size-3" />
      {normalized ?? 'UNSPECIFIED'}
    </Badge>
  )
}

export function DirectorWorkspace() {
  const [view, setView] = React.useState('table')
  const { directorAnalysis } = useProduction()
  const scenes = directorAnalysis?.scenes ?? []

  const characters = new Set(scenes.flatMap((s) => s.characters_in_scene))
  const props = new Set(scenes.flatMap((s) => s.props_in_scene))

  return (
    <AnalysisGate agent="director">
      <div className="flex flex-col gap-5">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[
            { label: 'Scenes parsed', value: scenes.length },
            { label: 'Evidence excerpts', value: scenes.reduce((sum, scene) => sum + scene.source_evidence.length, 0) },
            { label: 'Unique characters', value: characters.size },
            { label: 'Props tracked', value: props.size },
          ].map((s) => (
            <Card key={s.label} className="gap-0 border-border/60 bg-card/70 py-0">
              <CardHeader className="gap-1 px-4 py-4">
                <CardDescription className="text-xs">{s.label}</CardDescription>
                <CardTitle className="text-2xl tabular-nums">{s.value}</CardTitle>
              </CardHeader>
            </Card>
          ))}
        </div>

        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium text-muted-foreground">Scene breakdown</h2>
          <ToggleGroup
            value={[view]}
            onValueChange={(v) => setView(v[0] ?? 'table')}
            className="shrink-0"
          >
            <ToggleGroupItem value="table" aria-label="Table view">
              <Rows3 />
              <span className="hidden sm:inline">Table</span>
            </ToggleGroupItem>
            <ToggleGroupItem value="cards" aria-label="Card view">
              <LayoutGrid />
              <span className="hidden sm:inline">Cards</span>
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        {view === 'table' ? <SceneTable scenes={scenes} /> : <SceneCards scenes={scenes} />}
      </div>
    </AnalysisGate>
  )
}

function SceneTable({ scenes }: { scenes: DirectorScene[] }) {
  return (
    <Card className="overflow-hidden border-border/60 bg-card/70 py-0">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-16">Scene</TableHead>
              <TableHead className="min-w-56">Slug line</TableHead>
              <TableHead className="min-w-40">Characters</TableHead>
              <TableHead className="min-w-40">Location type</TableHead>
              <TableHead className="min-w-44">Props</TableHead>
              <TableHead className="min-w-56">Shooting requirements</TableHead>
              <TableHead className="min-w-48">Source evidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {scenes.map((scene) => (
              <TableRow key={scene.scene_number}>
                <TableCell className="font-mono text-xs text-amber">
                  {String(scene.scene_number).padStart(2, '0')}
                </TableCell>
                <TableCell>
                  <div className="flex flex-col gap-1.5">
                    <span className="text-sm font-medium">{scene.scene_heading}</span>
                    <div className="flex gap-1.5">
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {scene.interior_exterior}
                      </Badge>
                      <TimeBadge scene={scene} />
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {scene.characters_in_scene.join(', ') || '—'}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {scene.location_setting ?? '—'}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {scene.props_in_scene.join(', ') || '—'}
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {scene.shooting_requirements.map((r) => (
                      <Badge key={r} variant="secondary" className="text-[10px] font-normal">
                        {r}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {scene.source_evidence.join(' · ') || '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}

function SceneCards({ scenes }: { scenes: DirectorScene[] }) {
  return (
    <Accordion className="flex flex-col gap-3">
      {scenes.map((scene) => (
        <AccordionItem
          key={scene.scene_number}
          value={`scene-${scene.scene_number}`}
          className="rounded-xl border border-border/60 bg-card/70 px-4 last:border-b"
        >
          <AccordionTrigger className="hover:no-underline">
            <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2.5 pr-2 text-left">
              <span className="font-mono text-xs text-amber">
                {String(scene.scene_number).padStart(2, '0')}
              </span>
              <span className="min-w-0 truncate text-sm font-medium">{scene.scene_heading}</span>
              <TimeBadge scene={scene} />
              <span className="ml-auto shrink-0 text-xs text-muted-foreground">{scene.interior_exterior}</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <p className="text-pretty text-sm leading-relaxed text-muted-foreground">
              {scene.source_evidence.join(' · ') || 'No source excerpt returned.'}
            </p>
            <Separator className="my-4" />
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Characters
                </dt>
                <dd className="flex flex-wrap gap-1.5">
                  {scene.characters_in_scene.map((c) => (
                    <Badge key={c} variant="outline">
                      {c}
                    </Badge>
                  ))}
                </dd>
              </div>
              <div className="flex flex-col gap-1.5">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Location type
                </dt>
                <dd className="text-sm">{scene.location_setting ?? 'Unspecified'}</dd>
              </div>
              <div className="flex flex-col gap-1.5">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Props
                </dt>
                <dd className="flex flex-wrap gap-1.5">
                  {scene.props_in_scene.map((p) => (
                    <Badge key={p} variant="secondary" className="font-normal">
                      {p}
                    </Badge>
                  ))}
                </dd>
              </div>
              <div className="flex flex-col gap-1.5">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Shooting requirements
                </dt>
                <dd className="flex flex-wrap gap-1.5">
                  {scene.shooting_requirements.map((r) => (
                    <Badge key={r} className="bg-primary/15 font-normal text-primary">
                      {r}
                    </Badge>
                  ))}
                </dd>
              </div>
            </dl>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
