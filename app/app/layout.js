'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Cpu,
  FolderGit2,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { createClient } from '@/lib/supabase/client';
import { useUIStore } from '@/lib/store/useUIStore';

export default function AppLayout({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

  const handleSignOut = async () => {
    if (isMock) {
      document.cookie = 'ai_iot_mock_auth=; path=/; max-age=0';
      router.push('/sign-in');
      return;
    }
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push('/sign-in');
  };

  const navItems = [
    { label: 'Projects', href: '/app/projects', icon: FolderGit2 },
    { label: 'Settings', href: '/app/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile Backdrop Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}

      {/* Adjustable Sidebar (Closed/Icon-only by default on desktop) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-all duration-300 ease-in-out md:static ${
          // Mobile: slide in/out
          sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0'
        } ${
          // Desktop: w-64 when open, w-16 when closed (icon-only rail)
          sidebarOpen ? 'md:w-64' : 'md:w-16'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex h-16 items-center justify-between border-b border-border px-3">
          <Link
            href="/app/projects"
            className="flex items-center gap-2.5 font-bold tracking-tight overflow-hidden"
            title="AI IoT Builder"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow">
              <Cpu className="h-5 w-5" />
            </div>
            {sidebarOpen && (
              <span className="text-base text-foreground truncate whitespace-nowrap transition-opacity duration-200">
                AI IoT Builder
              </span>
            )}
          </Link>

          {/* Toggle Button on Desktop & Close Button on Mobile */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="shrink-0 h-8 w-8 text-muted-foreground hover:text-foreground"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <span className="md:hidden">
              <X className="h-4 w-4" />
            </span>
            <span className="hidden md:block">
              {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </span>
          </Button>
        </div>

        {/* Quick Action: New Project */}
        <div className="p-2.5">
          {sidebarOpen ? (
            <Link href="/app/projects/new">
              <Button className="w-full gap-2 shadow-sm font-semibold" size="sm">
                <Plus className="h-4 w-4 shrink-0" />
                <span className="truncate">New Project</span>
              </Button>
            </Link>
          ) : (
            <Tooltip text="New Project">
              <Link href="/app/projects/new" className="block w-full">
                <Button size="icon" className="h-9 w-9 mx-auto shadow-sm" aria-label="New Project">
                  <Plus className="h-4 w-4" />
                </Button>
              </Link>
            </Tooltip>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1.5 px-2 py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);

            if (!sidebarOpen) {
              return (
                <div key={item.href} className="flex justify-center">
                  <Tooltip text={item.label}>
                    <Link
                      href={item.href}
                      aria-label={item.label}
                      className={`flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground shadow-sm'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                    </Link>
                  </Tooltip>
                </div>
              );
            }

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Hardware Status Tag (Full when open, minimal dot when collapsed) */}
        {sidebarOpen ? (
          <div className="mx-3 my-2 rounded-lg border border-border/80 bg-muted/40 p-3 text-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="font-semibold text-foreground">Web Serial</span>
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              FastAPI mock mode active. Chrome USB driver connected.
            </p>
          </div>
        ) : (
          <div className="my-2 flex justify-center">
            <Tooltip text="Web Serial Connected">
              <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-500/20" />
            </Tooltip>
          </div>
        )}

        {/* User Footer Menu */}
        <div className="border-t border-border p-2">
          {sidebarOpen ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5 truncate">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                  SC
                </div>
                <div className="truncate text-left">
                  <div className="truncate text-xs font-semibold text-foreground">Sarah Chen</div>
                  <div className="truncate text-[10px] text-muted-foreground">Hardware Engineer</div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <ThemeToggle />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSignOut}
                  title="Sign out"
                  aria-label="Sign out"
                  className="h-8 w-8"
                >
                  <LogOut className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Tooltip text="Sarah Chen (Hardware Engineer)">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary cursor-default">
                  SC
                </div>
              </Tooltip>
              <Tooltip text="Toggle theme">
                <div>
                  <ThemeToggle />
                </div>
              </Tooltip>
              <Tooltip text="Sign out">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSignOut}
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  aria-label="Sign out"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </Tooltip>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        {/* Top Navbar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-card px-4 md:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="text-sm font-medium text-muted-foreground hidden sm:block">
              Server: <span className="text-foreground font-semibold">Online</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-500 border border-emerald-500/20 hidden sm:inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>System Ready</span>
            </span>
          </div>
        </header>

        {/* Content View */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
