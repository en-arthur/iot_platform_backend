'use client';

import React, { useState, useEffect, use } from 'react';
import { api } from '@/lib/api';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
  CheckCircle2,
  XCircle,
  Play,
  RotateCw,
  Sparkles,
  Terminal,
  Activity,
  Check,
  X,
  Loader2,
} from 'lucide-react';

const STEP_ICONS = {
  compile: '1. ESP-IDF Compile',
  simulate: '2. QEMU Emulation',
  flash: '3. Virtual Flash',
  selftest: '4. Silicon Self-Test',
};

export default function VerificationPage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const { approveProposal, isSaving, loadProjectAndSpec } = useSpecStore();

  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [logs, setLogs] = useState([]);
  const [activeFix, setActiveFix] = useState(null);
  const [runId, setRunId] = useState(null);

  const storageKey = `iot-verify-run-${projectId}`;

  const applyRun = (data) => {
    setRun(data);
    setLogs(data.logs || []);
    // Check if any failed test has an AI fix proposal
    const failedWithFix = data.tests?.find((t) => !t.passed && t.fix_proposal);
    setActiveFix(failedWithFix ? failedWithFix.fix_proposal : null);
  };

  const fetchRunData = async (id = runId) => {
    if (!id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      applyRun(await api.getVerificationRun(id));
    } catch {
      setRun(null);
      setLogs([]);
      setActiveFix(null);
    } finally {
      setLoading(false);
    }
  };

  // Remember the last triggered run id between visits.
  useEffect(() => {
    const stored = window.localStorage.getItem(storageKey);
    setRunId(stored || null);
    if (!stored) setLoading(false);
  }, [storageKey]);

  useEffect(() => {
    if (runId) fetchRunData(runId);
  }, [runId]);

  // Poll while the pipeline is still running so logs/steps appear live.
  const pollRun = async (id) => {
    for (let attempt = 0; attempt < 15; attempt += 1) {
      let data;
      try {
        data = await api.getVerificationRun(id);
      } catch {
        return;
      }
      applyRun(data);
      if (data.status !== 'running') return;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  };

  const handleTriggerVerify = async () => {
    setTriggering(true);
    try {
      const res = await api.triggerVerify(projectId);
      const id = res?.run_id;
      if (id) {
        window.localStorage.setItem(storageKey, id);
        setRunId(id);
        await pollRun(id);
      }
    } finally {
      setTriggering(false);
    }
  };

  const handleApproveFix = async () => {
    if (!activeFix) return;
    await approveProposal(projectId, activeFix.proposal_id);
    setActiveFix(null);
    await fetchRunData();
  };

  return (
    <div className="container max-w-7xl p-6 md:p-8 space-y-8 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span>Verification & Hardware-in-the-Loop (HIL)</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            End-to-end automated pipeline: Xtensa compilation, QEMU emulation, and bus self-tests.
          </p>
        </div>

        <Button
          onClick={handleTriggerVerify}
          disabled={triggering}
          className="gap-2 shadow"
        >
          {triggering ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Play className="h-4 w-4" />
              <span>Run Verification Pipeline</span>
            </>
          )}
        </Button>
      </div>

      {/* Pipeline Steps Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {run?.steps?.map((step) => {
          const isPassed = step.status === 'success';
          const isFailed = step.status === 'failed';
          const isRunning = step.status === 'running';

          return (
            <div
              key={step.name}
              className={`p-4 rounded-xl border transition-all ${
                isFailed
                  ? 'border-destructive/60 bg-destructive/5'
                  : isPassed
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : 'border-border bg-card'
              }`}
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-foreground">
                  {STEP_ICONS[step.name] || step.name}
                </span>
                {isPassed && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                {isFailed && <XCircle className="h-4 w-4 text-destructive" />}
                {isRunning && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
              </div>
              <div className="text-xs text-muted-foreground">{step.details}</div>
              {step.duration_ms && (
                <div className="mt-2 text-[10px] font-mono text-muted-foreground">
                  Duration: {(step.duration_ms / 1000).toFixed(2)}s
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* AI Automated Fix Card if failed */}
      {activeFix && (
        <Card className="border-2 border-primary/50 shadow-xl bg-gradient-to-r from-card to-primary/5">
          <CardHeader className="p-5 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <CardTitle className="text-base">AI Auto-Remediation Proposal</CardTitle>
              </div>
              <Badge variant="inferred">Self-Test Failure Fix</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">{activeFix.summary}</p>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="space-y-2 bg-muted/40 p-3 rounded-lg border font-mono text-xs">
              {activeFix.changes.map((c, i) => (
                <div key={i} className="space-y-1 border-b last:border-0 pb-2 last:pb-0">
                  <span className="text-primary font-bold">{c.path}</span>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <span className="text-destructive line-through">Old: {String(c.old ?? 'None')}</span>
                    <span className="text-emerald-500 font-bold">New: {String(c.new)}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground font-sans mt-0.5">{c.reason}</p>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveFix(null)}
                className="gap-1.5"
              >
                <X className="h-3.5 w-3.5" />
                <span>Dismiss</span>
              </Button>
              <Button
                size="sm"
                onClick={handleApproveFix}
                disabled={isSaving}
                className="gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white shadow"
              >
                {isSaving ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <>
                    <Check className="h-3.5 w-3.5" />
                    <span>Approve AI Fix & Bump Version</span>
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tests & Streaming Logs Grid */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Test Matrix (Col 1-5) */}
        <div className="lg:col-span-5 space-y-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Executed Test Cases
          </h2>
          <div className="space-y-2.5">
            {run?.tests?.map((test) => (
              <div
                key={test.id}
                className="p-3 rounded-xl border border-border bg-card flex items-start justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="font-semibold text-xs text-foreground flex items-center gap-1.5">
                    {test.passed ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-destructive shrink-0" />
                    )}
                    <span>{test.name}</span>
                  </div>
                  {test.message && (
                    <p className="text-[11px] text-muted-foreground leading-relaxed pl-5">
                      {test.message}
                    </p>
                  )}
                </div>
                <Badge
                  variant={test.passed ? 'confirmed' : 'destructive'}
                  className="text-[10px] shrink-0"
                >
                  {test.passed ? 'Passed' : 'Failed'}
                </Badge>
              </div>
            ))}
          </div>
        </div>

        {/* Live Streaming Logs (Col 6-12) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Terminal className="h-4 w-4 text-primary" />
              <span>Emulation & Build Logs</span>
            </h2>
            <span className="text-[10px] font-mono text-muted-foreground">UTF-8 Plaintext</span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 h-96 overflow-y-auto space-y-1">
            {logs.map((log, index) => (
              <div
                key={index}
                className={
                  log.includes('[FAIL]')
                    ? 'text-red-400 font-bold'
                    : log.includes('[PASS]')
                    ? 'text-emerald-400'
                    : 'text-slate-400'
                }
              >
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
