'use client';

import React, { useEffect, use } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  History,
  Code2,
  CheckCircle,
  Zap,
  Radio,
  Cpu,
  Layers,
  ChevronRight,
} from 'lucide-react';

const LIFECYCLE_STEPS = [
  { id: 'draft', label: 'Draft' },
  { id: 'validated', label: 'Validated' },
  { id: 'confirmed', label: 'Confirmed' },
  { id: 'generated', label: 'Generated' },
  { id: 'verified', label: 'Verified' },
  { id: 'deployed', label: 'Deployed' },
];

export default function ProjectWorkspaceLayout({ children, params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;
  const pathname = usePathname();

  const { project, loadProjectAndSpec, isLoading } = useSpecStore();

  useEffect(() => {
    if (projectId) {
      loadProjectAndSpec(projectId);
    }
  }, [projectId, loadProjectAndSpec]);

  const currentLifecycle = project?.lifecycle || 'draft';
  const currentStepIndex = LIFECYCLE_STEPS.findIndex((s) => s.id === currentLifecycle);

  const tabs = [
    { label: 'Spec Model', href: `/app/projects/${projectId}`, exact: true, icon: FileText },
    { label: 'Versions & Diff', href: `/app/projects/${projectId}/versions`, icon: History },
    { label: 'Code Viewer', href: `/app/projects/${projectId}/code`, icon: Code2 },
    { label: 'Verification', href: `/app/projects/${projectId}/verify`, icon: CheckCircle },
    { label: 'Web Flash', href: `/app/projects/${projectId}/flash`, icon: Zap },
    { label: 'Live Interface', href: `/app/projects/${projectId}/live`, icon: Radio },
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      {/* Project Workspace Header */}
      <div className="border-b border-border bg-card/60 backdrop-blur px-6 py-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Link href="/app/projects" className="hover:text-foreground">Projects</Link>
              <ChevronRight className="h-3 w-3" />
              <span className="font-mono text-foreground">{projectId}</span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold tracking-tight text-foreground">
                {project?.name || 'Loading Project...'}
              </h1>
              <Badge variant="default" className="text-xs">
                v{project?.version || 1}.0
              </Badge>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Cpu className="h-3 w-3 text-primary" />
                <span>{project?.board_id || 'ESP32-S3'}</span>
              </span>
            </div>
          </div>

          {/* Lifecycle Stepper */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {LIFECYCLE_STEPS.map((step, idx) => {
              const isPast = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;
              return (
                <div key={step.id} className="flex items-center gap-1.5">
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                      isCurrent
                        ? 'bg-primary text-primary-foreground shadow-sm ring-2 ring-primary/20'
                        : isPast
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                        : 'bg-muted text-muted-foreground border border-border'
                    }`}
                  >
                    <span className="text-[10px] font-mono">{idx + 1}.</span>
                    <span>{step.label}</span>
                  </div>
                  {idx < LIFECYCLE_STEPS.length - 1 && (
                    <span className="text-muted-foreground text-xs font-mono">›</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 mt-4 border-t border-border/40 pt-3 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = tab.exact
              ? pathname === tab.href
              : pathname.startsWith(tab.href);
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tab.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Main Workspace View */}
      <div className="flex-1 flex flex-col">
        {children}
      </div>
    </div>
  );
}
