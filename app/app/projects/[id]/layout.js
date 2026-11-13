'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { useUIStore } from '@/lib/store/useUIStore';
import { api } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  FileText,
  Code2,
  CheckCircle,
  Zap,
  Radio,
  Cpu,
  ChevronRight,
  Check,
  Lock,
  CheckCircle2,
  AlertTriangle,
  Menu,
  Sparkles,
  Loader2,
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

  const {
    project,
    spec,
    issues,
    loadProjectAndSpec,
    confirmCurrentSpec,
    isSaving,
    mobileDrawerOpen,
    setMobileDrawerOpen,
  } = useSpecStore();

  const { toggleSidebar } = useUIStore();
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateCode = async () => {
    if (isGenerating) return;
    setIsGenerating(true);
    try {
      await api.generateProjectCode(projectId);
      await loadProjectAndSpec(projectId);
      router.push(`/app/projects/${projectId}/code`);
    } catch (err) {
      alert(`Code generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      loadProjectAndSpec(projectId);
    }
  }, [projectId, loadProjectAndSpec]);

  // Count blocking issues and open fields
  const blockingIssues = issues.filter((i) => i.severity === 'error');
  const openFieldsCount = spec
    ? Object.values(spec).reduce((total, sec) => {
        return (
          total +
          Object.values(sec.fields || {}).filter((f) => f.state === 'open').length
        );
      }, 0)
    : 0;

  // RULE: Never show "Deployed" while there are open fields or errors.
  const hasBlockingErrorsOrOpenFields = blockingIssues.length > 0 || openFieldsCount > 0;
  const effectiveLifecycle = hasBlockingErrorsOrOpenFields
    ? 'draft'
    : project?.lifecycle || 'draft';

  const currentStepIndex = Math.max(
    0,
    LIFECYCLE_STEPS.findIndex((s) => s.id === effectiveLifecycle)
  );

  const isConfirmDisabled = hasBlockingErrorsOrOpenFields || isSaving;
  const isAlreadyConfirmed =
    !hasBlockingErrorsOrOpenFields &&
    ['confirmed', 'generated', 'verified', 'deployed'].includes(project?.lifecycle);
  const hasGeneratedCode = ['generated', 'verified', 'deployed'].includes(project?.lifecycle);

  // Version chip calculation
  const versionChipText = hasBlockingErrorsOrOpenFields
    ? `v${(project?.version || 3) + 0.1} draft`
    : project?.version_display || `v${project?.version || 3}.0`;

  // Status reason for footer
  let lockReason = '';
  if (blockingIssues.length > 0 && openFieldsCount > 0) {
    lockReason = `Confirm locked: ${blockingIssues.length} error(s) and ${openFieldsCount} open field(s) require review`;
  } else if (blockingIssues.length > 0) {
    lockReason = `Confirm locked: ${blockingIssues[0].message}`;
  } else if (openFieldsCount > 0) {
    lockReason = `Confirm locked: ${openFieldsCount} required field(s) are open`;
  } else if (isAlreadyConfirmed) {
    lockReason = 'Spec confirmed — ready for firmware synthesis & deployment';
  } else {
    lockReason = 'All validation rules passed — ready for engineering sign-off';
  }

  const deployedBaseline = project?.deployed_version || 'v3.0';

  const tabs = [
    { label: 'Spec model', href: `/app/projects/${projectId}`, exact: true, icon: FileText },
    { label: 'Code', href: `/app/projects/${projectId}/code`, icon: Code2 },
    { label: 'Verification', href: `/app/projects/${projectId}/verify`, icon: CheckCircle },
    { label: 'Flash', href: `/app/projects/${projectId}/flash`, icon: Zap },
    { label: 'Live', href: `/app/projects/${projectId}/live`, icon: Radio },
  ];

  const handleConfirm = async () => {
    if (isConfirmDisabled) return;
    try {
      await confirmCurrentSpec(projectId);
    } catch (err) {
      alert(`Confirm failed: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-background">
      {/* =====================================================================
          HEADER ROW 1 (about 52px height)
          Breadcrumb, Project Title (one-line truncated), Version Chip, Board Chip,
          Server online dot, and Confirm Spec Button.
          ===================================================================== */}
      <header className="h-[52px] min-h-[52px] max-h-[52px] border-b border-border bg-card px-3 sm:px-4 flex items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2 sm:gap-2.5 min-w-0 flex-1">
          {/* Hamburger on tablet/mobile to open 56px rail */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="xl:hidden h-8 w-8 text-muted-foreground shrink-0"
            aria-label="Toggle navigation menu"
          >
            <Menu className="h-4 w-4" />
          </Button>

          {/* Breadcrumb "Projects /" */}
          <Link
            href="/app/projects"
            className="text-xs font-medium text-muted-foreground hover:text-foreground shrink-0 transition-colors"
          >
            Projects
          </Link>
          <span className="text-muted-foreground/60 text-xs shrink-0 select-none">/</span>

          {/* Project Title on ONE line (truncate with ellipsis) */}
          <h1
            className="text-sm font-bold text-foreground truncate min-w-0"
            title={project?.name || ''}
          >
            {project?.name || ''}
          </h1>

          {/* Version Chip */}
          <Badge
            variant={hasBlockingErrorsOrOpenFields ? 'open' : 'confirmed'}
            className="text-[11px] font-mono px-2 py-0 shrink-0 font-medium whitespace-nowrap"
          >
            {versionChipText}
          </Badge>

          {/* Board Chip */}
          <span className="hidden sm:inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground shrink-0">
            <Cpu className="h-3 w-3 text-primary" />
            <span>{project?.board_id || 'ESP32-S3'}</span>
          </span>
        </div>

        {/* Right side: Code generation + Confirm Spec Button */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Generate firmware / cloud / interface code */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateCode}
            disabled={isGenerating}
            className="h-8 text-xs gap-1.5 border-border"
            title="Synthesize firmware, cloud backend and web interface code"
          >
            {isGenerating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Code2 className="h-3.5 w-3.5" />
            )}
            <span className="hidden sm:inline">
              {isGenerating ? 'Generating...' : hasGeneratedCode ? 'Regenerate code' : 'Generate code'}
            </span>
          </Button>

          {/* Tablet drawer toggle button for Checks and AI (<1280px) */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
            className="xl:hidden h-8 text-xs gap-1.5 border-border"
            aria-label={`Checks and AI (${issues.length})`}
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Checks and AI</span>
            {issues.length > 0 && (
              <span className="rounded-full bg-primary/20 text-primary text-[10px] px-1.5 py-0 font-mono">
                {issues.length}
              </span>
            )}
          </Button>

          {/* Confirm Spec Button */}
          <Button
            size="sm"
            onClick={handleConfirm}
            disabled={isConfirmDisabled}
            className={`h-8 px-3.5 text-xs font-semibold shadow-sm transition-all ${
              isAlreadyConfirmed
                ? 'bg-emerald-600 hover:bg-emerald-600 text-white cursor-default'
                : ''
            }`}
            title={isConfirmDisabled ? lockReason : 'Confirm Spec and Sign Off'}
          >
            {isSaving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : isAlreadyConfirmed ? (
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                <span>Confirmed</span>
              </span>
            ) : (
              'Confirm spec'
            )}
          </Button>
        </div>
      </header>

      {/* =====================================================================
          HEADER ROW 2 (about 40px height)
          Navigation Tabs on left; Compact Lifecycle Stepper on right.
          ===================================================================== */}
      <div className="h-[40px] min-h-[40px] max-h-[40px] border-b border-border bg-card/60 px-3 sm:px-4 flex items-center justify-between gap-4 shrink-0 overflow-hidden">
        {/* Tabs on Left */}
        <nav
          role="tablist"
          aria-label="Workspace views"
          className="flex items-center gap-1 overflow-x-auto no-scrollbar shrink-0 h-full"
        >
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = tab.exact
              ? pathname === tab.href
              : pathname.startsWith(tab.href);

            return (
              <Link
                key={tab.href}
                href={tab.href}
                role="tab"
                aria-selected={isActive}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span>{tab.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Compact Lifecycle Stepper on Right (never scrolls or clips) */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Desktop full stepper */}
          <ol
            aria-label="Lifecycle progress"
            className="hidden lg:flex items-center gap-1 list-none p-0 m-0"
          >
            {LIFECYCLE_STEPS.map((step, idx) => {
              const isPast = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;
              const isUpcoming = idx > currentStepIndex;

              return (
                <li
                  key={step.id}
                  aria-current={isCurrent ? 'step' : undefined}
                  className="flex items-center gap-1"
                >
                  <div
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold whitespace-nowrap transition-colors ${
                      isCurrent
                        ? 'bg-primary text-primary-foreground ring-2 ring-primary/40 shadow-xs'
                        : isPast
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                        : 'text-muted-foreground/50'
                    }`}
                  >
                    {isPast ? (
                      <Check className="h-3 w-3 stroke-[3]" aria-hidden="true" />
                    ) : (
                      <span className="text-[10px] font-mono">{idx + 1}</span>
                    )}
                    <span>{step.label}</span>
                  </div>

                  {idx < LIFECYCLE_STEPS.length - 1 && (
                    <span className="text-muted-foreground/40 text-[10px] select-none mx-0.5">
                      ›
                    </span>
                  )}
                </li>
              );
            })}
          </ol>

          {/* Tablet/Mobile Compact Stepper: "Draft - step 1 of 6" + 6 small bars */}
          <div className="flex lg:hidden items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="capitalize font-semibold text-foreground">
              {LIFECYCLE_STEPS[currentStepIndex]?.label} — step {currentStepIndex + 1} of 6
            </span>
            <div className="flex items-center gap-1" aria-hidden="true">
              {LIFECYCLE_STEPS.map((_, i) => (
                <span
                  key={i}
                  className={`h-1.5 w-2.5 rounded-full ${
                    i <= currentStepIndex ? 'bg-primary' : 'bg-muted-foreground/30'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* =====================================================================
          MAIN WORKSPACE CONTENT (3 Panes below header, fills exact remaining height)
          ===================================================================== */}
      <main className="flex-1 overflow-hidden flex flex-col min-h-0">
        {children}
      </main>

      {/* =====================================================================
          FOOTER STATUS BAR (about 32px height)
          Left: why Confirm is locked. Right: Autosave and deployed sync status.
          ===================================================================== */}
      <footer className="h-[32px] min-h-[32px] max-h-[32px] border-t border-border bg-card px-3 sm:px-4 flex items-center justify-between text-xs text-muted-foreground shrink-0 select-none">
        {/* Left: Lock icon + why Confirm is locked */}
        <div className="flex items-center gap-2 truncate pr-2">
          {hasBlockingErrorsOrOpenFields ? (
            <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-medium truncate">
              <Lock className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{lockReason}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium truncate">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{lockReason}</span>
            </div>
          )}
        </div>

        {/* Right: Autosaved & Deployed Version Sync */}
        <div className="flex items-center gap-2 shrink-0 font-mono text-[11px] text-muted-foreground">
          <span>Draft {versionChipText.split(' ')[0]} autosaved</span>
          <span>—</span>
          <span>{deployedBaseline} is deployed</span>
        </div>
      </footer>
    </div>
  );
}
