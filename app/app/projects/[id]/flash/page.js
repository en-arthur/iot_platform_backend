'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Download,
  Loader2,
  Terminal,
  Usb,
  Zap,
} from 'lucide-react';

function formatBytes(value) {
  if (typeof value !== 'number' || value <= 0) return null;
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}

export default function FlashPage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasSerialSupport, setHasSerialSupport] = useState(true);
  const [port, setPort] = useState(null);
  const [speed, setSpeed] = useState('921600');
  const [flashing, setFlashing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [flashDone, setFlashDone] = useState(false);
  const [logs, setLogs] = useState([]);
  const [boardNames, setBoardNames] = useState({});

  const addLog = (message) => {
    const text = String(message ?? '').trimEnd();
    if (!text) return;
    setLogs((prev) => [...prev, text]);
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setHasSerialSupport('serial' in navigator);
    }
    let cancelled = false;
    (async () => {
      try {
        const runs = await api.getProjectRuns(projectId);
        if (!cancelled) setRun(runs[0] || null);
      } catch (err) {
        if (!cancelled) setError(err?.message || 'We could not load your builds.');
      } finally {
        if (!cancelled) setLoading(false);
      }
      try {
        const boards = await api.getBoards();
        if (!cancelled) {
          const map = {};
          (Array.isArray(boards) ? boards : []).forEach((board) => {
            if (board?.id) map[board.id] = board.name;
          });
          setBoardNames(map);
        }
      } catch {
        // A missing board list only affects the label, not flashing.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const artifactReady = Boolean(run?.artifact_available);
  const isUf2 = run?.artifact_format === 'uf2';
  const boardLabel = run?.board_id ? boardNames[run.board_id] || run.board_id : null;

  const handleConnect = async () => {
    setError(null);
    if (!('serial' in navigator)) {
      setError(
        'This browser cannot talk to USB devices. Open this page in Chrome or Edge on a desktop computer, then try again.'
      );
      return;
    }
    try {
      const selected = await navigator.serial.requestPort();
      setPort(selected);
      setFlashDone(false);
      addLog('Device port connected.');
    } catch (err) {
      if (err?.name !== 'NotFoundError') {
        addLog(`We could not open that port: ${err?.message || err}`);
      }
    }
  };

  const handleFlash = async () => {
    if (!port || !run || flashing) return;
    setFlashing(true);
    setFlashDone(false);
    setProgress(0);
    setError(null);
    setLogs([]);

    let transport = null;
    try {
      addLog('Preparing your firmware…');
      const manifest = await api.getFirmwareArtifact(run.run_id);
      if (manifest.format !== 'esp-segments') {
        throw new Error('This firmware installs by copying a file, not over USB.');
      }

      const { ESPLoader, Transport } = await import('esptool-js');
      const terminal = {
        clean() {},
        writeLine(data) {
          addLog(data);
        },
        write(data) {
          addLog(data);
        },
      };

      transport = new Transport(port, true);
      const loader = new ESPLoader({
        transport,
        baudrate: Number(speed),
        terminal,
      });

      addLog('Connecting to your device…');
      const chip = await loader.main();
      addLog(`Connected: ${chip}`);

      const totalBytes = manifest.segments.reduce((sum, item) => sum + item.size, 0);
      const beforeFile = (index) =>
        manifest.segments
          .slice(0, index)
          .reduce((sum, item) => sum + item.size, 0);

      addLog(`Sending ${formatBytes(totalBytes) || `${totalBytes} B`} of firmware…`);

      await loader.writeFlash({
        fileArray: manifest.segments.map((segment) => ({
          data: atob(segment.data_b64),
          address: segment.offset,
        })),
        flashSize: 'keep',
        flashMode: 'keep',
        flashFreq: 'keep',
        eraseAll: false,
        compress: true,
        reportProgress: (fileIndex, written, total) => {
          const current = manifest.segments[fileIndex];
          const perFile = total > 0 ? written / total : 0;
          const overall =
            totalBytes > 0 && current
              ? (beforeFile(fileIndex) + perFile * current.size) / totalBytes
              : 0;
          setProgress(Math.min(100, Math.round(overall * 100)));
        },
      });

      setProgress(100);
      addLog('Finishing up and restarting your device…');
      await loader.after();
      setFlashDone(true);
      addLog('Done. Your device is running the new firmware.');
    } catch (err) {
      addLog(`Something went wrong: ${err?.message || err}`);
      setError(
        'We could not finish installing the firmware. Check that the device is plugged in and try again.'
      );
    } finally {
      setFlashing(false);
      if (transport) {
        try {
          await transport.disconnect();
        } catch {
          // Port may already be released after a failed connect.
        }
      }
    }
  };

  const handleDownload = async () => {
    if (!run) return;
    try {
      await api.downloadFirmware(run.run_id, run.artifact_name || 'firmware.bin');
    } catch (err) {
      setError(err?.message || 'We could not download the firmware.');
    }
  };

  return (
    <div className="container max-w-6xl p-6 md:p-8 space-y-8 h-full overflow-y-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Zap className="h-6 w-6 text-amber-500" />
          <span>Install Firmware</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Copies the firmware from your last successful build onto your device through the USB
          cable.
        </p>
      </div>

      {!hasSerialSupport && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-1 text-sm">
            <h4 className="font-semibold text-foreground">
              This browser cannot talk to USB devices
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Use Chrome or Edge on a computer to install directly. You can still download the
              firmware file below.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 flex items-start gap-2 text-sm">
          <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-border bg-card p-10 flex items-center justify-center text-sm text-muted-foreground gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading your latest build…
        </div>
      ) : !run ? (
        <Card>
          <CardContent className="p-10 flex flex-col items-center text-center gap-3">
            <Usb className="h-10 w-10 text-muted-foreground" />
            <div className="text-sm font-semibold text-foreground">No firmware to install yet</div>
            <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
              Build your project first. Installing only becomes available after a successful
              build produces a firmware file.
            </p>
            <Link
              href={`/app/projects/${projectId}/verify`}
              className="text-xs font-semibold text-primary hover:underline mt-2"
            >
              Go to Build Check
            </Link>
          </CardContent>
        </Card>
      ) : !artifactReady ? (
        <Card>
          <CardContent className="p-10 flex flex-col items-center text-center gap-3">
            <AlertTriangle className="h-10 w-10 text-amber-500" />
            <div className="text-sm font-semibold text-foreground">
              This build has no firmware file
            </div>
            <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
              {run.status === 'passed'
                ? 'The build succeeded, but the firmware file was not saved. Build again to recreate it.'
                : 'The most recent build did not succeed, so there is nothing to install yet.'}
            </p>
            <Link
              href={`/app/projects/${projectId}/verify`}
              className="text-xs font-semibold text-primary hover:underline mt-2"
            >
              Go to Build Check
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-5 space-y-4">
            <Card>
              <CardHeader className="p-5 border-b">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-primary" />
                  <span>Firmware Ready</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-muted/30">
                  <div className="min-w-0">
                    <div className="text-xs font-semibold font-mono truncate">
                      {run.artifact_name}
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {formatBytes(run.artifact_size_bytes) || 'Size unknown'}
                      {boardLabel ? ` · ${boardLabel}` : ''}
                    </div>
                  </div>
                  <Badge variant="confirmed">Built</Badge>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full gap-2 text-xs"
                  onClick={handleDownload}
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download firmware file</span>
                </Button>

                {isUf2 ? (
                  <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground space-y-2">
                    <div className="font-semibold text-foreground">
                      This device installs by copying a file
                    </div>
                    <p className="leading-relaxed">
                      Hold the BOOTSEL button while you plug the device in, then copy the
                      downloaded file onto the drive that appears.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Transfer speed
                      </label>
                      <select
                        value={speed}
                        onChange={(event) => setSpeed(event.target.value)}
                        disabled={flashing}
                        className="w-full text-xs rounded-md border border-input bg-background p-2"
                      >
                        <option value="921600">Fast (recommended)</option>
                        <option value="460800">Normal</option>
                        <option value="115200">Slow (try this if installing fails)</option>
                      </select>
                    </div>

                    <div className="space-y-2 pt-1">
                      {!port ? (
                        <Button
                          onClick={handleConnect}
                          disabled={!hasSerialSupport || flashing}
                          className="w-full gap-2 shadow"
                        >
                          <Usb className="h-4 w-4" />
                          <span>Connect Device</span>
                        </Button>
                      ) : (
                        <Button
                          onClick={handleFlash}
                          disabled={flashing}
                          className="w-full gap-2 bg-amber-600 hover:bg-amber-500 text-white shadow"
                        >
                          {flashing ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Zap className="h-4 w-4" />
                          )}
                          <span>{flashing ? 'Installing…' : 'Install on Device'}</span>
                        </Button>
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {!isUf2 && (
              <div className="rounded-xl border border-border bg-card p-4 space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-foreground">Install progress</span>
                  <span className="font-mono text-muted-foreground">{progress}%</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300 rounded-full"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {flashDone
                    ? 'All done. Your device restarted with the new firmware.'
                    : port
                    ? 'Device connected. Ready to install.'
                    : 'Connect your device with a USB cable to begin.'}
                </p>
              </div>
            )}

            {flashDone && (
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <div className="font-semibold text-emerald-600 dark:text-emerald-400">
                    Firmware installed
                  </div>
                  <p className="text-muted-foreground mt-0.5">
                    Your device is running the new firmware. No tests were run on the device.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                <span>Install Details</span>
              </h2>
              <span className="text-[10px] font-mono text-muted-foreground">
                {speed === '921600' ? 'Fast' : speed === '460800' ? 'Normal' : 'Slow'}
              </span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 h-[430px] overflow-y-auto space-y-0.5">
              {logs.length === 0 ? (
                <div className="text-slate-500 italic py-8 text-center">
                  {port ? 'Ready.' : 'Connect your device to begin.'}
                </div>
              ) : (
                logs.map((line, index) => (
                  <div
                    key={index}
                    className={`whitespace-pre-wrap ${
                      line.includes('Something went wrong') ? 'text-red-400' : ''
                    }`}
                  >
                    {line}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
