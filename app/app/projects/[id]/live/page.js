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
  const declaredCommands = spec?.behavior?.fields?.declared_commands?.value || [
    'TRIGGER_FAN_FORCE_ON',
    'TRIGGER_FAN_AUTO',
    'REBOOT_NODE',
  ];

  useEffect(() => {
    async function loadData() {
      const [devs, tData] = await Promise.all([
        api.getDevices(projectId),
        api.getTelemetry('dev-node-alpha'),
      ]);
      setDevices(devs);
      setTelemetry(tData);
      if (project?.lifecycle === 'deployed') {
        setDeployed(true);
      }
    }
    loadData();
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
    setCommandStatus(`Sending command ${cmd}...`);
    try {
      const res = await api.sendDeviceCommand(targetDevice, cmd);
      setCommandStatus(`Executed "${cmd}" successfully at ${new Date().toLocaleTimeString()}!`);
      setTimeout(() => setCommandStatus(''), 4000);
    } catch (err) {
      setCommandStatus(`Error: ${err.message}`);
    }
  };

  const handleCopySecret = () => {
    if (newDeviceSecretModal?.secret) {
      navigator.clipboard.writeText(newDeviceSecretModal.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

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
            Real-time telemetry streaming from live ESP32-S3 nodes via FastAPI MQTT broker.
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
              <span>Current Temperature</span>
              <Activity className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">
              {telemetry[telemetry.length - 1]?.value || 29.5}°C
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">Ventilation trigger: 30.0°C</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Relative Humidity</span>
              <Activity className="h-4 w-4 text-sky-500" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">64.2%</div>
            <p className="text-[11px] text-muted-foreground mt-1">Optimal greenhouse range</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Fan Relay Status</span>
              <Power className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">AUTO (OFF)</div>
            <p className="text-[11px] text-muted-foreground mt-1">GPIO9 active-high relay</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs text-muted-foreground mb-1">
              <span>Connected Nodes</span>
              <Cpu className="h-4 w-4 text-primary" />
            </div>
            <div className="text-2xl font-extrabold text-foreground">{devices.length} Online</div>
            <p className="text-[11px] text-emerald-500 mt-1">MQTT TLS v1.3 healthy</p>
          </CardContent>
        </Card>
      </div>

      {/* Telemetry Chart */}
      <Card>
        <CardHeader className="p-5 border-b flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base">Real-Time Climate Telemetry (BME280)</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">Streamed every 60s between deep sleep intervals</p>
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
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetry} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                <XAxis dataKey="timestamp" stroke="#64748b" fontSize={11} />
                <YAxis domain={[20, 40]} stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8 }}
                  itemStyle={{ fontSize: 12 }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  name="Temperature (°C)"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#10b981' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
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
                    <CardTitle className="text-base">Hardware Command Dispatcher</CardTitle>
                  </div>
                  <Badge variant="confirmed">Spec Declared</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Commands are strictly bound to declared actions in section 4 (Behavior). Arbitrary commands are rejected by FastAPI.
                </p>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
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

                {commandStatus && (
                  <div className="p-3 rounded-lg bg-muted text-xs font-mono text-primary animate-in fade-in">
                    {commandStatus}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Role-Based Access Control Preview */}
          <div className="lg:col-span-5">
            <Card>
              <CardHeader className="p-5 border-b">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  <CardTitle className="text-base">Role-Based Access (RBAC)</CardTitle>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Web app user permissions and session control</p>
              </CardHeader>
              <CardContent className="p-5 space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg border bg-muted/20">
                  <div>
                    <div className="font-semibold text-foreground">Operator (Field Staff)</div>
                    <div className="text-muted-foreground text-[11px]">Can view telemetry and toggle FAN_AUTO</div>
                  </div>
                  <Badge variant="defaulted">1 Member</Badge>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg border bg-muted/20">
                  <div>
                    <div className="font-semibold text-foreground">Engineer (Admin)</div>
                    <div className="text-muted-foreground text-[11px]">Full command dispatch + firmware OTA</div>
                  </div>
                  <Badge variant="confirmed">Active</Badge>
                </div>
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
              Burn this token into the ESP32 NVS partition or provide it over USB serial during initial enrollment.
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
