'use client'

import { Check, Loader2 } from 'lucide-react'
import { AGENT_SEQUENCE } from '@/lib/production-data'
import { useProduction } from '@/components/production-provider'
import { cn } from '@/lib/utils'

export function AgentStepper() {
  const { agents } = useProduction()
  const completed = AGENT_SEQUENCE.filter((a) => agents[a.key] === 'complete').length
  const pct = (completed / AGENT_SEQUENCE.length) * 100

  return (
    <div className="rounded-xl border border-border/60 bg-card/60 p-4 md:p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <h2 className="text-sm font-medium">Agent pipeline</h2>
        <span className="font-mono text-xs text-muted-foreground">
          {completed}/{AGENT_SEQUENCE.length} complete
        </span>
      </div>

      <div className="relative">
        <div className="absolute left-0 right-0 top-4 h-0.5 rounded-full bg-border" aria-hidden />
        <div
          className="absolute left-0 top-4 h-0.5 rounded-full bg-primary transition-all duration-500"
          style={{ width: `${pct}%` }}
          aria-hidden
        />

        <ol className="relative grid grid-cols-5 gap-1">
          {AGENT_SEQUENCE.map((agent, i) => {
            const status = agents[agent.key]
            return (
              <li key={agent.key} className="flex flex-col items-center gap-2 text-center">
                <span
                  className={cn(
                    'flex size-8 items-center justify-center rounded-full border-2 bg-card text-xs font-semibold transition-colors',
                    status === 'complete' && 'border-primary bg-primary text-primary-foreground',
                    status === 'running' && 'border-amber text-amber',
                    status === 'idle' && 'border-border text-muted-foreground',
                  )}
                >
                  {status === 'complete' ? (
                    <Check className="size-4" />
                  ) : status === 'running' ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </span>
                <span
                  className={cn(
                    'text-[11px] font-medium leading-tight sm:text-xs',
                    status === 'idle' ? 'text-muted-foreground' : 'text-foreground',
                  )}
                >
                  {agent.short}
                </span>
              </li>
            )
          })}
        </ol>
      </div>
    </div>
  )
}
