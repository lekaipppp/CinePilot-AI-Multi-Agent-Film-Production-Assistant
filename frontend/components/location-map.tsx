'use client'

import * as React from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip as LeafletTooltip, useMap } from 'react-leaflet'
import type { LocationOption } from '@/lib/production-data'
import { formatCurrency } from '@/lib/production-data'
import 'leaflet/dist/leaflet.css'

function FitBounds({ locations }: { locations: LocationOption[] }) {
  const map = useMap()
  React.useEffect(() => {
    if (locations.length === 0) return
    const bounds = locations.map((l) => [l.lat, l.lng]) as [number, number][]
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: 9 })
  }, [locations, map])
  return null
}

function Focus({ location }: { location: LocationOption | null }) {
  const map = useMap()
  React.useEffect(() => {
    if (!location) return
    map.flyTo([location.lat, location.lng], 10, { duration: 0.8 })
  }, [location, map])
  return null
}

export default function LocationMap({
  locations,
  selectedId,
  onSelect,
}: {
  locations: LocationOption[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const selected = locations.find((l) => l.id === selectedId) ?? null

  return (
    <MapContainer
      center={[36.3, -117]}
      zoom={7}
      scrollWheelZoom
      className="size-full"
      style={{ minHeight: '100%' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; OpenStreetMap &copy; CARTO'
      />
      <FitBounds locations={locations} />
      <Focus location={selected} />
      {locations.map((loc) => {
        const active = loc.id === selectedId
        return (
          <CircleMarker
            key={loc.id}
            center={[loc.lat, loc.lng]}
            radius={active ? 13 : 9}
            pathOptions={{
              color: active ? '#f4b942' : '#4a90ff',
              fillColor: active ? '#f4b942' : '#4a90ff',
              fillOpacity: active ? 0.75 : 0.4,
              weight: 2,
            }}
            eventHandlers={{ click: () => onSelect(loc.id) }}
          >
            <LeafletTooltip direction="top" offset={[0, -8]}>
              <span style={{ fontWeight: 600 }}>{loc.name}</span>
              <br />
              {formatCurrency(loc.costPerDay)} / day · Sc. {loc.scenes.join(', ')}
            </LeafletTooltip>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
