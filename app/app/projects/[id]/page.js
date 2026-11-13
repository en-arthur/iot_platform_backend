'use client';

import React, { useState, useEffect, useRef, use } from 'react';
import Link from 'next/link';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { useUIStore } from '@/lib/store/useUIStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { AIChatPanel } from '@/components/spec/AIChatPanel';
import { ValidationPanel } from '@/components/spec/ValidationPanel';
import { DependenciesPanel } from '@/components/spec/DependenciesPanel';
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Lock,
  Unlock,
  Check,
  X,
  SlidersHorizontal,
  ChevronRight,
  ChevronDown,
  PanelRightClose,
  PanelRightOpen,
  Loader2,
} from 'lucide-react';

const SECTION_CONFIG = [
  { key: 'metadata', num: 1, shortName: 'Metadata', fullName: 'Project Metadata' },
  { key: 'hardware', num: 2, shortName: 'Hardware', fullName: 'Hardware Platform & Power' },
  { key: 'peripherals', num: 3, shortName: 'Peripherals', fullName: 'Peripherals & Pin Multiplexing' },
  { key: 'behavior', num: 4, shortName: 'Behavior', fullName: 'Runtime Behavior & State Machine' },
  { key: 'data_model', num: 5, shortName: 'Data Model', fullName: 'Telemetry & Data Model' },
  { key: 'connectivity', num: 6, shortName: 'Connectivity', fullName: 'Connectivity & Protocols' },
  { key: 'cloud_backend', num: 7, shortName: 'Cloud Backend', fullName: 'Cloud Backend & Ingestion' },
  { key: 'interface', num: 8, shortName: 'Interface', fullName: 'Web/App Interface' },
  { key: 'security', num: 9, shortName: 'Security', fullName: 'Device Security & Identity' },
  { key: 'updates', num: 10, shortName: 'Updates', fullName: 'Updates & Lifecycle (OTA)' },
  { key: 'verification', num: 11, shortName: 'Verification', fullName: 'Verification Contracts' },
  { key: 'provenance', num: 12, shortName: 'Provenance', fullName: 'Audit Provenance & Export Gate' },
];

/**
 * Compact Inline Field Row
 * - Monospace label column (~170px)
 * - Flexible value column with real <label for> and inline <input>/<textarea>
 * - No badge on confirmed fields
 * - State tags under label: Required (alert icon), Default (muted text), AI proposed (sparkle icon + inline Accept/Dismiss), From library (lock icon)
 */
