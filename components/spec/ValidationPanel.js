'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { useUIStore } from '@/lib/store/useUIStore';

const SEVERITY_CONFIG = {
  error: {
    icon: AlertCircle,
    label: 'Error',
    color: 'text-destructive',
    badge: 'destructive',
  },
  warning: {
    icon: AlertTriangle,
    label: 'Warning',
    color: 'text-amber-500',
    badge: 'open',
  },
  info: {
    icon: Info,
    label: 'Required',
    color: 'text-sky-500',
    badge: 'from_library',
  },
};

export function ValidationPanel({ issues }) {
  const { setActiveSpecSection, setActiveRightTab } = useUIStore();
  const { setFocusedFieldPath } = useSpecStore();

  const handleGoToField = (fieldPath) => {
    const [sectionKey] = fieldPath.split('.');
    if (sectionKey) {
      setActiveSpecSection(sectionKey);
      setFocusedFieldPath(fieldPath);
      // Automatically scroll to and focus the input element
      setTimeout(() => {
        const inputEl = document.getElementById(fieldPath);
        if (inputEl) {
          inputEl.focus();
          inputEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 50);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-card">
      {/* Issues List Column */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        <div className="flex items-center justify-between text-xs text-muted-foreground pb-1">
          <span className="font-semibold text-foreground uppercase tracking-wider text-[10px]">
            Validation Issues
          </span>
          <span className="font-mono text-[11px]">
            {issues.length} {issues.length === 1 ? 'item' : 'items'}
          </span>
        </div>

        {issues.length === 0 ? (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 text-center space-y-2 my-auto">
            <CheckCircle2 className="h-7 w-7 text-emerald-500 mx-auto" />
            <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              Zero Blocking Issues
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              All electrical, resource, and schema rules passed. Ready for engineering confirmation.
            </p>
          </div>
        ) : (
          issues.map((issue) => {
            const isRequired =
              issue.layer === 'completeness' || issue.id.includes('open');
            const cfg = isRequired
              ? {
                  icon: AlertCircle,
                  label: 'Required',
                  color: 'text-amber-500',
                  badge: 'open',
                }
              : SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.error;

            const Icon = cfg.icon;

            return (
              <div
                key={issue.id}
                className="rounded-lg border border-border bg-card p-3 space-y-2 hover:border-primary/40 transition-colors shadow-xs"
              >
                {/* Severity + Layer Label */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 font-bold text-xs">
                    <Icon className={`h-3.5 w-3.5 shrink-0 ${cfg.color}`} />
                    <span className={cfg.color}>{cfg.label}</span>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                    {issue.layer}
                  </span>
                </div>

                {/* Message */}
                <p className="text-xs text-foreground/90 leading-relaxed">
                  {issue.message}
                </p>

                {/* Field Path Link + Go to Field Button */}
                <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[11px]">
                  <button
                    type="button"
                    onClick={() => handleGoToField(issue.field_path)}
                    className="font-mono text-primary hover:underline truncate max-w-[170px] text-left"
                    title={`Jump to ${issue.field_path}`}
                  >
                    {issue.field_path}
                  </button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleGoToField(issue.field_path)}
                    className="h-6 px-2 text-[10px] gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <span>Go to field</span>
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pinned Bottom Button: "Ask AI to propose fixes" */}
      <div className="p-2.5 border-t border-border bg-card/90 shrink-0">
        <Button
          onClick={() => setActiveRightTab('chat')}
          variant="outline"
          size="sm"
          className="w-full gap-2 text-xs font-semibold shadow-xs hover:border-primary/50"
        >
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          <span>Ask AI to propose fixes</span>
        </Button>
      </div>
    </div>
  );
}
