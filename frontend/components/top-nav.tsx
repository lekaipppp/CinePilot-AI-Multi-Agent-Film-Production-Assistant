'use client'

import { Check, Loader2 } from 'lucide-react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useProduction } from '@/components/production-provider'
import { AGENT_SEQUENCE, SCRIPT_TITLE } from '@/lib/production-data'
import { cn } from '@/lib/utils'

export function TopNav() {
  const { agents, analyzed } = useProduction()

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-2 border-b border-border/60 bg-background/80 px-4 backdrop-blur-xl">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-1 h-5" />

      <div className="flex min-w-0 items-center gap-2">
        <span className="truncate text-sm font-semibold">
          {analyzed ? SCRIPT_TITLE : 'Untitled project'}
        </span>
        <Badge variant="outline" className="hidden shrink-0 font-mono text-[10px] sm:inline-flex">
          {analyzed ? 'FEATURE · DRAFT 4' : 'NO SCRIPT'}
        </Badge>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <div className="hidden items-center gap-1.5 lg:flex">
          {AGENT_SEQUENCE.map((agent) => {
            const status = agents[agent.key]
            return (
              <Tooltip key={agent.key}>
                <TooltipTrigger
                  render={
                    <span
                      className={cn(
                        'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs',
                        status === 'complete' && 'border-success/30 bg-success/10 text-success',
                        status === 'running' && 'border-amber/40 bg-amber/10 text-amber',
                        status === 'idle' && 'border-border bg-muted/40 text-muted-foreground',
                      )}
                    />
                  }
                >
                  {status === 'complete' ? (
                    <Check className="size-3" />
                  ) : status === 'running' ? (
                    <Loader2 className="size-3 animate-spin" />
                  ) : (
                    <span className="size-1.5 rounded-full bg-current opacity-50" />
                  )}
                  <span className="font-medium">{agent.short}</span>
                </TooltipTrigger>
                <TooltipContent>
                  {agent.label}:{' '}
                  {status === 'complete' ? 'Complete' : status === 'running' ? 'Running…' : 'Queued'}
                </TooltipContent>
              </Tooltip>
            )
          })}
        </div>
      </div>
    </header>
  )
}
