'use client';

import React, { useState, use } from 'react';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { useUIStore } from '@/lib/store/useUIStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { FieldBadge } from '@/components/spec/FieldBadge';
import { AIChatPanel } from '@/components/spec/AIChatPanel';
import { ValidationPanel } from '@/components/spec/ValidationPanel';
import { DependenciesPanel } from '@/components/spec/DependenciesPanel';
import { FieldEditorModal } from '@/components/spec/FieldEditorModal';
import {
  CheckCircle2,
  AlertCircle,
  Edit2,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldAlert,
  Loader2,
  HardDrive,
} from 'lucide-react';

const SECTIONS_ORDER = [
  'metadata',
  'hardware',
  'peripherals',
  'behavior',
  'data_model',
  'connectivity',
  'cloud_backend',
  'interface',
  'security',
  'updates',
  'verification',
  'provenance',
];

export default function SpecWorkspacePage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const {
    spec,
    project,
    issues,
    isLoading,
    isSaving,
    updateFieldOptimistic,
    confirmCurrentSpec,
  } = useSpecStore();

  const {
    activeSpecSection,
    setActiveSpecSection,
    activeRightTab,
    setActiveRightTab,
  } = useUIStore();

  // Field editor state
  const [editingField, setEditingField] = useState(null); // { sectionKey, fieldKey, fieldData }
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState('');

  if (isLoading || !spec) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 text-sm text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mr-2 text-primary" />
        <span>Loading 12-Section Spec Model...</span>
      </div>
    );
  }

  // Count blocking issues and open fields
  const blockingIssues = issues.filter((i) => i.severity === 'error');
  const openFieldsCount = Object.values(spec).reduce((total, sec) => {
    return total + Object.values(sec.fields || {}).filter((f) => f.state === 'open').length;
  }, 0);

  const isConfirmDisabled = blockingIssues.length > 0 || openFieldsCount > 0;
  const isAlreadyConfirmed = project?.lifecycle === 'confirmed';

  const handleConfirm = async () => {
    if (isConfirmDisabled) return;
    setConfirming(true);
    setConfirmError('');
    try {
      await confirmCurrentSpec(projectId);
    } catch (err) {
      setConfirmError(err.message);
    } finally {
      setConfirming(false);
    }
  };

  const handleFieldSave = (secKey, fldKey, newVal, overrideReason) => {
    updateFieldOptimistic(projectId, secKey, fldKey, newVal, overrideReason);
  };

  const activeSectionData = spec[activeSpecSection] || spec.metadata;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* 3-Column Workspace Grid */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* Left Column: 12-Section Navigation (Col 1-3) */}
        <div className="col-span-12 md:col-span-3 border-r border-border bg-card/40 flex flex-col overflow-y-auto">
          <div className="p-3 border-b border-border/80 text-xs font-semibold uppercase tracking-wider text-muted-foreground flex justify-between items-center">
            <span>Spec Sections (12)</span>
            {openFieldsCount > 0 && (
              <span className="text-[11px] font-mono text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded">
                {openFieldsCount} open
              </span>
            )}
          </div>

          <div className="p-2 space-y-1">
            {SECTIONS_ORDER.map((secKey) => {
              const sec = spec[secKey];
              if (!sec) return null;

              const fields = Object.values(sec.fields || {});
              const openCount = fields.filter((f) => f.state === 'open').length;
              const hasErrors = issues.some(
                (i) => i.field_path.startsWith(secKey) && i.severity === 'error'
              );
              const isActive = activeSpecSection === secKey;

              return (
                <button
                  key={secKey}
                  type="button"
                  onClick={() => setActiveSpecSection(secKey)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs font-medium transition-all flex items-center justify-between ${
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm font-semibold'
                      : 'hover:bg-muted text-foreground'
                  }`}
                >
                  <span className="truncate">{sec.title}</span>
                  <div className="flex items-center gap-1.5 shrink-0 ml-2">
                    {hasErrors && (
                      <span className="h-2 w-2 rounded-full bg-destructive" title="Errors present" />
                    )}
                    {openCount > 0 ? (
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                          isActive
                            ? 'bg-primary-foreground/20 text-primary-foreground'
                            : 'bg-amber-500/15 text-amber-600'
                        }`}
                      >
                        {openCount} open
                      </span>
                    ) : (
                      <CheckCircle2
                        className={`h-3.5 w-3.5 ${
                          isActive ? 'text-primary-foreground' : 'text-emerald-500'
                        }`}
                      />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Center Column: Schema-Driven Form (Col 4-8) */}
        <div className="col-span-12 md:col-span-5 border-r border-border flex flex-col overflow-y-auto bg-background">
          <div className="p-4 border-b border-border flex items-center justify-between sticky top-0 bg-background/95 backdrop-blur z-10">
            <div>
              <h2 className="text-base font-bold text-foreground">
                {activeSectionData?.title}
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Inspect attributes, field states, and configure parameter overrides.
              </p>
            </div>
          </div>

          <div className="p-4 space-y-4">
            {Object.entries(activeSectionData?.fields || {}).map(([fKey, fData]) => {
              const fieldPath = `${activeSpecSection}.${fKey}`;
              const fieldIssue = issues.find((i) => i.field_path === fieldPath);

              return (
                <div
                  key={fKey}
                  className={`p-4 rounded-xl border transition-all ${
                    fieldIssue
                      ? fieldIssue.severity === 'error'
                        ? 'border-destructive/60 bg-destructive/5'
                        : 'border-amber-500/40 bg-amber-500/5'
                      : 'border-border bg-card'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-semibold text-foreground">
                      {fKey}
                    </span>
                    <FieldBadge
                      state={fData.state}
                      source={fData.source}
                      overrideReason={fData.override_reason}
                    />
                  </div>

                  {/* Value Display */}
                  <div className="mt-2 text-xs font-mono bg-muted/60 p-2.5 rounded-lg border border-border/60 break-all">
                    {fData.value === null ? (
                      <span className="text-amber-500 italic">null (Unfilled open field)</span>
                    ) : typeof fData.value === 'object' ? (
                      <pre className="text-[11px] whitespace-pre-wrap">
                        {JSON.stringify(fData.value, null, 2)}
                      </pre>
                    ) : typeof fData.value === 'boolean' ? (
                      fData.value ? 'true' : 'false'
                    ) : (
                      String(fData.value)
                    )}
                  </div>

                  {/* Override reason banner */}
                  {fData.override_reason && (
                    <div className="mt-2 text-[11px] text-muted-foreground flex items-center gap-1.5 italic">
                      <span>Reason: &quot;{fData.override_reason}&quot;</span>
                    </div>
                  )}

                  {/* Inline Issue Alert */}
                  {fieldIssue && (
                    <div
                      className={`mt-2.5 p-2 rounded text-xs flex items-start gap-2 ${
                        fieldIssue.severity === 'error'
                          ? 'bg-destructive/10 text-destructive'
                          : 'bg-amber-500/10 text-amber-500'
                      }`}
                    >
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span>{fieldIssue.message}</span>
                    </div>
                  )}

                  {/* Action */}
                  <div className="mt-3 flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setEditingField({
                          sectionKey: activeSpecSection,
                          fieldKey: fKey,
                          fieldData: fData,
                        })
                      }
                      className="h-7 text-xs gap-1.5 text-muted-foreground hover:text-foreground"
                    >
                      <Edit2 className="h-3 w-3" />
                      <span>Edit Field</span>
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: AI Chat, Validation & Dependencies Tabs (Col 9-12) */}
        <div className="col-span-12 md:col-span-4 flex flex-col overflow-hidden bg-card/20">
          <Tabs
            value={activeRightTab}
            onValueChange={setActiveRightTab}
            className="flex-1 flex flex-col overflow-hidden"
          >
            <div className="p-3 border-b border-border bg-card">
              <TabsList className="w-full grid grid-cols-3">
                <TabsTrigger value="chat" className="text-xs">
                  AI Chat
                </TabsTrigger>
                <TabsTrigger value="validation" className="text-xs relative">
                  <span>Validation</span>
                  {issues.length > 0 && (
                    <span
                      className={`ml-1.5 rounded-full px-1.5 py-0 text-[10px] font-mono ${
                        blockingIssues.length > 0
                          ? 'bg-destructive text-destructive-foreground'
                          : 'bg-muted-foreground text-card'
                      }`}
                    >
                      {issues.length}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="dependencies" className="text-xs">
                  Dependencies
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-hidden">
              <TabsContent value="chat" className="h-full mt-0">
                <AIChatPanel projectId={projectId} />
              </TabsContent>
              <TabsContent value="validation" className="h-full mt-0">
                <ValidationPanel issues={issues} />
              </TabsContent>
              <TabsContent value="dependencies" className="h-full mt-0">
                <DependenciesPanel spec={spec} />
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>

      {/* Spec Confirmation Footer Gate */}
      <footer className="border-t border-border bg-card p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {isAlreadyConfirmed ? (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-500">
              <CheckCircle2 className="h-4 w-4" />
              <span>Spec is confirmed. Ready to generate and verify firmware.</span>
            </div>
          ) : isConfirmDisabled ? (
            <div className="flex items-center gap-2 text-xs font-semibold text-destructive">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              <span>
                Confirmation Blocked: {blockingIssues.length} error(s) and {openFieldsCount} open field(s) require resolution.
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              <span>All validation rules passed. Spec is ready for engineering sign-off.</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {confirmError && (
            <span className="text-xs text-destructive">{confirmError}</span>
          )}
          <Button
            onClick={handleConfirm}
            disabled={isConfirmDisabled || confirming || isAlreadyConfirmed}
            className={`shadow-md px-6 ${
              isAlreadyConfirmed ? 'bg-emerald-600 hover:bg-emerald-600 text-white' : ''
            }`}
          >
            {confirming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : isAlreadyConfirmed ? (
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-white" />
                <span>Spec Confirmed</span>
              </span>
            ) : (
              'Confirm Spec (Sign-Off)'
            )}
          </Button>
        </div>
      </footer>

      {/* Field Editor Modal */}
      {editingField && (
        <FieldEditorModal
          open={Boolean(editingField)}
          onOpenChange={(open) => !open && setEditingField(null)}
          sectionKey={editingField.sectionKey}
          fieldKey={editingField.fieldKey}
          fieldData={editingField.fieldData}
          onSave={handleFieldSave}
        />
      )}
    </div>
  );
}
