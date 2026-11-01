'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input, Textarea } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Cpu,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Layers,
  Activity,
  Sliders,
  Shield,
  Loader2,
  Sparkles,
} from 'lucide-react';

const STEPS = [
  { id: 1, title: 'Name & Goal' },
  { id: 2, title: 'Hardware & Peripherals' },
  { id: 3, title: 'Behavior & Logic' },
  { id: 4, title: 'Interface Type' },
];

export default function NewProjectWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');
  const [selectedBoard, setSelectedBoard] = useState('esp32-s3-devkitc-1');
  const [selectedPeripherals, setSelectedPeripherals] = useState(['bme280', 'relay-module-5v']);
  const [behaviorPrompt, setBehaviorPrompt] = useState(
    'Read temperature and humidity every 60 seconds. Put the MCU in deep sleep between cycles. If temperature exceeds 30°C, energize the fan relay. If it exceeds 35°C for 10 minutes, dispatch an urgent cloud alert over MQTT.'
  );
  const [interfaceType, setInterfaceType] = useState('web app'); // 'dashboard' | 'web app'

  // Library Data
  const [boards, setBoards] = useState([]);
  const [peripherals, setPeripherals] = useState([]);

  useEffect(() => {
    async function loadLibrary() {
      const [b, p] = await Promise.all([api.getBoards(), api.getPeripherals()]);
      setBoards(b);
      setPeripherals(p);
    }
    loadLibrary();
  }, []);

  const togglePeripheral = (id) => {
    setSelectedPeripherals((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const project = await api.createProject({
        name: name || 'Smart Greenhouse Node',
        description: goal || behaviorPrompt,
        board_id: selectedBoard,
        interface_type: interfaceType,
      });
      router.push(`/app/projects/${project.id}`);
    } catch (err) {
      alert(`Failed to create project: ${err.message}`);
      setSubmitting(false);
    }
  };

  return (
    <div className="container max-w-4xl p-6 md:p-10 space-y-8 pb-24">
      {/* Stepper Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Create New Hardware Project</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Provide your requirements in plain language. AI will synthesize the 12-section project spec.
        </p>
      </div>

      <div className="flex items-center justify-between border-b border-border pb-4">
        {STEPS.map((s, idx) => (
          <div key={s.id} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                currentStep === s.id
                  ? 'bg-primary text-primary-foreground ring-2 ring-primary/30'
                  : currentStep > s.id
                  ? 'bg-emerald-500/20 text-emerald-500'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {currentStep > s.id ? <CheckCircle2 className="h-4 w-4" /> : s.id}
            </div>
            <span
              className={`text-xs font-medium hidden sm:inline ${
                currentStep === s.id ? 'text-foreground font-semibold' : 'text-muted-foreground'
              }`}
            >
              {s.title}
            </span>
            {idx < STEPS.length - 1 && <span className="text-border mx-2 hidden sm:inline">—</span>}
          </div>
        ))}
      </div>

      {/* Step 1: Name and Goal */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Project Name & Objectives</CardTitle>
            <CardDescription>
              Identify your device and summarize its physical deployment scenario.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Project Name
              </label>
              <Input
                placeholder="e.g. Smart Greenhouse Climate Monitor"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                High-Level Goal & Context
              </label>
              <Textarea
                rows={4}
                placeholder="e.g. Battery-powered agricultural node placed in an enclosed greenhouse to monitor humidity, log barometric shifts, and actuate a ventilation exhaust fan."
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Board & Peripherals */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Verified Hardware Library Selection</CardTitle>
            <CardDescription>
              Choose your target MCU board and connected sensors or actuators.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-3">
                Target Development Board
              </label>
              <div className="grid gap-3 sm:grid-cols-3">
                {boards.map((b) => (
                  <div
                    key={b.id}
                    onClick={() => setSelectedBoard(b.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedBoard === b.id
                        ? 'border-primary bg-primary/5 ring-1 ring-primary'
                        : 'border-border hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <Cpu className="h-5 w-5 text-primary" />
                      <Badge variant={b.status === 'tested' ? 'confirmed' : b.status === 'draft' ? 'defaulted' : 'open'}>
                        {b.status}
                      </Badge>
                    </div>
                    <div className="font-semibold text-sm text-foreground">{b.name}</div>
                    <div className="text-xs text-muted-foreground mt-1">{b.mcu}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-3">
                Peripherals & Components
              </label>
              <div className="grid gap-3 sm:grid-cols-2">
                {peripherals.map((p) => {
                  const isChecked = selectedPeripherals.includes(p.id);
                  return (
                    <div
                      key={p.id}
                      onClick={() => togglePeripheral(p.id)}
                      className={`p-3.5 rounded-xl border cursor-pointer flex items-start gap-3 transition-all ${
                        isChecked
                          ? 'border-primary bg-primary/5 ring-1 ring-primary'
                          : 'border-border hover:bg-muted/50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="mt-1"
                      />
                      <div className="text-xs space-y-1">
                        <div className="font-semibold text-foreground flex items-center gap-2">
                          <span>{p.name}</span>
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            {p.interface}
                          </span>
                        </div>
                        <p className="text-muted-foreground">{p.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Behavior */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Behavior & Operational Rules</CardTitle>
            <CardDescription>
              State sampling rates, power modes, thresholds, and actuation logic in natural language.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Behavior Specification
              </label>
              <Textarea
                rows={6}
                value={behaviorPrompt}
                onChange={(e) => setBehaviorPrompt(e.target.value)}
                placeholder="Describe sampling cycles, sleep modes, threshold triggers, and commands..."
              />
            </div>
            <div className="rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-400 shrink-0" />
              <span>
                AI will parse thresholds and declare explicit command signatures (e.g. <code>TRIGGER_FAN_FORCE_ON</code>) in the spec behavior section.
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Interface Type */}
      {currentStep === 4 && (
        <Card>
          <CardHeader>
            <CardTitle>Interface Mode Selection</CardTitle>
            <CardDescription>
              Choose how users interact with this device. Can be converted later as a new version.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div
                onClick={() => setInterfaceType('dashboard')}
                className={`p-5 rounded-xl border cursor-pointer transition-all ${
                  interfaceType === 'dashboard'
                    ? 'border-primary bg-primary/5 ring-2 ring-primary'
                    : 'border-border hover:bg-muted/50'
                }`}
              >
                <div className="flex justify-between items-center mb-3">
                  <Activity className="h-6 w-6 text-primary" />
                  <Badge variant="defaulted">Monitoring Only</Badge>
                </div>
                <h4 className="font-bold text-base text-foreground">Dashboard</h4>
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                  Optimized for telemetry monitoring. Includes real-time sensor charts, threshold alert badges, and node connectivity health. Read-only.
                </p>
              </div>

              <div
                onClick={() => setInterfaceType('web app')}
                className={`p-5 rounded-xl border cursor-pointer transition-all ${
                  interfaceType === 'web app'
                    ? 'border-primary bg-primary/5 ring-2 ring-primary'
                    : 'border-border hover:bg-muted/50'
                }`}
              >
                <div className="flex justify-between items-center mb-3">
                  <Sliders className="h-6 w-6 text-primary" />
                  <Badge variant="confirmed">Monitoring + Controls</Badge>
                </div>
                <h4 className="font-bold text-base text-foreground">Full Web App</h4>
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                  Bundled web application with telemetry graphs plus interactive actuator controls strictly mapped to declared commands, role-based access, and user sign-in.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between items-center pt-2">
        {currentStep > 1 ? (
          <Button
            variant="outline"
            onClick={() => setCurrentStep((prev) => prev - 1)}
            disabled={submitting}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Previous</span>
          </Button>
        ) : (
          <div />
        )}

        {currentStep < 4 ? (
          <Button
            onClick={() => setCurrentStep((prev) => prev + 1)}
            className="gap-2"
          >
            <span>Next Step</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={submitting}
            className="gap-2 shadow-lg px-6"
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Synthesize Spec & Workspace</span>
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
