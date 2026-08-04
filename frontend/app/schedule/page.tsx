import { PageHeader } from '@/components/page-header'
import { ScheduleWorkspace } from '@/components/schedule-workspace'

export const metadata = {
  title: 'Scheduler Agent — Shooting Schedule | CinePilot AI',
  description:
    'Optimised day-by-day shooting schedule solved against actor, crew and weather constraints.',
}

export default function SchedulePage() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <PageHeader
        eyebrow="PHASE 03 · SCHEDULER AGENT"
        title="Shooting schedule"
        description="Scenes grouped into shoot days that respect cast availability, crew bookings and weather windows — with every remaining conflict surfaced."
      />
      <ScheduleWorkspace />
    </main>
  )
}
