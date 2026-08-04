'use client'

import * as React from 'react'
import dynamic from 'next/dynamic'
import Image from 'next/image'
import {
  Car,
  Cloud,
  CloudRain,
  MapPin,
  Ruler,
  Sun,
  Wind,
  Thermometer,
  Check,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from '@/components/ui/field'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { AnalysisGate } from '@/components/analysis-gate'
import { LOCATIONS, formatCurrency, type LocationOption } from '@/lib/production-data'
import { cn } from '@/lib/utils'

const LocationMap = dynamic(() => import('@/components/location-map'), {
  ssr: false,
  loading: () => <Skeleton className="size-full rounded-none" />,
})

const WEATHER_ICON = {
  clear: Sun,
  cloudy: Cloud,
  rain: CloudRain,
  wind: Wind,
} as const

const REGIONS = [
  { value: 'all', label: 'All regions' },
  { value: 'Death Valley, CA', label: 'Death Valley, CA' },
  { value: 'Imperial County, CA', label: 'Imperial County, CA' },
  { value: 'Independence, CA', label: 'Independence, CA' },
  { value: 'Panamint Range, CA', label: 'Panamint Range, CA' },
  { value: 'Amargosa Valley, NV', label: 'Amargosa Valley, NV' },
]

export function LocationsWorkspace() {
  const [region, setRegion] = React.useState('all')
  const [maxCost, setMaxCost] = React.useState(6000)
  const [indoor, setIndoor] = React.useState(true)
  const [outdoor, setOutdoor] = React.useState(true)
  const [weatherOnly, setWeatherOnly] = React.useState(false)
  const [permitFree, setPermitFree] = React.useState(false)
  const [selectedId, setSelectedId] = React.useState<string | null>(LOCATIONS[0].id)

  const filtered = LOCATIONS.filter((loc) => {
    if (region !== 'all' && loc.region !== region) return false
    if (loc.costPerDay > maxCost) return false
    if (loc.environment === 'indoor' && !indoor) return false
    if (loc.environment === 'outdoor' && !outdoor) return false
    if (weatherOnly && !loc.weatherDependent) return false
    if (permitFree && loc.permitRequired) return false
    return true
  })

  React.useEffect(() => {
    if (filtered.length > 0 && !filtered.some((l) => l.id === selectedId)) {
      setSelectedId(filtered[0].id)
    }
  }, [filtered, selectedId])

  const reset = () => {
    setRegion('all')
    setMaxCost(6000)
    setIndoor(true)
    setOutdoor(true)
    setWeatherOnly(false)
    setPermitFree(false)
  }

  return (
    <AnalysisGate agent="location">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
        {/* Left: filters + list */}
        <div className="flex min-w-0 flex-col gap-4">
          <Card className="border-border/60 bg-card/70">
            <CardHeader>
              <CardTitle className="text-base">Filters</CardTitle>
              <CardDescription>
                {filtered.length} of {LOCATIONS.length} recommendations match
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="region-select">Preferred region</FieldLabel>
                  <Select value={region} onValueChange={(v) => setRegion(String(v))}>
                    <SelectTrigger id="region-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {REGIONS.map((r) => (
                          <SelectItem key={r.value} value={r.value}>
                            {r.label}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </Field>

                <Field>
                  <FieldLabel htmlFor="cost-slider">
                    Max day rate
                    <span className="ml-auto font-mono text-xs tabular-nums text-amber">
                      {formatCurrency(maxCost)}
                    </span>
                  </FieldLabel>
                  <Slider
                    id="cost-slider"
                    min={1000}
                    max={6000}
                    step={100}
                    value={maxCost}
                    onValueChange={(v) => setMaxCost(Array.isArray(v) ? v[0] : v)}
                  />
                  <FieldDescription>Site fee per shoot day, excluding permits.</FieldDescription>
                </Field>

                <FieldSet>
                  <FieldLegend variant="label">Scene requirements</FieldLegend>
                  <FieldGroup className="gap-3">
                    <Field orientation="horizontal">
                      <Checkbox
                        id="f-indoor"
                        checked={indoor}
                        onCheckedChange={(c) => setIndoor(Boolean(c))}
                      />
                      <FieldLabel htmlFor="f-indoor" className="font-normal">
                        Indoor / practical interiors
                      </FieldLabel>
                    </Field>
                    <Field orientation="horizontal">
                      <Checkbox
                        id="f-outdoor"
                        checked={outdoor}
                        onCheckedChange={(c) => setOutdoor(Boolean(c))}
                      />
                      <FieldLabel htmlFor="f-outdoor" className="font-normal">
                        Outdoor / exterior
                      </FieldLabel>
                    </Field>
                    <Field orientation="horizontal">
                      <Checkbox
                        id="f-weather"
                        checked={weatherOnly}
                        onCheckedChange={(c) => setWeatherOnly(Boolean(c))}
                      />
                      <FieldLabel htmlFor="f-weather" className="font-normal">
                        Weather-dependent only
                      </FieldLabel>
                    </Field>
                    <Field orientation="horizontal">
                      <Checkbox
                        id="f-permit"
                        checked={permitFree}
                        onCheckedChange={(c) => setPermitFree(Boolean(c))}
                      />
                      <FieldLabel htmlFor="f-permit" className="font-normal">
                        No permit required
                      </FieldLabel>
                    </Field>
                  </FieldGroup>
                </FieldSet>

                <Button variant="ghost" size="sm" onClick={reset} className="w-fit">
                  Reset filters
                </Button>
              </FieldGroup>
            </CardContent>
          </Card>

          <div className="flex flex-col gap-3">
            {filtered.length === 0 ? (
              <Card className="border-dashed border-border/70 bg-card/40">
                <CardContent className="py-8 text-center text-sm text-muted-foreground">
                  No locations match these filters. Widen the day rate or region.
                </CardContent>
              </Card>
            ) : (
              filtered.map((loc) => (
                <LocationCard
                  key={loc.id}
                  location={loc}
                  active={loc.id === selectedId}
                  onSelect={() => setSelectedId(loc.id)}
                />
              ))
            )}
          </div>
        </div>

        {/* Right: map */}
        <Card className="overflow-hidden border-border/60 bg-card/70 py-0 lg:sticky lg:top-24 lg:h-[calc(100vh-8rem)]">
          <div className="flex items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <MapPin className="size-4 text-amber" />
              Scout map
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-amber" />
                Selected
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-primary" />
                Candidate
              </span>
            </div>
          </div>
          <div className="h-80 w-full lg:h-[calc(100%-3.25rem)]">
            <LocationMap locations={filtered} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
        </Card>
      </div>
    </AnalysisGate>
  )
}

function LocationCard({
  location,
  active,
  onSelect,
}: {
  location: LocationOption
  active: boolean
  onSelect: () => void
}) {
  const WeatherIcon = WEATHER_ICON[location.weather]

  return (
    <Card
      className={cn(
        'cursor-pointer gap-0 overflow-hidden border-border/60 bg-card/70 py-0 transition-colors',
        active ? 'border-amber/60 ring-1 ring-amber/30' : 'hover:border-primary/40',
      )}
      onClick={onSelect}
    >
      <div className="flex flex-col sm:flex-row">
        <div className="relative h-36 w-full shrink-0 sm:h-auto sm:w-40">
          <Image
            src={location.image || '/placeholder.svg'}
            alt={`${location.name} scout photo`}
            fill
            sizes="200px"
            className="object-cover"
          />
          {active ? (
            <span className="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-amber px-2 py-0.5 text-[10px] font-semibold text-amber-foreground">
              <Check className="size-3" />
              Selected
            </span>
          ) : null}
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex min-w-0 flex-col gap-0.5">
              <h3 className="truncate text-sm font-semibold">{location.name}</h3>
              <p className="truncate text-xs text-muted-foreground">{location.region}</p>
            </div>
            <Badge className="shrink-0 bg-primary/15 text-primary">
              {location.matchScore}% match
            </Badge>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <Badge variant="outline" className="text-[10px] capitalize">
              {location.environment}
            </Badge>
            <Badge variant="outline" className="text-[10px]">
              Sc. {location.scenes.join(', ')}
            </Badge>
            {location.permitRequired ? (
              <Badge variant="secondary" className="text-[10px]">
                Permit required
              </Badge>
            ) : null}
          </div>

          <Separator />

          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
            <div className="flex flex-col gap-0.5">
              <dt className="text-muted-foreground">Day rate</dt>
              <dd className="font-mono font-medium tabular-nums text-amber">
                {formatCurrency(location.costPerDay)}
              </dd>
            </div>
            <div className="flex flex-col gap-0.5">
              <dt className="flex items-center gap-1 text-muted-foreground">
                <WeatherIcon className="size-3" />
                Forecast
              </dt>
              <dd className="flex items-center gap-1 font-medium capitalize">
                {location.weather}
                <span className="flex items-center gap-0.5 text-muted-foreground">
                  <Thermometer className="size-3" />
                  {location.tempC}°C
                </span>
              </dd>
            </div>
            <div className="flex flex-col gap-0.5">
              <dt className="flex items-center gap-1 text-muted-foreground">
                <Ruler className="size-3" />
                Distance
              </dt>
              <dd className="font-medium tabular-nums">{location.distanceKm} km</dd>
            </div>
            <div className="flex flex-col gap-0.5">
              <dt className="flex items-center gap-1 text-muted-foreground">
                <Car className="size-3" />
                Travel
              </dt>
              <dd className="font-medium tabular-nums">{location.travelMinutes} min</dd>
            </div>
          </dl>

          <p className="text-pretty text-xs leading-relaxed text-muted-foreground">
            {location.notes}
          </p>
        </div>
      </div>
    </Card>
  )
}
