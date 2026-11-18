'use client';

import React, { useState, useEffect, use } from 'react';
import { api } from '@/lib/api';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Radio,
  Sliders,
  Activity,
  Key,
  Shield,
  Users,
  AlertTriangle,
  Play,
  RotateCw,
  Copy,
  Check,
  Power,
  Cpu,
  Loader2,
} from 'lucide-react';

export default function LiveInterfacePage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const { project, spec } = useSpecStore();

  const [devices, setDevices] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [deploying, setDeploying] = useState(false);
  const [deployed, setDeployed] = useState(project?.lifecycle === 'deployed');
  const [activeRange, setActiveRange] = useState('1h');
  const [newDeviceSecretModal, setNewDeviceSecretModal] = useState(null);
  const [commandStatus, setCommandStatus] = useState('');
  const [copiedSecret, setCopiedSecret] = useState(false);

  // Interface type from spec or project
  const interfaceType = spec?.interface?.fields?.interface_type?.value || project?.interface_type || 'web app';
  const declaredCommands = spec?.behavior?.fields?.declared_commands?.value || [];

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        const devs = await api.getDevices(projectId);
        if (cancelled) return;
        const list = Array.isArray(devs) ? devs : [];
        setDevices(list);
        // Read the real telemetry of this project's devices. Nothing is shown
        // until a device has actually reported.
        const series = await Promise.all(
          list
            .slice(0, 5)
            .map((device) =>
              api.getTelemetry(device.id).catch(() => [])
            )
        );
        if (cancelled) return;
        const merged = series
          .flat()
          .filter(Boolean)
          .sort((a, b) => String(a.timestamp).localeCompare(String(b.timestamp)));
        setTelemetry(merged);
        if (project?.lifecycle === 'deployed') {
          setDeployed(true);
        }
      } catch {
        if (!cancelled) setTelemetry([]);
      }
    }
    loadData();
    // Keep the page current while it is open. This only re-reads data the
    // devices have already sent; nothing is invented.
    const timer = setInterval(loadData, 15000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [projectId, project]);

  const handleDeploy = async () => {
    setDeploying(true);
    try {
      await api.deployProject(projectId);
      setDeployed(true);
    } finally {
      setDeploying(false);
    }
  };

  const handleProvisionDevice = async () => {
    const newDev = await api.provisionDevice(projectId, {
      name: `Greenhouse Node ${devices.length + 1}`,
    });
    setDevices((prev) => [...prev, newDev]);
    setNewDeviceSecretModal(newDev); // Displays the secret ONCE!
  };

  const handleSendCommand = async (cmd) => {
    const targetDevice = devices[0]?.id;
    if (!targetDevice) {
      setCommandStatus('No device provisioned yet. Click "Provision New Device" first.');
      return;
    }
    setCommandStatus(`Sending ${cmd}…`);
    try {
      await api.sendDeviceCommand(targetDevice, cmd);
      setCommandStatus(
        `Command sent: ${cmd}. Your device acts on it the next time it checks in.`
      );
      setTimeout(() => setCommandStatus(''), 6000);
    } catch (err) {
      setCommandStatus(`Could not send the command: ${err.message}`);
    }
  };

  const handleCopySecret = () => {
    if (newDeviceSecretModal?.secret) {
      navigator.clipboard.writeText(newDeviceSecretModal.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

  // Only real readings are shown; a tile stays empty until a device reports.
  const formatTime = (value) => {
    if (!value) return '';
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
  };
  const latestOf = (needle) => {
    const match = telemetry
      .filter((entry) => String(entry.metric || '').toLowerCase().includes(needle))
      .slice(-1)[0];
    return match || null;
  };
  const latestTemp = latestOf('temp');
  const latestHumidity = latestOf('humid');
  const latestRelay = latestOf('relay') || latestOf('state');
  const lastReading = telemetry[telemetry.length - 1] || null;
  const chartData = latestTemp
    ? telemetry.filter((entry) =>
        String(entry.metric || '').toLowerCase().includes('temp')
      )
    : telemetry;

  return (
    <div className="container max-w-7xl p-6 md:p-8 space-y-8 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Radio className="h-6 w-6 text-emerald-500" />
              <span>Live {interfaceType === 'web app' ? 'Web App' : 'Dashboard'}</span>
            </h1>
            <Badge variant={interfaceType === 'web app' ? 'confirmed' : 'defaulted'}>
              {interfaceType === 'web app' ? 'Web App (Monitoring + Controls)' : 'Dashboard (Monitoring)'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Readings from your own devices show up here once they connect and
            start reporting.
          </p>
        </div>

        {!deployed ? (
          <Button onClick={handleDeploy} disabled={deploying} className="gap-2 shadow">
            {deploying ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Play className="h-4 w-4" />
                <span>Deploy to Cloud</span>
              </>
            )}
          </Button>
        ) : (
          <Button onClick={handleProvisionDevice} size="sm" variant="outline" className="gap-2">
            <Key className="h-4 w-4 text-primary" />
            <span>Provision New Device</span>
          </Button>
        )}
      </div>

      {/* KPI Tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Temperature</span>
              <Activity className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">
              {latestTemp ? `${latestTemp.value}${latestTemp.unit || '°C'}` : '—'}
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              {latestTemp ? `Last reading ${formatTime(latestTemp.timestamp)}` : 'No readings yet'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Humidity</span>
              <Activity className="h-4 w-4 text-sky-500" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">
              {latestHumidity ? `${latestHumidity.value}${latestHumidity.unit || '%'}` : '—'}
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              {latestHumidity ? `Last reading ${formatTime(latestHumidity.timestamp)}` : 'No readings yet'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Last Reported Output</span>
              <Power className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">
              {latestRelay ? String(latestRelay.value) : '—'}
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              {latestRelay
                ? `${latestRelay.metric} at ${formatTime(latestRelay.timestamp)}`
                : 'Your device has not reported an output state yet'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Devices</span>
              <Cpu className="h-4 w-4 text-primary" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">
              {devices.length === 0
                ? 'None yet'
                : `${devices.filter((d) => d.status === 'online').length} of ${devices.length} online`}
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              {lastReading
                ? `Most recent reading ${formatTime(lastReading.timestamp)}`
                : devices.length === 0
                  ? 'Add a device below to start reporting'
                  : 'Waiting for the first reading'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Telemetry Chart */}
      <Card>
        <CardHeader className="p-5 border-b flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base">Readings Over Time</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Plotted from what your device has actually sent.
            </p>
          </div>
          <div className="flex gap-1.5 bg-muted p-1 rounded-lg">
            {['1h', '6h', '24h', '7d'].map((r) => (
              <button
                key={r}
                onClick={() => setActiveRange(r)}
                className={`px-2.5 py-1 text-xs font-semibold rounded ${
                  activeRange === r ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="p-5">
          {chartData.length === 0 ? (
            <div className="h-72 w-full flex flex-col items-center justify-center gap-2 text-center">
              <Activity className="h-8 w-8 text-muted-foreground/40" />
              <p className="text-sm font-medium text-foreground">No readings yet</p>
              <p className="text-xs text-muted-foreground max-w-sm">
                Once your device is powered on, connected, and sending data, its
                readings will be drawn here. Nothing is shown until then.
              </p>
            </div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                  <XAxis
                    dataKey="timestamp"
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(value) => {
                      const parsed = new Date(value);
                      return Number.isNaN(parsed.getTime())
                        ? String(value)
                        : parsed.toLocaleTimeString();
                    }}
                  />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8 }}
                    itemStyle={{ fontSize: 12 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="Reading"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#10b981' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* WEB APP EXCLUSIVE CONTROLS & RBAC PANEL */}
      {interfaceType === 'web app' && (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Controls Panel (strictly mapped to spec behavior) */}
          <div className="lg:col-span-7">
            <Card className="border-primary/30">
              <CardHeader className="p-5 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sliders className="h-5 w-5 text-primary" />
                    <CardTitle className="text-base">Device Commands</CardTitle>
                  </div>
                  <Badge variant="confirmed">From your plan</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  These are the on/off actions described in your plan. The server
                  refuses any command that is not on this list.
                </p>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                {declaredCommands.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Your plan does not list any on/off actions for this device,
                    so there is nothing to send.
                  </p>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {declaredCommands.map((cmd) => (
                      <Button
                        key={cmd}
                        variant="outline"
                        onClick={() => handleSendCommand(cmd)}
                        className="h-12 justify-start font-mono text-xs gap-2 border-border/80 hover:border-primary"
                      >
                        <Power className="h-4 w-4 text-primary" />
                        <span>{cmd}</span>
                      </Button>
                    ))}
                  </div>
                )}

                {commandStatus && (
                  <div className="p-3 rounded-lg bg-muted text-xs font-mono text-primary animate-in fade-in">
                    {commandStatus}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Who can use this app */}
          <div className="lg:col-span-5">
            <Card>
              <CardHeader className="p-5 border-b">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  <CardTitle className="text-base">Who Can Use This</CardTitle>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Access to this dashboard</p>
              </CardHeader>
              <CardContent className="p-5 space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg border bg-muted/20">
                  <div>
                    <div className="font-semibold text-foreground">You (account owner)</div>
                    <div className="text-muted-foreground text-[11px]">
                      Can see readings and send the commands above
                    </div>
                  </div>
                  <Badge variant="confirmed">Signed in</Badge>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Sharing this dashboard with other people, and giving them
                  different permission levels, is not available yet. Anyone who
                  signs in to this account can use every control here.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* One-Time Provisioning Secret Dialog (Contract Requirement) */}
      {newDeviceSecretModal && (
        <Dialog open={Boolean(newDeviceSecretModal)} onOpenChange={() => setNewDeviceSecretModal(null)}>
          <DialogHeader>
            <div className="flex items-center gap-2 text-amber-500">
              <Key className="h-5 w-5" />
              <DialogTitle>Provisioning Secret Returned ONCE</DialogTitle>
            </div>
            <DialogDescription>
              Copy this device key immediately. For security, it will never be displayed again.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-3">
            <div className="text-xs font-semibold text-foreground">
              Device: {newDeviceSecretModal.name} ({newDeviceSecretModal.id})
            </div>
            <div className="flex items-center gap-2">
              <Input
                readOnly
                value={newDeviceSecretModal.secret}
                className="font-mono text-xs select-all bg-muted"
              />
              <Button size="icon" variant="outline" onClick={handleCopySecret} className="shrink-0">
                {copiedSecret ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Keep this key somewhere safe. Your device needs it the first time it
              connects, so enter it during device setup, or add it to the code
              before you install the firmware.
            </p>
          </div>

          <DialogFooter>
            <Button onClick={() => setNewDeviceSecretModal(null)}>
              I Have Saved This Key
            </Button>
          </DialogFooter>
        </Dialog>
      )}
    </div>
  );
}
