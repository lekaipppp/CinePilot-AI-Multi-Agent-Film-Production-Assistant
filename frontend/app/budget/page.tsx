import { PageHeader } from '@/components/page-header'
import { BudgetWorkspace } from '@/components/budget-workspace'

export const metadata = {
  title: 'Budget Agent — Cost Estimation | CinePilot AI',
  description:
    'Interactive budget breakdown across locations, equipment, crew, transportation and contingency.',
}

export default function BudgetPage() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <PageHeader
        eyebrow="PHASE 04 · BUDGET AGENT"
        title="Cost estimation"
        description="A live cost model built from the locked schedule. Adjust any category to test a scenario, then re-run the plan to propagate it downstream."
      />
      <BudgetWorkspace />
    </main>
  )
}
