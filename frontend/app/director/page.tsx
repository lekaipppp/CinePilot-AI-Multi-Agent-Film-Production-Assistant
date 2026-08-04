import { PageHeader } from '@/components/page-header'
import { DirectorWorkspace } from '@/components/director-workspace'

export const metadata = {
  title: 'Director Agent — Script Analysis | CinePilot AI',
  description: 'Scene-by-scene screenplay breakdown with characters, props and shooting requirements.',
}

export default function DirectorPage() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <PageHeader
        eyebrow="PHASE 01 · DIRECTOR AGENT"
        title="Script analysis"
        description="Every scene parsed into characters, location type, props and shooting requirements — the structured handoff every downstream agent reads from."
      />
      <DirectorWorkspace />
    </main>
  )
}
