'use client'

import * as React from 'react'
import { Download, FileText, Loader2, MapPin, ShieldAlert, Wallet } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { AnalysisGate } from '@/components/analysis-gate'
import { useProduction } from '@/components/production-provider'
import { SCRIPT_TITLE, formatCurrency } from '@/lib/production-data'
import { cn } from '@/lib/utils'

const PRINT_STYLES = `
@media print {
  [data-slot="sidebar"],
  [data-slot="sidebar-rail"],
  [data-slot="sidebar-trigger"],
  header {
    display: none !important;
  }
  [data-slot="sidebar-inset"] {
    margin: 0 !important;
  }
}
`

export function ReportWorkspace() {
  const {
    directorAnalysis,
    scheduleResult,
    budgetResult,
    riskResult,
    reportResult,
    reportError,
    selectedLocationsByScene,
    agents,
    runReport,
  } = useProduction()

  const scenes = directorAnalysis?.scenes ?? []
  const isGenerating = agents.report === 'running'
  const confirmedSceneNumbers = scenes.filter(
    (scene) => selectedLocationsByScene[scene.scene_number],
  )

  const printableRef = React.useRef<HTMLDivElement>(null)
  const [downloadingPdf, setDownloadingPdf] = React.useState(false)
  const [downloadError, setDownloadError] = React.useState<string | null>(null)

  const generatedDate = React.useMemo(
    () =>
      new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }),
    [reportResult],
  )

  const handleDownloadPdf = React.useCallback(async () => {
    if (!printableRef.current) return

    setDownloadingPdf(true)
    setDownloadError(null)

    try {
      const [{ jsPDF }, { default: html2canvas }] = await Promise.all([
        import('jspdf'),
        import('html2canvas-pro'),
      ])

      const canvas = await html2canvas(printableRef.current, { scale: 2 })
      const imgData = canvas.toDataURL('image/png')

      const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' })
      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()

      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width

      let heightLeft = imgHeight
      let position = 0

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      while (heightLeft > 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      pdf.save('cinepilot-production-report.pdf')
    } catch (error) {
      console.error('PDF generation failed:', error)
      setDownloadError('Could not generate the PDF. Please try again.')
    } finally {
      setDownloadingPdf(false)
    }
  }, [])

  return (
    <AnalysisGate agent="director">
      {scenes.length === 0 ? (
        <Card className="border-dashed border-border/70 bg-card/40">
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground">
              No scenes were returned by the Director Agent.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-6">
          <style>{PRINT_STYLES}</style>

          <Card className="border-border/60 bg-card/70 print:hidden">
            <CardHeader>
              <CardTitle className="text-base">Combined production report</CardTitle>
              <CardDescription>
                The Report Agent synthesizes an executive summary and cross-cutting highlights
                across every agent that has run so far, then combines everything into one
                printable document.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  Run Location, Scheduler, Budget, and Risk first for the most complete report —
                  missing sections are simply left out.
                </p>

                <div className="flex shrink-0 gap-2">
                  <Button
                    type="button"
                    disabled={isGenerating}
                    onClick={() => void runReport()}
                    className="bg-amber text-amber-foreground hover:bg-amber/90"
                  >
                    {isGenerating && <Loader2 className="size-4 animate-spin" />}
                    {isGenerating
                      ? 'Generating report...'
                      : reportResult
                        ? 'Regenerate report'
                        : 'Generate report'}
                  </Button>
                  {reportResult ? (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={downloadingPdf}
                      onClick={() => void handleDownloadPdf()}
                    >
                      {downloadingPdf ? (
                        <Loader2 data-icon="inline-start" className="animate-spin" />
                      ) : (
                        <Download data-icon="inline-start" />
                      )}
                      {downloadingPdf ? 'Preparing PDF...' : 'Download PDF'}
                    </Button>
                  ) : null}
                </div>
              </div>
            </CardContent>
          </Card>

          {reportError ? (
            <Card className="border-destructive/50 print:hidden">
              <CardContent className="pt-6 text-sm text-destructive">{reportError}</CardContent>
            </Card>
          ) : null}

          {downloadError ? (
            <Card className="border-destructive/50 print:hidden">
              <CardContent className="pt-6 text-sm text-destructive">{downloadError}</CardContent>
            </Card>
          ) : null}

          {!reportResult && !isGenerating && !reportError ? (
            <Card className="border-dashed border-border/70 bg-card/40 print:hidden">
              <CardContent className="flex flex-col items-center gap-2 py-14 text-center">
                <FileText className="size-8 text-muted-foreground" />
                <p className="text-sm font-medium">No report generated yet</p>
                <p className="max-w-sm text-xs text-muted-foreground">
                  Click &ldquo;Generate report&rdquo; above to have the Report Agent combine
                  everything into one document.
                </p>
              </CardContent>
            </Card>
          ) : null}

          {isGenerating ? (
            <div className="grid gap-4 sm:grid-cols-2 print:hidden">
              <div className="h-40 animate-pulse rounded-xl bg-muted/40" />
              <div className="h-40 animate-pulse rounded-xl bg-muted/40" />
            </div>
          ) : null}

          {reportResult ? (
            <div ref={printableRef} className="flex flex-col gap-6">
              <Card className="print:break-inside-avoid print:border-none print:shadow-none">
                <CardHeader>
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <CardTitle className="text-xl">{SCRIPT_TITLE}</CardTitle>
                    <span className="font-mono text-xs text-muted-foreground">
                      Generated {generatedDate}
                    </span>
                  </div>
                  <CardDescription>Combined pre-production report</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                  <p className="text-sm leading-relaxed">{reportResult.executive_summary}</p>
                  {reportResult.highlights.length > 0 ? (
                    <ul className="flex flex-col gap-2">
                      {reportResult.highlights.map((highlight, index) => (
                        <li key={index} className="flex gap-2 text-sm leading-relaxed">
                          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                          {highlight}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </CardContent>
              </Card>

              <Card className="print:break-inside-avoid print:border-none print:shadow-none">
                <CardHeader>
                  <CardTitle className="text-base">Scene breakdown</CardTitle>
                  <CardDescription>{scenes.length} scenes from the Director Agent</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-border/60 text-muted-foreground">
                          <th className="py-1.5 pr-3 font-medium">#</th>
                          <th className="py-1.5 pr-3 font-medium">Heading</th>
                          <th className="py-1.5 pr-3 font-medium">Int/Ext</th>
                          <th className="py-1.5 pr-3 font-medium">Time</th>
                          <th className="py-1.5 font-medium">Characters</th>
                        </tr>
                      </thead>
                      <tbody>
                        {scenes.map((scene) => (
                          <tr key={scene.scene_number} className="border-b border-border/30">
                            <td className="py-1.5 pr-3 font-mono">{scene.scene_number}</td>
                            <td className="py-1.5 pr-3">{scene.scene_heading}</td>
                            <td className="py-1.5 pr-3">{scene.interior_exterior}</td>
                            <td className="py-1.5 pr-3">{scene.time_of_day ?? '—'}</td>
                            <td className="py-1.5">
                              {scene.characters_in_scene.join(', ') || '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              <Card className="print:break-inside-avoid print:border-none print:shadow-none">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <MapPin className="size-4 text-muted-foreground" />
                    Locations
                  </CardTitle>
                  <CardDescription>
                    {confirmedSceneNumbers.length} of {scenes.length} scenes have a confirmed
                    location
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {confirmedSceneNumbers.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No locations confirmed yet.</p>
                  ) : (
                    <ul className="flex flex-col gap-2 text-sm">
                      {confirmedSceneNumbers.map((scene) => {
                        const entry = selectedLocationsByScene[scene.scene_number]
                        return (
                          <li
                            key={scene.scene_number}
                            className="flex flex-wrap items-center justify-between gap-2 border-b border-border/30 pb-2"
                          >
                            <span>
                              <span className="font-mono text-xs text-muted-foreground">
                                Scene {scene.scene_number}
                              </span>{' '}
                              {entry.candidate.place_name}
                            </span>
                            <span className="flex items-center gap-2">
                              {entry.candidate.price != null ? (
                                <span className="font-mono text-xs text-muted-foreground">
                                  {formatCurrency(entry.candidate.price)}
                                  {entry.candidate.price_unit &&
                                  entry.candidate.price_unit !== 'unknown'
                                    ? ` / ${entry.candidate.price_unit}`
                                    : ''}
                                </span>
                              ) : null}
                              <Badge variant="outline" className="text-[10px] uppercase">
                                {entry.status}
                              </Badge>
                            </span>
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </CardContent>
              </Card>

              <Card className="print:break-inside-avoid print:border-none print:shadow-none">
                <CardHeader>
                  <CardTitle className="text-base">Shoot schedule</CardTitle>
                  <CardDescription>
                    {scheduleResult
                      ? `${scheduleResult.total_shoot_days} shoot days · ${scheduleResult.night_block_count} night blocks`
                      : 'Not generated yet'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!scheduleResult ? (
                    <p className="text-sm text-muted-foreground">
                      Run the Scheduler Agent to include a shoot schedule.
                    </p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-border/60 text-muted-foreground">
                            <th className="py-1.5 pr-3 font-medium">Day</th>
                            <th className="py-1.5 pr-3 font-medium">Call time</th>
                            <th className="py-1.5 pr-3 font-medium">Scene</th>
                            <th className="py-1.5 font-medium">Location</th>
                          </tr>
                        </thead>
                        <tbody>
                          {scheduleResult.schedule.map((block) => (
                            <tr key={block.scene_number} className="border-b border-border/30">
                              <td className="py-1.5 pr-3 font-mono">{block.shoot_day}</td>
                              <td className="py-1.5 pr-3 font-mono">{block.call_time}</td>
                              <td className="py-1.5 pr-3">
                                {block.scene_number} · {block.scene_heading}
                              </td>
                              <td className="py-1.5">{block.location_name ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="print:break-inside-avoid print:border-none print:shadow-none">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Wallet className="size-4 text-muted-foreground" />
                    Budget
                  </CardTitle>
                  <CardDescription>
                    {budgetResult
                      ? `Total ${formatCurrency(budgetResult.total_estimated_amount)}`
                      : 'Not generated yet'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!budgetResult ? (
                    <p className="text-sm text-muted-foreground">
                      Run the Budget Agent to include a cost breakdown.
                    </p>
                  ) : (
                    <ul className="flex flex-col gap-2 text-sm">
                      {budgetResult.line_items.map((item) => (
                        <li
                          key={item.key}
                          className="flex items-start justify-between gap-3 border-b border-border/30 pb-2"
                        >
                          <span>
                            <span className="font-medium">{item.label}</span>
                            <p className="text-xs text-muted-foreground">{item.note}</p>
                          </span>
                          <span className="shrink-0 font-mono text-xs">
                            {formatCurrency(item.estimated_amount)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>

              <Card className="print:break-inside-avoid print:border-none print:shadow-none">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <ShieldAlert className="size-4 text-muted-foreground" />
                    Risk register
                  </CardTitle>
                  <CardDescription>
                    {riskResult
                      ? `${riskResult.risks.length} identified risks`
                      : 'Not generated yet'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!riskResult ? (
                    <p className="text-sm text-muted-foreground">
                      Run the Risk Agent to include a risk register.
                    </p>
                  ) : riskResult.risks.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No risks identified.</p>
                  ) : (
                    <ul className="flex flex-col gap-2 text-sm">
                      {riskResult.risks.map((risk) => (
                        <li
                          key={risk.id}
                          className="flex items-start justify-between gap-3 border-b border-border/30 pb-2"
                        >
                          <span>
                            <span className="font-medium">{risk.title}</span>
                            <p className="text-xs text-muted-foreground">
                              {risk.scope} · {risk.recommendation}
                            </p>
                          </span>
                          <Badge
                            variant="outline"
                            className={cn(
                              'shrink-0 font-mono text-[10px] uppercase',
                              risk.severity === 'high' &&
                                'border-destructive/40 bg-destructive/12 text-destructive',
                              risk.severity === 'medium' &&
                                'border-amber/40 bg-amber/12 text-amber',
                              risk.severity === 'low' &&
                                'border-success/35 bg-success/10 text-success',
                            )}
                          >
                            {risk.severity}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      )}
    </AnalysisGate>
  )
}