function CompactFieldRow({
  projectId,
  sectionKey,
  fieldKey,
  fieldData,
  issue,
  isFocused,
  onUpdateField,
}) {
  const [val, setVal] = useState(
    fieldData.value === null || fieldData.value === undefined
      ? ''
      : typeof fieldData.value === 'object'
      ? JSON.stringify(fieldData.value)
      : String(fieldData.value)
  );
  const [isOverriding, setIsOverriding] = useState(false);
  const [overrideReasonInput, setOverrideReasonInput] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    setVal(
      fieldData.value === null || fieldData.value === undefined
        ? ''
        : typeof fieldData.value === 'object'
        ? JSON.stringify(fieldData.value)
        : String(fieldData.value)
    );
  }, [fieldData.value]);

  useEffect(() => {
    if (isFocused && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isFocused]);

  const fieldId = `${sectionKey}.${fieldKey}`;
  const isRequired = fieldData.state === 'open';
  const isAiProposed = fieldData.state === 'inferred' || fieldData.source === 'ai';
  const isDefault = fieldData.state === 'defaulted';
  const isFromLibrary =
    (fieldData.source === 'from_library' || fieldData.source === 'library') &&
    !fieldData.override_reason;
  const isOverridden = Boolean(fieldData.override_reason);
  const isConfirmed = fieldData.state === 'confirmed' && !isFromLibrary;

  const handleBlurOrCommit = () => {
    if (isFromLibrary) return;
    let parsedVal = val;
    if (typeof fieldData.value === 'number') {
      const num = Number(val);
      if (!isNaN(num)) parsedVal = num;
    } else if (typeof fieldData.value === 'boolean') {
      parsedVal = val === 'true';
    }
    if (parsedVal !== fieldData.value) {
      onUpdateField(projectId, sectionKey, fieldKey, parsedVal, fieldData.override_reason);
    }
  };

  const handleAcceptAi = () => {
    onUpdateField(projectId, sectionKey, fieldKey, fieldData.value, fieldData.override_reason);
  };

  const handleDismissAi = () => {
    onUpdateField(projectId, sectionKey, fieldKey, null, 'Dismissed AI proposal');
  };

  const handleCommitOverride = () => {
    if (!overrideReasonInput.trim()) return;
    onUpdateField(projectId, sectionKey, fieldKey, fieldData.value, overrideReasonInput);
    setIsOverriding(false);
  };

  // Determine row container styling according to requirements
  let containerStyle = 'border-b border-border/70 hover:bg-muted/15';
  if (isRequired) {
    // Tinted container with full border (no left-border accent)
    containerStyle = 'border border-amber-500/40 bg-amber-500/5 rounded-md my-1.5';
  } else if (isAiProposed) {
    // Dashed-border container
    containerStyle = 'border border-dashed border-primary/60 bg-primary/5 rounded-md my-1.5';
  } else if (issue && issue.severity === 'error') {
    containerStyle = 'border border-destructive/50 bg-destructive/5 rounded-md my-1.5';
  }

  return (
    <div
      className={`px-3.5 py-2.5 transition-all text-xs ${containerStyle} ${
        isFocused ? 'ring-2 ring-primary ring-offset-1 rounded-md' : ''
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
        {/* Label Column (~170px) */}
        <div className="w-full sm:w-[170px] sm:min-w-[170px] sm:max-w-[170px] shrink-0 flex flex-col justify-center">
          <label
            htmlFor={fieldId}
            className="font-mono text-xs font-semibold text-foreground truncate cursor-pointer hover:underline select-none"
            title={fieldKey}
          >
            {fieldKey}
          </label>

          {/* State tag under label (ONLY for non-confirmed fields: icon + text, never color alone) */}
          {isRequired && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-600 dark:text-amber-400 mt-0.5">
              <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span>Required</span>
            </span>
          )}

          {isAiProposed && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-primary mt-0.5">
              <Sparkles className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span>AI proposed</span>
            </span>
          )}

          {isDefault && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground mt-0.5">
              <SlidersHorizontal className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span>Default</span>
            </span>
          )}

          {isFromLibrary && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground mt-0.5">
              <Lock className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span>From library</span>
            </span>
          )}

          {isOverridden && !isRequired && !isAiProposed && (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-muted-foreground mt-0.5 italic truncate" title={`Override: ${fieldData.override_reason}`}>
              <Unlock className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span>Overridden</span>
            </span>
          )}
        </div>

        {/* Value Column (Flexible) */}
        <div className="flex-1 min-w-0 flex items-center gap-2">
          {typeof fieldData.value === 'boolean' ? (
            <div className="flex items-center gap-2">
              <button
                id={fieldId}
                type="button"
                disabled={isFromLibrary}
                onClick={() =>
                  onUpdateField(projectId, sectionKey, fieldKey, !fieldData.value, fieldData.override_reason)
                }
                className={`h-7 px-3 rounded text-xs font-mono font-medium border transition-colors ${
                  fieldData.value
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-muted text-muted-foreground border-border'
                } ${isFromLibrary ? 'cursor-not-allowed opacity-75' : ''}`}
              >
                {fieldData.value ? 'true' : 'false'}
              </button>
            </div>
          ) : (
            <input
              id={fieldId}
              ref={inputRef}
              type="text"
              readOnly={isFromLibrary}
              value={val}
              onChange={(e) => setVal(e.target.value)}
              onBlur={handleBlurOrCommit}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.currentTarget.blur();
                }
              }}
              placeholder={isRequired ? 'Enter required parameter...' : 'null'}
              className={`h-8 w-full rounded-md border border-input bg-background/90 px-2.5 py-1 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-all ${
                isFromLibrary ? 'bg-muted/40 cursor-not-allowed text-muted-foreground' : ''
              } ${isRequired && !val ? 'placeholder:text-amber-500/70 italic' : ''}`}
            />
          )}

          {/* AI proposed inline Accept / Dismiss buttons */}
          {isAiProposed && (
            <div className="flex items-center gap-1 shrink-0">
              <Button
                type="button"
                size="sm"
                variant="default"
                onClick={handleAcceptAi}
                className="h-7 px-2.5 text-xs gap-1 bg-primary text-primary-foreground shadow-xs"
                title="Accept AI proposal"
              >
                <Check className="h-3.5 w-3.5" />
                <span>Accept</span>
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={handleDismissAi}
                className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                title="Dismiss AI proposal"
              >
                <X className="h-3.5 w-3.5" />
                <span>Dismiss</span>
              </Button>
            </div>
          )}

          {/* From library Override button */}
          {isFromLibrary && (
            <div className="shrink-0">
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => setIsOverriding(!isOverriding)}
                className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground border-border"
                title="Override library default"
              >
                <Unlock className="h-3 w-3" />
                <span>Override</span>
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Override Reason Prompt if overriding */}
      {isOverriding && (
        <div className="mt-2.5 pt-2 border-t border-border flex items-center gap-2 animate-in fade-in">
          <input
            type="text"
            value={overrideReasonInput}
            onChange={(e) => setOverrideReasonInput(e.target.value)}
            placeholder="Record engineering reason for override..."
            className="h-7 flex-1 rounded border border-input bg-background px-2 text-xs font-sans text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Button
            size="sm"
            onClick={handleCommitOverride}
            disabled={!overrideReasonInput.trim()}
            className="h-7 text-xs px-2.5 bg-primary text-primary-foreground"
          >
            Confirm Override
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsOverriding(false)}
            className="h-7 text-xs px-2 text-muted-foreground"
          >
            Cancel
          </Button>
        </div>
      )}

      {/* Inline Validation Issue Alert */}
      {issue && (
        <div
          className={`mt-2 flex items-start gap-1.5 text-xs p-1.5 rounded ${
            issue.severity === 'error'
              ? 'bg-destructive/10 text-destructive'
              : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
          }`}
        >
          {issue.severity === 'error' ? (
            <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          )}
          <span className="font-medium">{issue.message}</span>
        </div>
      )}
    </div>
  );
}

export default function SpecWorkspacePage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const {
    spec,
    issues,
    error,
    isLoading,
    updateFieldOptimistic,
    fieldFilter,
    setFieldFilter,
    focusedFieldPath,
    rightPanelCollapsed,
    setRightPanelCollapsed,
    mobileDrawerOpen,
    setMobileDrawerOpen,
  } = useSpecStore();

  const {
    activeSpecSection,
    setActiveSpecSection,
    activeRightTab,
    setActiveRightTab,
  } = useUIStore();

  // Close mobile drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setMobileDrawerOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setMobileDrawerOpen]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 text-sm text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mr-2 text-primary" />
        <span>Loading 12-Section Spec Model...</span>
      </div>
    );
  }

  if (!spec) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 p-12 text-sm text-muted-foreground">
        <AlertCircle className="h-6 w-6 text-destructive" />
        <p className="font-medium text-foreground">This project could not be loaded.</p>
        <p className="max-w-md text-center">
          {error || 'The project may have been removed, or the backend restarted and cleared its in-memory data.'}
        </p>
        <Link href="/app/projects">
          <Button variant="outline" size="sm" className="mt-2">
            Back to projects
          </Button>
        </Link>
      </div>
    );
  }

  const activeSectionData = spec[activeSpecSection] || spec.metadata || {};
  const activeSectionFields = activeSectionData.fields || {};
  const activeSectionConfig =
    SECTION_CONFIG.find((s) => s.key === activeSpecSection) || SECTION_CONFIG[0];

  // Needs attention count for active section
  const sectionFieldEntries = Object.entries(activeSectionFields);
  const attentionEntries = sectionFieldEntries.filter(([fKey, fData]) => {
    const fieldPath = `${activeSpecSection}.${fKey}`;
    const hasIssue = issues.some((i) => i.field_path === fieldPath);
    const isOpen = fData.state === 'open';
    const isAi = fData.state === 'inferred' || fData.source === 'ai';
    return isOpen || isAi || hasIssue;
  });

  const displayedFieldEntries =
    fieldFilter === 'needs_attention' ? attentionEntries : sectionFieldEntries;

  return (
    <div className="flex-1 flex overflow-hidden min-h-0 w-full relative">
      {/* =====================================================================
          PANE 1: SECTIONS LIST (Desktop: 216px wide, fits 12 rows without scroll)
          ===================================================================== */}
      <nav
        role="tablist"
        aria-label="Spec Sections"
        className="hidden lg:flex w-[216px] min-w-[216px] max-w-[216px] border-r border-border bg-card/40 flex-col shrink-0 select-none overflow-hidden"
      >
        <div className="h-[36px] min-h-[36px] px-3 border-b border-border/80 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-muted-foreground shrink-0">
          <span>Sections</span>
          <span className="font-mono text-[10px]">12/12</span>
        </div>

        <div className="p-1 space-y-0.5 flex-1 flex flex-col justify-start">
          {SECTION_CONFIG.map((sec) => {
            const secData = spec[sec.key];
            const fields = Object.values(secData?.fields || {});
            const openCount = fields.filter((f) => f.state === 'open').length;
            const hasError = issues.some(
              (i) => i.field_path.startsWith(sec.key) && i.severity === 'error'
            );
            const isActive = activeSpecSection === sec.key;

            return (
              <button
                key={sec.key}
                role="tab"
                type="button"
                aria-selected={isActive}
                aria-current={isActive ? 'true' : undefined}
                onClick={() => setActiveSpecSection(sec.key)}
                className={`h-[32px] min-h-[32px] max-h-[32px] w-full px-2.5 rounded-md text-xs font-medium transition-colors flex items-center justify-between text-left ${
                  isActive
                    ? 'bg-accent text-accent-foreground font-semibold shadow-xs'
                    : 'text-foreground/80 hover:bg-muted/60 hover:text-foreground'
                }`}
              >
                <div className="flex items-center gap-1.5 truncate min-w-0 pr-1">
                  <span className="font-mono text-[10px] text-muted-foreground w-3.5 shrink-0 text-right">
                    {sec.num}
                  </span>
                  <span className="truncate">{sec.shortName}</span>
                </div>

                <div className="flex items-center gap-1 shrink-0 ml-1">
                  {hasError ? (
                    <AlertTriangle
                      className="h-3.5 w-3.5 text-destructive"
                      aria-label="Has errors"
                    />
                  ) : openCount > 0 ? (
                    <span
                      className="text-[10px] font-mono px-1.5 py-0 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 font-semibold"
                      title={`${openCount} open field(s)`}
                    >
                      {openCount}
                    </span>
                  ) : (
                    <CheckCircle2
                      className={`h-3.5 w-3.5 ${
                        isActive ? 'text-primary' : 'text-emerald-500'
                      }`}
                      aria-label="Section complete"
                    />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </nav>

      {/* =====================================================================
          PANE 2: FIELDS PANE (Flexible width, ~750px at 1366px wide)
          ===================================================================== */}
      <section
        aria-label="Spec Fields"
        className="flex-1 min-w-0 flex flex-col bg-background border-r border-border overflow-hidden"
      >
        {/* Tablet Dropdown Selector for Sections (< 1024px) */}
        <div className="lg:hidden border-b border-border p-2 bg-card/60 shrink-0">
          <label htmlFor="tablet-section-select" className="sr-only">
            Select Spec Section
          </label>
          <div className="relative">
            <select
              id="tablet-section-select"
              value={activeSpecSection}
              onChange={(e) => setActiveSpecSection(e.target.value)}
              className="w-full text-xs font-semibold bg-background border border-border rounded-md px-3 py-1.5 pr-8 text-foreground appearance-none focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
            >
              {SECTION_CONFIG.map((sec) => {
                const secData = spec[sec.key];
                const openCount = secData
                  ? Object.values(secData.fields || {}).filter((f) => f.state === 'open').length
                  : 0;
                return (
                  <option key={sec.key} value={sec.key}>
                    {sec.num} {sec.fullName} {openCount > 0 ? `(${openCount} open)` : ''}
                  </option>
                );
              })}
            </select>
            <ChevronDown className="h-4 w-4 text-muted-foreground absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Section Header (~60px) with segmented filter */}
        <div className="h-[60px] min-h-[60px] max-h-[60px] px-4 border-b border-border flex items-center justify-between gap-4 bg-background/95 shrink-0 select-none">
          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-bold text-foreground truncate">
              {activeSectionConfig.num}. {activeSectionConfig.fullName}
            </h2>
            <p className="text-[11px] text-muted-foreground truncate">
              Inspect attributes, configure parameter overrides, and review hardware constraints.
            </p>
          </div>

          {/* Segmented Filter: All fields | Needs attention (n) */}
          <div className="inline-flex items-center rounded-lg bg-muted p-0.5 text-xs font-medium shrink-0">
            <button
              type="button"
              onClick={() => setFieldFilter('all')}
              className={`rounded-md px-2.5 py-1 text-xs transition-all ${
                fieldFilter === 'all'
                  ? 'bg-background text-foreground shadow-xs font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All fields ({sectionFieldEntries.length})
            </button>
            <button
              type="button"
              onClick={() => setFieldFilter('needs_attention')}
              className={`rounded-md px-2.5 py-1 text-xs transition-all flex items-center gap-1.5 ${
                fieldFilter === 'needs_attention'
                  ? 'bg-background text-foreground shadow-xs font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <span>Needs attention</span>
              {attentionEntries.length > 0 && (
                <span
                  className={`rounded-full px-1.5 py-0 text-[10px] font-mono ${
                    fieldFilter === 'needs_attention'
                      ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold'
                      : 'bg-muted-foreground/20 text-muted-foreground'
                  }`}
                >
                  {attentionEntries.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Compact Field Rows List (Internally scrollable) */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {displayedFieldEntries.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              {fieldFilter === 'needs_attention'
                ? 'No fields in this section require attention. All parameters are confirmed.'
                : 'No fields configured for this section.'}
            </div>
          ) : (
            displayedFieldEntries.map(([fKey, fData]) => {
              const fieldPath = `${activeSpecSection}.${fKey}`;
              const fieldIssue = issues.find((i) => i.field_path === fieldPath);
              const isFocused = focusedFieldPath === fieldPath;

              return (
                <CompactFieldRow
                  key={fKey}
                  projectId={projectId}
                  sectionKey={activeSpecSection}
                  fieldKey={fKey}
                  fieldData={fData}
                  issue={fieldIssue}
                  isFocused={isFocused}
                  onUpdateField={updateFieldOptimistic}
                />
              );
            })
          )}
        </div>
      </section>

      {/* =====================================================================
          PANE 3: RIGHT PANEL (Desktop: ~340px wide, collapsable)
          Tabs: Validation (count) [DEFAULT], AI chat, Impact
          ===================================================================== */}
      {!rightPanelCollapsed ? (
        <aside
          aria-label="Checks and AI Assistant"
          className="hidden xl:flex w-[340px] min-w-[340px] max-w-[340px] flex-col border-l border-border bg-card/30 shrink-0 overflow-hidden"
        >
          <Tabs
            value={activeRightTab}
            onValueChange={setActiveRightTab}
            className="flex-1 flex flex-col overflow-hidden"
          >
            {/* Right Panel Header with Tabs and Collapse button */}
            <div className="h-[44px] min-h-[44px] px-2 border-b border-border bg-card flex items-center justify-between gap-1 shrink-0 select-none">
              <TabsList className="grid grid-cols-3 h-8 flex-1 p-0.5">
                <TabsTrigger value="validation" className="text-xs px-1 gap-1">
                  <span>Validation</span>
                  {issues.length > 0 && (
                    <span className="rounded-full bg-destructive/15 text-destructive font-mono text-[10px] px-1 py-0">
                      {issues.length}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="chat" className="text-xs px-1">
                  AI chat
                </TabsTrigger>
                <TabsTrigger value="impact" className="text-xs px-1">
                  Impact
                </TabsTrigger>
              </TabsList>

              {/* Collapse button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setRightPanelCollapsed(true)}
                className="h-7 w-7 text-muted-foreground hover:text-foreground shrink-0 ml-1"
                aria-label="Collapse side panel"
                title="Collapse side panel"
              >
                <PanelRightClose className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex-1 overflow-hidden">
              <TabsContent value="validation" className="h-full mt-0">
                <ValidationPanel issues={issues} />
              </TabsContent>
              <TabsContent value="chat" className="h-full mt-0">
                <AIChatPanel projectId={projectId} />
              </TabsContent>
              <TabsContent value="impact" className="h-full mt-0">
                <DependenciesPanel spec={spec} />
              </TabsContent>
            </div>
          </Tabs>
        </aside>
      ) : (
        /* Collapsed Panel Restore Strip (Desktop) */
        <div className="hidden xl:flex w-8 border-l border-border bg-card/40 flex-col items-center py-2 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setRightPanelCollapsed(false)}
            className="h-7 w-7 text-muted-foreground hover:text-foreground"
            aria-label="Expand Checks and AI panel"
            title="Expand Checks and AI panel"
          >
            <PanelRightOpen className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* =====================================================================
          RESPONSIVE SLIDE-OVER DRAWER (Tablet/Mobile: < 1280px)
          Opened from "Checks and AI (count)" button in header
          Scrim behind it, closes on Escape or backdrop click
          ===================================================================== */}
      {mobileDrawerOpen && (
        <div className="xl:hidden fixed inset-0 z-50 flex justify-end">
          {/* Backdrop Scrim */}
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileDrawerOpen(false)}
            aria-hidden="true"
          />

          {/* Slide-over Drawer Panel (~380px) */}
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Checks and AI drawer"
            className="relative w-[380px] max-w-[90vw] h-full bg-card border-l border-border shadow-2xl flex flex-col z-50 animate-in slide-in-from-right duration-200"
          >
            <Tabs
              value={activeRightTab}
              onValueChange={setActiveRightTab}
              className="flex-1 flex flex-col overflow-hidden"
            >
              <div className="h-[48px] px-3 border-b border-border bg-card flex items-center justify-between gap-2 shrink-0">
                <TabsList className="grid grid-cols-3 h-8 flex-1 p-0.5">
                  <TabsTrigger value="validation" className="text-xs px-1 gap-1">
                    <span>Validation</span>
                    {issues.length > 0 && (
                      <span className="rounded-full bg-destructive/15 text-destructive font-mono text-[10px] px-1 py-0">
                        {issues.length}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="chat" className="text-xs px-1">
                    AI chat
                  </TabsTrigger>
                  <TabsTrigger value="impact" className="text-xs px-1">
                    Impact
                  </TabsTrigger>
                </TabsList>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setMobileDrawerOpen(false)}
                  className="h-8 w-8 text-muted-foreground hover:text-foreground shrink-0"
                  aria-label="Close drawer"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex-1 overflow-hidden">
                <TabsContent value="validation" className="h-full mt-0">
                  <ValidationPanel issues={issues} />
                </TabsContent>
                <TabsContent value="chat" className="h-full mt-0">
                  <AIChatPanel projectId={projectId} />
                </TabsContent>
                <TabsContent value="impact" className="h-full mt-0">
                  <DependenciesPanel spec={spec} />
                </TabsContent>
              </div>
            </Tabs>
          </div>
        </div>
      )}
    </div>
  );
}
