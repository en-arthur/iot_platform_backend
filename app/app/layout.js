'use client';

import React from 'react';
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
  Usb,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { createClient } from '@/lib/supabase/client';
import { useUIStore } from '@/lib/store/useUIStore';

export default function AppLayout({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';
  const isProjectWorkspace =
    pathname.startsWith('/app/projects/') &&
    !pathname.startsWith('/app/projects/new');

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

  /* =========================================================================
     1. WORKSPACE MODE (Left 56px Icon Rail, No Separate Top Header Bar)
     ========================================================================= */
  if (isProjectWorkspace) {
    return (
      <div className="flex h-screen w-screen overflow-hidden bg-background">
        {/* Mobile/Tablet Drawer Backdrop for Rail when opened on <1280px */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm xl:hidden"
            onClick={toggleSidebar}
            aria-hidden="true"
          />
        )}

        {/* 56px Left Icon Rail (replaces 255px sidebar) */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex flex-col items-center justify-between border-r border-border bg-card py-3.5 px-2 w-[56px] min-w-[56px] max-w-[56px] shrink-0 transition-transform duration-200 xl:static xl:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
          aria-label="Workspace navigation rail"
        >
          {/* Top: Logo, Projects, Settings */}
          <div className="flex flex-col items-center gap-3.5 w-full">
            <Tooltip text="DeviceStack">
              <Link
                href="/app/projects"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm hover:opacity-90 transition-opacity"
                aria-label="DeviceStack home"
              >
                <Cpu className="h-5 w-5" />
              </Link>
            </Tooltip>

            <nav className="flex flex-col items-center gap-2 w-full pt-1" aria-label="Main navigation">
              <Tooltip text="Projects">
                <Link
                  href="/app/projects"
                  aria-label="Projects list"
                  className={`flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
                    pathname === '/app/projects'
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  <FolderGit2 className="h-4 w-4" />
                </Link>
              </Tooltip>

              <Tooltip text="Settings">
                <Link
                  href="/app/settings"
                  aria-label="Settings"
                  className={`flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
                    pathname.startsWith('/app/settings')
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  <Settings className="h-4 w-4" />
                </Link>
              </Tooltip>
            </nav>
          </div>

          {/* Bottom: Board connection icon with live dot, theme toggle, avatar */}
          <div className="flex flex-col items-center gap-3 w-full">
            <Tooltip text="Board Connection (ESP32 Live)">
              <div
                className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                aria-label="Board connection status: ESP32 Live"
              >
                <Usb className="h-4 w-4" />
                <span
                  className="absolute top-1 right-1 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-card"
                  aria-label="Board connected"
                />
              </div>
            </Tooltip>

            <Tooltip text="Toggle theme">
              <div className="flex items-center justify-center" aria-label="Theme toggle">
                <ThemeToggle />
              </div>
            </Tooltip>

            <Tooltip text="Sarah Chen (Hardware Engineer)">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary select-none"
                aria-label="User avatar: Sarah Chen"
              >
                SC
              </div>
            </Tooltip>
          </div>
        </aside>

        {/* Main Workspace Canvas (Occupies full viewport width minus 56px rail) */}
        <div className="flex flex-1 flex-col overflow-hidden min-w-0">
          {children}
        </div>
      </div>
    );
  }

  /* =========================================================================
     2. STANDARD MODE (Projects List, New Wizard, Settings)
     ========================================================================= */
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

      {/* Adjustable Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-all duration-300 ease-in-out md:static ${
          sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0'
        } ${sidebarOpen ? 'md:w-64' : 'md:w-16'}`}
      >
        {/* Sidebar Header */}
        <div
          className={`flex h-16 items-center border-b border-border px-3 ${
            sidebarOpen ? 'justify-between' : 'justify-center'
          }`}
        >
          {sidebarOpen ? (
            <Link
              href="/app/projects"
              className="flex items-center gap-2.5 font-bold tracking-tight overflow-hidden"
              title="DeviceStack"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow">
                <Cpu className="h-5 w-5" />
              </div>
              <span className="text-base text-foreground truncate whitespace-nowrap transition-opacity duration-200">
                DeviceStack
              </span>
            </Link>
          ) : (
            <Tooltip text="DeviceStack">
              <Link
                href="/app/projects"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow hover:opacity-90 transition-opacity"
                aria-label="DeviceStack"
              >
                <Cpu className="h-5 w-5" />
              </Link>
            </Tooltip>
          )}

          {sidebarOpen && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="shrink-0 h-8 w-8 text-muted-foreground hover:text-foreground"
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
            >
              <span className="md:hidden">
                <X className="h-4 w-4" />
              </span>
              <span className="hidden md:block">
                <ChevronLeft className="h-4 w-4" />
              </span>
            </Button>
          )}
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
