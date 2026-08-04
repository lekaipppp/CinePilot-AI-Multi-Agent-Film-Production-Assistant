import { PageHeader } from '@/components/page-header'
import { ScriptInput } from '@/components/script-input'
import { AgentStepper } from '@/components/agent-stepper'
import { OverviewStats } from '@/components/overview-stats'
import { ProjectSummary } from '@/components/project-summary'
import { AgentActivityFeed } from '@/components/agent-activity-feed'

export default function OverviewPage() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <PageHeader
        eyebrow="OVERVIEW"
        title="Plan an entire pre-production in one pass"
        description="Five specialist agents read your screenplay, scout locations, build the board, cost it out, and flag every risk before you commit a single shoot day."
      />

      <ScriptInput />
      <AgentStepper />
      <OverviewStats />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ProjectSummary />
        </div>
        <AgentActivityFeed />
      </div>
    </main>
  )
}
