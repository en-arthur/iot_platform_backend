'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, ArrowRight } from 'lucide-react';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { useUIStore } from '@/lib/store/useUIStore';

const SEVERITY_CONFIG = {
  error: { icon: AlertCircle, color: 'text-destructive', badge: 'destructive' },
  warning: { icon: AlertTriangle, color: 'text-amber-500', badge: 'open' },
  info: { icon: Info, color: 'text-sky-500', badge: 'from_library' },
};

export function ValidationPanel({ issues, onSelectField }) {
  const { setActiveSpecSection } = useUIStore();

  const grouped = {
    electrical: issues.filter((i) => i.layer === 'electrical'),
    completeness: issues.filter((i) => i.layer === 'completeness'),
    logical: issues.filter((i) => i.layer === 'logical'),
    resource: issues.filter((i) => i.layer === 'resource'),
    security: issues.filter((i) => i.layer === 'security'),
  };

  const layersWithIssues = Object.entries(grouped).filter(([_, list]) => list.length > 0);

  const handleNavigateToField = (fieldPath) => {
    const [section] = fieldPath.split('.');
    if (section) {
      setActiveSpecSection(section);
      onSelectField?.(fieldPath);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-foreground">Validation Issues</h4>
        <span className="text-xs font-mono text-muted-foreground">
          {issues.length} {issues.length === 1 ? 'finding' : 'findings'}
        </span>
      </div>

      {issues.length === 0 ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 text-center space-y-2">
          <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
          <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
            Spec Passes All Rules
          </div>
          <p className="text-xs text-muted-foreground">
            Zero electrical conflicts or blocking completeness issues found. Ready for confirmation.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {layersWithIssues.map(([layer, list]) => (
            <div key={layer} className="rounded-xl border border-border bg-card p-3.5 space-y-3">
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  {layer} Layer
                </span>
                <span className="text-xs font-mono text-muted-foreground">{list.length}</span>
              </div>

              <div className="space-y-2.5">
                {list.map((issue) => {
                  const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.info;
                  const Icon = cfg.icon;
                  return (
                    <div
                      key={issue.id}
                      onClick={() => handleNavigateToField(issue.field_path)}
                      className="group p-2.5 rounded-lg border border-border/80 hover:border-primary/40 bg-muted/20 hover:bg-muted/40 cursor-pointer transition-all space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5 font-semibold">
                          <Icon className={`h-3.5 w-3.5 ${cfg.color}`} />
                          <span className="capitalize">{issue.severity}</span>
                        </div>
                        <Badge variant={cfg.badge} className="text-[10px] py-0 px-1.5">
                          {issue.field_path}
                        </Badge>
                      </div>
                      <p className="text-xs text-foreground/90 leading-relaxed">{issue.message}</p>
                      <div className="flex items-center gap-1 text-[11px] text-primary group-hover:underline pt-1">
                        <span>Jump to field</span>
                        <ArrowRight className="h-3 w-3" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
