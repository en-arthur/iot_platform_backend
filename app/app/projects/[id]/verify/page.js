'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Download,
  Loader2,
  Play,
  Terminal,
  XCircle,
} from 'lucide-react';

const STATUS = {
  queued: { label: 'Waiting to start', variant: 'defaulted' },
  running: { label: 'Building', variant: 'defaulted' },
  passed: { label: 'Build succeeded', variant: 'confirmed' },
  failed: { label: 'Build failed', variant: 'destructive' },
};

function formatBytes(value) {
  if (typeof value !== 'number' || value <= 0) return null;
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}

function logTone(line) {
  if (/\[BUILD FAILED\]|\[VERIFICATION ERROR\]|\[PREFLIGHT ERROR\]|error:/i.test(line)) {
    return 'text-red-400';
  }
  if (/\[ARTIFACT\]|\[BUILD SIZE\]/i.test(line)) return 'text-emerald-400';
  if (/\[ARTIFACT WARNING\]|\[SANDBOX ERROR\]|\[SIZE REPORT SKIPPED\]/i.test(line)) {
    return 'text-amber-400';
  }
  if (line.startsWith('$')) return 'text-sky-400';
  return 'text-slate-400';
}

export default function VerificationPage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const [run, setRun] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState(null);
  const [boardNames, setBoardNames] = useState({});

  const storageKey = `iot-verify-run-${projectId}`;

  const applyRun = (data) => {
    setRun(data);
    setLogs(Array.isArray(data?.logs) ? data.logs : []);
  };

  const fetchLatest = async () => {
    setLoading(true);
    setError(null);
    try {
      const runs = await api.getProjectRuns(projectId);
      const storedId =
        typeof window !== 'undefined' ? window.localStorage.getItem(storageKey) : null;
      const selected =
        runs.find((item) => item.run_id === storedId) || runs[0] || null;
      if (selected) {
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(storageKey, selected.run_id);
        }
        applyRun(selected);
      } else {
        applyRun(null);
      }
    } catch (err) {
      setError(err?.message || 'We could not load your builds.');
      applyRun(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatest();
    api
      .getBoards()
      .then((boards) => {
        const map = {};
        (Array.isArray(boards) ? boards : []).forEach((board) => {
          if (board?.id) map[board.id] = board.name;
        });
        setBoardNames(map);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const pollRun = async (id) => {
    for (let attempt = 0; attempt < 90; attempt += 1) {
      let data;
      try {
        data = await api.getVerificationRun(id);
      } catch {
        return;
      }
      applyRun(data);
      if (data.status !== 'running' && data.status !== 'queued') return;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  };

  const handleTrigger = async () => {
    setTriggering(true);
    setError(null);
    try {
      const res = await api.triggerVerify(projectId);
      const id = res?.run_id;
      if (id) {
        window.localStorage.setItem(storageKey, id);
        applyRun(null);
        setLogs(['Starting your build…']);
        await pollRun(id);
      }
    } catch (err) {
      setError(err?.message || 'We could not start the build.');
    } finally {
      setTriggering(false);
    }
  };

  const handleDownload = async () => {
    if (!run?.artifact_available) return;
    try {
      await api.downloadFirmware(run.run_id, run.artifact_name || 'firmware.bin');
    } catch (err) {
      setError(err?.message || 'We could not download the firmware.');
    }
  };

  const configError = logs.find((line) =>
    /E2B is not configured|template .* not found|template .* does not exist/i.test(line)
  );
  const status = STATUS[run?.status] || STATUS.queued;
  const sizeLabel = formatBytes(run?.artifact_size_bytes);
  const isRunning = run?.status === 'running' || run?.status === 'queued';
  const boardLabel = run?.board_id ? boardNames[run.board_id] || run.board_id : 'Board not recorded';

  return (
    <div className="container max-w-7xl p-6 md:p-8 space-y-8 h-full overflow-y-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span>Build Check</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            We build your project on a clean machine and show exactly what happened. When it
            succeeds, you get a firmware file ready to install on your device.
          </p>
        </div>

        <Button
          onClick={handleTrigger}
          disabled={triggering || isRunning}
          className="gap-2 shadow"
        >
          {triggering || isRunning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          <span>{run ? 'Build Again' : 'Build Firmware'}</span>
        </Button>
      </div>

      <p className="text-xs text-muted-foreground -mt-4">
        This checks that your code builds. It does not test a physical device.
      </p>

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 flex items-start gap-2 text-sm">
          <XCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {configError && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-1 text-sm">
            <div className="font-semibold text-foreground">
              Building is not available on this server yet
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              The build machine could not be started. This is a setup issue on our side — your
              project is fine.
            </p>
            <code className="block text-[11px] font-mono text-amber-700 dark:text-amber-400 pt-1">
              {configError}
            </code>
          </div>
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-border bg-card p-10 flex items-center justify-center text-sm text-muted-foreground gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading builds…
        </div>
      ) : !run ? (
        <Card>
          <CardContent className="p-10 flex flex-col items-center text-center gap-3">
            <Terminal className="h-10 w-10 text-muted-foreground" />
            <div className="text-sm font-semibold text-foreground">Nothing built yet</div>
            <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
              Build your project once to check it and get a firmware file. Your project must be
              generated before it can be built.
            </p>
            <Button onClick={handleTrigger} disabled={triggering} className="gap-2 mt-2">
              <Play className="h-4 w-4" />
              <span>Build Firmware</span>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-border bg-card p-4 space-y-2">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Result
              </div>
              <Badge variant={status.variant} className="gap-1.5">
                {run.status === 'passed' && <CheckCircle2 className="h-3 w-3" />}
                {run.status === 'failed' && <XCircle className="h-3 w-3" />}
                {isRunning && <Loader2 className="h-3 w-3 animate-spin" />}
                {status.label}
              </Badge>
              <div className="text-[11px] font-mono text-muted-foreground">
                {run.run_id}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 space-y-2">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Device
              </div>
              <div className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <Cpu className="h-4 w-4 text-primary" />
                <span>{boardLabel}</span>
              </div>
              <div className="text-[11px] text-muted-foreground">
                Plan version {run.version_number ?? 1}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 space-y-2">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Firmware
              </div>
              {run.artifact_available ? (
                <>
                  <div className="text-sm font-semibold text-foreground font-mono truncate">
                    {run.artifact_name}
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {sizeLabel || 'Size unknown'}
                    {run.artifact_format === 'uf2' ? ' · copy-to-device file' : ' · ready to install'}
                  </div>
                </>
              ) : (
                <div className="text-xs text-muted-foreground">
                  {run.status === 'passed'
                    ? 'The build succeeded, but no firmware file was saved.'
                    : 'No firmware file for this build.'}
                </div>
              )}
            </div>

            <div className="rounded-xl border border-border bg-card p-4 space-y-2">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                What&apos;s next
              </div>
              {run.artifact_available ? (
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">
                    You can install this firmware on your device over USB.
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Link
                      href={`/app/projects/${projectId}/flash`}
                      className="text-xs font-semibold text-primary hover:underline"
                    >
                      Install firmware
                    </Link>
                    <button
                      type="button"
                      onClick={handleDownload}
                      className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1"
                    >
                      <Download className="h-3 w-3" />
                      Download
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">
                  {run.status === 'failed'
                    ? 'Fix the error shown below, then build again.'
                    : 'Waiting for a successful build.'}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                <span>Build Output</span>
              </h2>
              <span className="text-[10px] font-mono text-muted-foreground">
                Built on a clean machine
              </span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs h-96 overflow-y-auto space-y-0.5">
              {logs.length === 0 ? (
                <div className="text-slate-500 italic">No output recorded.</div>
              ) : (
                logs.map((line, index) => (
                  <div key={index} className={`whitespace-pre-wrap ${logTone(line)}`}>
                    {line}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
