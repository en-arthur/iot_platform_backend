'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Cpu,
  FolderGit2,
  Settings,
  LogOut,
  ChevronDown,
  Menu,
  X,
  Plus,
  BookOpen,
  Terminal,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { createClient } from '@/lib/supabase/client';
import { useUIStore } from '@/lib/store/useUIStore';

export default function AppLayout({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

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
      {/* Sidebar Desktop & Mobile */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card transition-transform duration-200 md:static md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <Link href="/app/projects" className="flex items-center gap-2.5 font-bold tracking-tight">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow">
              <Cpu className="h-5 w-5" />
            </div>
            <span className="text-base text-foreground">AI IoT Builder</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={toggleSidebar}
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Quick Action */}
        <div className="p-4">
          <Link href="/app/projects/new">
            <Button className="w-full gap-2 shadow-sm font-semibold" size="sm">
              <Plus className="h-4 w-4" />
              <span>New Project</span>
            </Button>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
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
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Hardware Status Tag */}
        <div className="mx-3 my-2 rounded-lg border border-border/80 bg-muted/40 p-3 text-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="font-semibold text-foreground">Web Serial</span>
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
          </div>
          <p className="mt-1 text-[11px] text-muted-foreground">
            FastAPI mock mode active. Chrome USB driver connected.
          </p>
        </div>

        {/* User Footer Menu */}
        <div className="border-t border-border p-3">
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
              >
                <LogOut className="h-4 w-4 text-muted-foreground hover:text-destructive" />
              </Button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navbar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-card px-4 md:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={toggleSidebar}
              aria-label="Open sidebar"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="text-sm font-medium text-muted-foreground hidden sm:block">
              Connected to: <span className="text-foreground font-mono font-semibold">FastAPI v1.0.0</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-500 border border-emerald-500/20 hidden sm:inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Contract Synced</span>
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
