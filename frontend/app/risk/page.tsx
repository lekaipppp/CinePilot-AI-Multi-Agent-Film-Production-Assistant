import { PageHeader } from '@/components/page-header'
import { RiskWorkspace } from '@/components/risk-workspace'

export const metadata = {
  title: 'Risk Agent — Risk Assessment | CinePilot AI',
  description:
    'Weather, permit, budget, scheduling and safety risks with recommended mitigations for each.',
}

export default function RiskPage() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <PageHeader
        eyebrow="PHASE 05 · RISK AGENT"
        title="Risk assessment"
        description="The final pass reads every upstream decision and reports what could still cost you a day or a dollar — each with a concrete mitigation."
      />
      <RiskWorkspace />
    </main>
  )
}
