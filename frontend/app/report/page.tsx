import { PageHeader } from '@/components/page-header'
import { ReportWorkspace } from '@/components/report-workspace'

export const metadata = {
  title: 'Report Agent — Production Report | CinePilot AI',
  description:
    'A single combined report synthesizing every agent\'s output, ready to export as a PDF.',
}

export default function ReportPage() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <PageHeader
        eyebrow="PHASE 06 · REPORT AGENT"
        title="Production report"
        description="One combined, AI-organized document pulling together the script breakdown, locations, schedule, budget, and risk register — ready to download as a PDF."
      />
      <ReportWorkspace />
    </main>
  )
}
