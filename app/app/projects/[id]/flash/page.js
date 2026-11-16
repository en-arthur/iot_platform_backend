'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
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
  const [baudRate, setBaudRate] = useState('921600');
  const [flashing, setFlashing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [flashDone, setFlashDone] = useState(false);
  const [logs, setLogs] = useState([]);

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
        if (!cancelled) setError(err?.message || 'Could not load builds.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const artifactReady = Boolean(run?.artifact_available);
  const isUf2 = run?.artifact_format === 'uf2';

  const handleConnect = async () => {
    setError(null);
    try {
      if (!('serial' in navigator)) return;
      const selected = await navigator.serial.requestPort();
      setPort(selected);
      setFlashDone(false);
      const info = selected.getInfo?.() || {};
      addLog(
        `Serial port selected (VID ${info.usbVendorId ?? 'unknown'}, PID ${info.usbProductId ?? 'unknown'}).`
      );
    } catch (err) {
      if (err?.name !== 'NotFoundError') {
        addLog(`Port selection failed: ${err?.message || err}`);
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
      addLog('Loading the verified artifact…');
      const manifest = await api.getFirmwareArtifact(run.run_id);
      if (manifest.format !== 'esp-segments') {
        throw new Error('This artifact is not a Web Serial image.');
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
        baudrate: Number(baudRate),
        terminal,
      });

      addLog('Connecting to the bootloader…');
      const chip = await loader.main();
      addLog(`Chip detected: ${chip}`);

      const totalBytes = manifest.segments.reduce((sum, item) => sum + item.size, 0);
      const beforeFile = (index) =>
        manifest.segments
          .slice(0, index)
          .reduce((sum, item) => sum + item.size, 0);

      addLog(
        `Writing ${manifest.segments.length} image(s), ${formatBytes(totalBytes) || `${totalBytes} B`} total.`
      );
      for (const segment of manifest.segments) {
        addLog(`  ${segment.name} → ${'0x' + segment.offset.toString(16)}`);
      }

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
      addLog('Flash complete. Resetting the board…');
      await loader.after();
      setFlashDone(true);
      addLog('Board reset. Open a serial monitor at 115200 baud to see its output.');
    } catch (err) {
      addLog(`[FLASH ERROR] ${err?.message || err}`);
      setError(err?.message || 'Flashing failed.');
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
      setError(err?.message || 'Could not download the artifact.');
    }
  };

  return (
    <div className="container max-w-6xl p-6 md:p-8 space-y-8 h-full overflow-y-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Zap className="h-6 w-6 text-amber-500" />
          <span>Firmware Flasher</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Writes the images from a passed build to the board over Web Serial, at the offsets
          PlatformIO chose.
        </p>
      </div>

      {!hasSerialSupport && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-1 text-sm">
            <h4 className="font-semibold text-foreground">
              Web Serial is not available in this browser
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Use Chrome, Edge, or Opera on desktop to flash over USB. You can still download
              the verified image below.
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
          Loading the latest build…
        </div>
      ) : !run ? (
        <Card>
          <CardContent className="p-10 flex flex-col items-center text-center gap-3">
            <Usb className="h-10 w-10 text-muted-foreground" />
            <div className="text-sm font-semibold text-foreground">No build to flash</div>
            <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
              Run a build first. Flashing is only enabled for a run that produced a real
              firmware image.
            </p>
            <Link
              href={`/app/projects/${projectId}/verify`}
              className="text-xs font-semibold text-primary hover:underline mt-2"
            >
              Go to Build Verification
            </Link>
          </CardContent>
        </Card>
      ) : !artifactReady ? (
        <Card>
          <CardContent className="p-10 flex flex-col items-center text-center gap-3">
            <AlertTriangle className="h-10 w-10 text-amber-500" />
            <div className="text-sm font-semibold text-foreground">
              This build has no firmware artifact
            </div>
            <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
              {run.status === 'passed'
                ? 'The build passed, but no image was stored. Re-run verification to rebuild it.'
                : 'The most recent build did not pass, so there is nothing to flash.'}
            </p>
            <Link
              href={`/app/projects/${projectId}/verify`}
              className="text-xs font-semibold text-primary hover:underline mt-2"
            >
              Go to Build Verification
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
                  <span>Verified Artifact</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-muted/30">
                  <div className="min-w-0">
                    <div className="text-xs font-semibold font-mono truncate">
                      {run.artifact_name}
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {formatBytes(run.artifact_size_bytes) || 'Size unknown'} ·{' '}
                      {run.board_id || 'Unknown board'}
                    </div>
                  </div>
                  <Badge variant="confirmed">Verified</Badge>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full gap-2 text-xs"
                  onClick={handleDownload}
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download {run.artifact_name}</span>
                </Button>

                {isUf2 ? (
                  <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground space-y-2">
                    <div className="font-semibold text-foreground">
                      UF2 board: copy the file instead
                    </div>
                    <p className="leading-relaxed">
                      Web Serial flashing is for ESP32/ESP8266. For RP2040 boards, hold BOOTSEL
                      while plugging in USB, then copy the downloaded UF2 file to the RPI-RP2
                      drive.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Baud Rate
                      </label>
                      <select
                        value={baudRate}
                        onChange={(event) => setBaudRate(event.target.value)}
                        disabled={flashing}
                        className="w-full text-xs font-mono rounded-md border border-input bg-background p-2"
                      >
                        <option value="921600">921,600</option>
                        <option value="460800">460,800</option>
                        <option value="115200">115,200</option>
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
                          <span>Connect USB Port</span>
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
                          <span>{flashing ? 'Flashing…' : 'Flash Firmware'}</span>
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
                  <span className="font-semibold text-foreground">Write progress</span>
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
                    ? 'Flash finished. The board was reset.'
                    : port
                    ? 'Port selected. Ready to flash.'
                    : 'Select the board’s USB port to begin.'}
                </p>
              </div>
            )}

            {flashDone && (
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <div className="font-semibold text-emerald-600 dark:text-emerald-400">
                    Firmware written
                  </div>
                  <p className="text-muted-foreground mt-0.5">
                    esptool reported success for every image. No device self-test was run.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                <span>Flasher Output</span>
              </h2>
              <span className="text-[10px] font-mono text-muted-foreground">
                {baudRate} baud
              </span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 h-[430px] overflow-y-auto space-y-0.5">
              {logs.length === 0 ? (
                <div className="text-slate-500 italic py-8 text-center">
                  {port ? 'Ready.' : 'Connect the board’s USB port to begin.'}
                </div>
              ) : (
                logs.map((line, index) => (
                  <div
                    key={index}
                    className={`whitespace-pre-wrap ${
                      line.includes('[FLASH ERROR]') ? 'text-red-400' : ''
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
