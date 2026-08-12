'use client'

import * as React from 'react'
import {
  CircleMarker,
  MapContainer,
  TileLayer,
  Tooltip as LeafletTooltip,
  useMap,
} from 'react-leaflet'

import type { LocationCandidate } from '@/lib/location-api'

import 'leaflet/dist/leaflet.css'

type MappableCandidate = LocationCandidate & {
  latitude: number
  longitude: number
}

function hasCoordinates(
  candidate: LocationCandidate,
): candidate is MappableCandidate {
  return (
    typeof candidate.latitude === 'number' &&
    Number.isFinite(candidate.latitude) &&
    typeof candidate.longitude === 'number' &&
    Number.isFinite(candidate.longitude)
  )
}

function FitCandidateBounds({
  candidates,
}: {
  candidates: MappableCandidate[]
}) {
  const map = useMap()

  React.useEffect(() => {
    if (candidates.length === 0) return

    if (candidates.length === 1) {
      map.setView(
        [candidates[0].latitude, candidates[0].longitude],
        13,
      )
      return
    }

    map.fitBounds(
      candidates.map((candidate) => [
        candidate.latitude,
        candidate.longitude,
      ]),
      {
        padding: [48, 48],
        maxZoom: 13,
      },
    )
  }, [candidates, map])

  return null
}

function FocusCandidate({
  candidate,
}: {
  candidate: MappableCandidate | null
}) {
  const map = useMap()

  React.useEffect(() => {
    if (!candidate) return

    map.flyTo(
      [candidate.latitude, candidate.longitude],
      14,
      {
        duration: 0.8,
      },
    )
  }, [candidate, map])

  return null
}

export default function LocationMap({
  candidates,
  selectedId,
  onSelect,
}: {
  candidates: LocationCandidate[]
  selectedId: string | null
  onSelect: (locationId: string) => void
}) {
  const mappableCandidates = candidates.filter(hasCoordinates)

  const selectedCandidate =
    mappableCandidates.find(
      (candidate) => candidate.location_id === selectedId,
    ) ?? null

  if (mappableCandidates.length === 0) {
    return (
      <div className="flex size-full min-h-[420px] items-center justify-center bg-[#101820] p-6 text-center">
        <div className="max-w-sm">
          <p className="font-medium text-white">
            No map coordinates available
          </p>

          <p className="mt-2 text-sm leading-relaxed text-white/60">
            The locations were found, but their sources did not provide
            coordinates. They can still be reviewed in the candidate
            cards below.
          </p>
        </div>
      </div>
    )
  }

  return (
    <MapContainer
      center={[
        mappableCandidates[0].latitude,
        mappableCandidates[0].longitude,
      ]}
      zoom={12}
      scrollWheelZoom
      className="size-full"
      style={{ minHeight: '420px' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution="&copy; OpenStreetMap contributors &copy; CARTO"
      />

      <FitCandidateBounds candidates={mappableCandidates} />

      <FocusCandidate candidate={selectedCandidate} />

      {mappableCandidates.map((candidate) => {
        const selected =
          candidate.location_id === selectedId

        return (
          <CircleMarker
            key={candidate.location_id}
            center={[
              candidate.latitude,
              candidate.longitude,
            ]}
            radius={selected ? 13 : 9}
            pathOptions={{
              color: selected ? '#f4b942' : '#4a90ff',
              fillColor: selected ? '#f4b942' : '#4a90ff',
              fillOpacity: selected ? 0.8 : 0.5,
              weight: 2,
            }}
            eventHandlers={{
              click: () => onSelect(candidate.location_id),
            }}
          >
            <LeafletTooltip
              direction="top"
              offset={[0, -8]}
            >
              <div>
                <strong>{candidate.place_name}</strong>

                <br />

                {candidate.match_score}% match

                {candidate.address
                  ? ` · ${candidate.address}`
                  : ''}
              </div>
            </LeafletTooltip>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}