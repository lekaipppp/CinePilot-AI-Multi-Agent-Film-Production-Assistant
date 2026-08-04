import { PageHeader } from '@/components/page-header'
import { LocationsWorkspace } from '@/components/locations-workspace'

export const metadata = {
  title: 'Location Agent — Recommendations | CinePilot AI',
  description: 'Ranked location recommendations with cost, weather and travel-time analysis.',
}

export default function LocationsPage() {
  return (
    <main className="mx-auto flex w-full max-w-[100rem] flex-col gap-6">
      <PageHeader
        eyebrow="PHASE 02 · LOCATION AGENT"
        title="Location recommendations"
        description="Candidate sites ranked against every scene requirement, with day rates, forecasts and unit-move times already factored in."
      />
      <LocationsWorkspace />
    </main>
  )
}
