'use client'

import Link from 'next/link'
import Image from 'next/image'
import { ArrowRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty'
import { Skeleton } from '@/components/ui/skeleton'
import { useProduction } from '@/components/production-provider'
import { type AgentKey } from '@/lib/production-data'

export function AnalysisGate({
  agent,
  children,
}: {
  agent: AgentKey
  children: React.ReactNode
}) {
  const { analyzed, agents } = useProduction()

  if (!analyzed) {
    return (
      <Empty className="rounded-2xl border border-dashed border-border/70 bg-card/40 py-14">
        <EmptyHeader>
          <EmptyMedia variant="default" className="bg-transparent">
            <Image
              src="/empty-clapperboard.png"
              alt="Illustration of a clapperboard and rolled script"
              width={200}
              height={200}
              className="h-28 w-auto rounded-xl object-contain"
            />
          </EmptyMedia>
          <EmptyTitle>Nothing to show yet</EmptyTitle>
          <EmptyDescription>
            This agent needs a screenplay before it can produce output. Head back to the overview,
            paste or upload your script, and start the analysis.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button render={<Link href="/" />}>
            Go to script input
            <ArrowRight data-icon="inline-end" />
          </Button>
        </EmptyContent>
      </Empty>
    )
  }

  if (agents[agent] !== 'complete') {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm text-amber">
          <Loader2 className="size-4 animate-spin" />
          Agent is still working — results stream in as soon as the handoff completes.
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
        </div>
      </div>
    )
  }

  return <>{children}</>
}
