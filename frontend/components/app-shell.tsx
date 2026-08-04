'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Clapperboard,
  FileText,
  MapPin,
  CalendarRange,
  Wallet,
  ShieldAlert,
  RotateCcw,
} from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from '@/components/ui/sidebar'
import { Button } from '@/components/ui/button'
import { TopNav } from '@/components/top-nav'
import { useProduction } from '@/components/production-provider'
import { AGENT_SEQUENCE, type AgentKey } from '@/lib/production-data'
import { cn } from '@/lib/utils'

const NAV_ITEMS: {
  href: string
  label: string
  phase: string
  icon: typeof FileText
  agent: AgentKey
}[] = [
  { href: '/', label: 'Script Input', phase: 'Phase 01', icon: FileText, agent: 'director' },
  { href: '/director', label: 'Script Analysis', phase: 'Phase 01', icon: Clapperboard, agent: 'director' },
  { href: '/locations', label: 'Locations', phase: 'Phase 02', icon: MapPin, agent: 'location' },
  { href: '/schedule', label: 'Schedule', phase: 'Phase 03', icon: CalendarRange, agent: 'scheduler' },
  { href: '/budget', label: 'Budget', phase: 'Phase 04', icon: Wallet, agent: 'budget' },
  { href: '/risk', label: 'Risk', phase: 'Phase 05', icon: ShieldAlert, agent: 'risk' },
]

function StatusDot({ agent }: { agent: AgentKey }) {
  const { agents } = useProduction()
  const status = agents[agent]
  return (
    <span
      aria-hidden
      className={cn(
        'size-1.5 rounded-full',
        status === 'complete' && 'bg-success',
        status === 'running' && 'animate-pulse bg-amber',
        status === 'idle' && 'bg-muted-foreground/40',
      )}
    />
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { reset, analyzed } = useProduction()

  return (
    <SidebarProvider>
      <Sidebar collapsible="icon">
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" render={<Link href="/" />}>
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Clapperboard />
                </div>
                <div className="grid flex-1 text-left leading-tight">
                  <span className="truncate font-semibold">CinePilot AI</span>
                  <span className="truncate text-xs text-muted-foreground">
                    Pre-production copilot
                  </span>
                </div>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Pipeline</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {NAV_ITEMS.map((item) => (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      isActive={pathname === item.href}
                      tooltip={item.label}
                      render={<Link href={item.href} />}
                    >
                      <item.icon />
                      <span>{item.label}</span>
                    </SidebarMenuButton>
                    <SidebarMenuBadge>
                      <StatusDot agent={item.agent} />
                    </SidebarMenuBadge>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          <SidebarGroup className="group-data-[collapsible=icon]:hidden">
            <SidebarGroupLabel>Agent activity</SidebarGroupLabel>
            <SidebarGroupContent className="px-2">
              <ul className="flex flex-col gap-2 text-xs">
                {AGENT_SEQUENCE.map((agent) => (
                  <AgentActivityRow key={agent.key} agentKey={agent.key} label={agent.short} />
                ))}
              </ul>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter className="group-data-[collapsible=icon]:hidden">
          <Button
            variant="outline"
            size="sm"
            onClick={reset}
            disabled={!analyzed}
            className="w-full"
          >
            <RotateCcw data-icon="inline-start" />
            Reset project
          </Button>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset className="min-w-0">
        <TopNav />
        <div className="min-w-0 flex-1 p-4 md:p-6">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  )
}

function AgentActivityRow({ agentKey, label }: { agentKey: AgentKey; label: string }) {
  const { agents } = useProduction()
  const status = agents[agentKey]
  return (
    <li className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-2 text-sidebar-foreground/80">
        <StatusDot agent={agentKey} />
        {label}
      </span>
      <span
        className={cn(
          'font-mono text-[10px] uppercase tracking-wide',
          status === 'complete' && 'text-success',
          status === 'running' && 'text-amber',
          status === 'idle' && 'text-muted-foreground',
        )}
      >
        {status === 'complete' ? 'done' : status === 'running' ? 'running' : 'queued'}
      </span>
    </li>
  )
}
