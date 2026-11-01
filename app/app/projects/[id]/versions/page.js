'use client';

import React, { useState, useEffect, use } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { formatDate } from '@/lib/utils';
import { History, GitCommit, ArrowRight, RefreshCw, RotateCcw, CheckCircle2 } from 'lucide-react';

export default function VersionsPage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const [versions, setVersions] = useState([]);
  const [selectedV1, setSelectedV1] = useState(1);
  const [selectedV2, setSelectedV2] = useState(2);
  const [diff, setDiff] = useState(null);
  const [loading, setLoading] = useState(true);
  const [diffLoading, setDiffLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const vList = await api.getVersions(projectId);
        setVersions(vList);
        if (vList.length > 1) {
          setSelectedV1(vList[vList.length - 2].version_number);
          setSelectedV2(vList[vList.length - 1].version_number);
        } else if (vList.length === 1) {
          setSelectedV1(vList[0].version_number);
          setSelectedV2(vList[0].version_number);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [projectId]);

  useEffect(() => {
    async function loadDiff() {
      if (!selectedV1 || !selectedV2) return;
      setDiffLoading(true);
      try {
        const d = await api.getVersionDiff(projectId, selectedV1, selectedV2);
        setDiff(d);
      } finally {
        setDiffLoading(false);
      }
    }
    loadDiff();
  }, [projectId, selectedV1, selectedV2]);

  return (
    <div className="container max-w-7xl p-6 md:p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <History className="h-6 w-6 text-primary" />
          <span>Spec Version History & Diff</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Every modification after confirmation creates an immutable version snapshot with full audit provenance.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Version List (Col 1-5) */}
        <div className="lg:col-span-5 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Version Timeline ({versions.length})
          </h2>

          <div className="space-y-3">
            {versions.map((ver) => (
              <div
                key={ver.version_number}
                className="rounded-xl border border-border bg-card p-4 shadow-sm hover:border-primary/50 transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GitCommit className="h-4 w-4 text-primary" />
                    <span className="font-bold text-sm text-foreground">
                      Version {ver.version_number}.0
                    </span>
                  </div>
                  <Badge variant="confirmed" className="text-[10px]">
                    {ver.lifecycle || 'confirmed'}
                  </Badge>
                </div>

                <p className="text-xs text-foreground/90">{ver.summary}</p>

                <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/40">
                  <span>By {ver.author}</span>
                  <span>{formatDate(ver.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Side-by-Side Diff Comparison (Col 6-12) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Side-by-Side Diff Inspection
            </h2>
            <div className="flex items-center gap-2 text-xs">
              <span>Compare v{selectedV1}</span>
              <ArrowRight className="h-3 w-3 text-muted-foreground" />
              <span>v{selectedV2}</span>
            </div>
          </div>

          <Card>
            <CardHeader className="p-4 border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-mono">
                  Diff: v{selectedV1}.0 &rarr; v{selectedV2}.0
                </CardTitle>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1.5">
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Redeploy Version {selectedV2}</span>
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              {diffLoading ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  Calculating spec AST diff...
                </div>
              ) : !diff || diff.differences?.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  No differences found between selected versions.
                </div>
              ) : (
                <div className="space-y-3">
                  {diff.differences.map((change, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-border p-3 space-y-2 text-xs font-mono"
                    >
                      <div className="font-bold text-primary">{change.field_path}</div>
                      <div className="grid grid-cols-2 gap-3 bg-muted/40 p-2 rounded">
                        <div className="text-destructive line-through">
                          - {String(change.from ?? 'null')}
                        </div>
                        <div className="text-emerald-500 font-bold">
                          + {String(change.to)}
                        </div>
                      </div>
                      <div className="text-[11px] text-muted-foreground font-sans">
                        Reason: {change.reason}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
