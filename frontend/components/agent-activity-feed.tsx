'use client'

import { Check, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useProduction } from '@/components/production-provider'
import { AGENT_SEQUENCE, type AgentKey } from '@/lib/production-data'
import { cn } from '@/lib/utils'

const LOG: Record<AgentKey, string> = {
  director: 'Parsed 7 scenes, 16.25 pages, 9 speaking roles and 21 props.',
  location: 'Scouted 6 candidate locations across 2 counties, ranked by cost and match.',
  scheduler: 'Built a 7-day board with 4 night units and 4 flagged conflicts.',
  budget: 'Costed 5 categories with a 10% weather contingency reserve.',
  risk: 'Surfaced 8 risks — 2 high severity requiring producer sign-off.',
}

export function AgentActivityFeed() {
  const { analyzed, agents } = useProduction()

  return (
    <Card className="border-border/60 bg-card/70">
      <CardHeader>
        <CardDescription className="font-mono text-xs uppercase tracking-wider text-amber">
          Agent log
        </CardDescription>
        <CardTitle className="text-base">Live handoffs</CardTitle>
      </CardHeader>
      <CardContent>
        {!analyzed ? (
          <p className="text-sm leading-relaxed text-muted-foreground">
            The orchestrator log streams here once analysis begins. Each agent passes its structured
            output to the next in the chain.
          </p>
        ) : (
          <ol className="flex flex-col gap-4">
            {AGENT_SEQUENCE.map((agent) => {
              const status = agents[agent.key]
              return (
                <li key={agent.key} className="flex gap-3">
                  <span
                    className={cn(
                      'mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border',
                      status === 'complete' && 'border-success/40 bg-success/15 text-success',
                      status === 'running' && 'border-amber/40 bg-amber/15 text-amber',
                      status === 'idle' && 'border-border bg-muted/40 text-muted-foreground',
                    )}
                  >
                    {status === 'complete' ? (
                      <Check className="size-3" />
                    ) : status === 'running' ? (
                      <Loader2 className="size-3 animate-spin" />
                    ) : (
                      <span className="size-1 rounded-full bg-current" />
                    )}
                  </span>
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-sm font-medium">{agent.label}</span>
                    <span className="text-xs leading-relaxed text-muted-foreground">
                      {status === 'complete'
                        ? LOG[agent.key]
                        : status === 'running'
                          ? 'Processing…'
                          : 'Waiting on upstream handoff.'}
                    </span>
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
