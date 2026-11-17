'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { MOCK_BOARDS, MOCK_PERIPHERALS } from '@/lib/api/mocks';
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
  Plus,
  RefreshCw,
} from 'lucide-react';

const STEPS = [
  { id: 1, title: 'Name & Goal' },
  { id: 2, title: 'Hardware & Sensors' },
  { id: 3, title: 'How It Works' },
  { id: 4, title: 'Controls' },
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
  const [behaviorPrompt, setBehaviorPrompt] = useState('');
  const [behaviorLoading, setBehaviorLoading] = useState(false);
  const [behaviorSource, setBehaviorSource] = useState(null); // 'ai' | 'template' | 'error'
  const behaviorDirtyRef = useRef(false);
  const [interfaceType, setInterfaceType] = useState('web app'); // 'dashboard' | 'web app'
  const [isCustomPeripheralSelected, setIsCustomPeripheralSelected] = useState(false);
  const [customPeripheralsText, setCustomPeripheralsText] = useState('');

  // Library Data
  const [boards, setBoards] = useState([]);
  const [peripherals, setPeripherals] = useState([]);
  const [libraryError, setLibraryError] = useState(false);

  const rankBoards = (list) => {
    // Verified boards first, then by name, so the picker leads with the
    // targets that have a pin map and a working build recipe.
    const rank = { tested: 0, unverified: 1, draft: 2, deprecated: 3 };
    return [...(list || [])].sort(
      (x, y) =>
        (rank[x.status] ?? 9) - (rank[y.status] ?? 9) ||
        x.name.localeCompare(y.name)
    );
  };

  const loadLibrary = async () => {
    setLibraryError(false);
    try {
      const [b, p] = await Promise.all([api.getBoards(), api.getPeripherals()]);
      const sorted = rankBoards(b);
      setBoards(sorted);
      setPeripherals(p);
      setSelectedBoard((current) =>
        sorted.some((board) => board.id === current)
          ? current
          : sorted[0]?.id || current
      );
    } catch {
      // Never leave the picker blank: fall back to the bundled library and
      // tell the user the server could not be reached.
      const sorted = rankBoards(MOCK_BOARDS);
      setBoards(sorted);
      setPeripherals(MOCK_PERIPHERALS);
      setLibraryError(true);
      setSelectedBoard((current) =>
        sorted.some((board) => board.id === current)
          ? current
          : sorted[0]?.id || current
      );
    }
  };

  useEffect(() => {
    loadLibrary();
  }, []);

  const togglePeripheral = (id) => {
    setSelectedPeripherals((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const getCustomPeripherals = () =>
    isCustomPeripheralSelected && customPeripheralsText.trim()
      ? customPeripheralsText.split(',').map((s) => s.trim()).filter(Boolean)
      : [];

  const getSelectedPeripheralNames = () => {
    const names = peripherals
      .filter((p) => selectedPeripherals.includes(p.id))
      .map((p) => p.name);
    return names.length > 0 ? names : selectedPeripherals;
  };

  // Draft the behavior spec from the Step 1 goal + Step 2 hardware.
  const generateBehavior = async () => {
    if (behaviorLoading) return;

    setBehaviorLoading(true);
    try {
      const draft = await api.generateBehaviorDraft({
        name: name || 'Untitled IoT device',
        goal,
        board_id: selectedBoard,
        peripherals: getSelectedPeripheralNames(),
        custom_peripherals: getCustomPeripherals(),
        interface_type: interfaceType,
      });
      setBehaviorPrompt(draft?.behavior || '');
      setBehaviorSource(draft?.source === 'ai' ? 'ai' : 'template');
    } catch (err) {
      setBehaviorSource('error');
    } finally {
      setBehaviorLoading(false);
    }
  };

  // Auto-generate on entering the Behavior step. User edits are preserved when
  // they navigate back and forth; Regenerate overrides them.
  useEffect(() => {
    if (currentStep !== 3 || behaviorDirtyRef.current) return;
    generateBehavior();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentStep]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const customList = getCustomPeripherals();

      const peripheralsNote = customList.length > 0
        ? ` Additional custom components: ${customList.join(', ')}.`
        : '';

      const description = [
        goal.trim(),
        behaviorPrompt.trim() ? `Behavior Specification:\n${behaviorPrompt.trim()}` : '',
      ].filter(Boolean).join('\n\n') + peripheralsNote;

      const project = await api.createProject({
        name: name || 'Smart Greenhouse Node',
        description,
        board_id: selectedBoard,
        interface_type: interfaceType,
        custom_peripherals: customList,
      });

      // Synthesize firmware, cloud backend and interface so the workspace opens
      // with real code instead of an empty placeholder.
      try {
        await api.generateProjectCode(project.id);
      } catch (genErr) {
        console.warn('Code generation failed:', genErr.message);
      }

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
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Start a New Project</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Tell us what you want to build in your own words. We will turn it into a plan you can review.
        </p>
      </div>

      <div className="flex items-center justify-between border-b border-border pb-4">
        {STEPS.map((s, idx) => (
          <div key={s.id} className="flex items-center gap-2">
            <button
              type="button"
              disabled={behaviorLoading}
              onClick={() => setCurrentStep(s.id)}
              className="flex items-center gap-2 group cursor-pointer focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            >
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                  currentStep === s.id
                    ? 'bg-primary text-primary-foreground ring-2 ring-primary/30'
                    : currentStep > s.id
                    ? 'bg-emerald-500/20 text-emerald-500'
                    : 'bg-muted text-muted-foreground group-hover:bg-muted/80'
                }`}
              >
                {currentStep > s.id ? <CheckCircle2 className="h-4 w-4" /> : s.id}
              </div>
              <span
                className={`text-xs font-medium hidden sm:inline transition-colors ${
                  currentStep === s.id ? 'text-foreground font-semibold' : 'text-muted-foreground group-hover:text-foreground'
                }`}
              >
                {s.title}
              </span>
            </button>
            {idx < STEPS.length - 1 && <span className="text-border mx-2 hidden sm:inline select-none">—</span>}
          </div>
        ))}
      </div>

      {/* Step 1: Name and Goal */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Name Your Project</CardTitle>
            <CardDescription>
              Give the device a name and say what it should do and where it will live.
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
                What Should It Do?
              </label>
              <Textarea
                rows={4}
                placeholder="e.g. A battery-powered sensor in a greenhouse that reports temperature and humidity, and turns on a fan when it gets too hot."
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
            <CardTitle>Choose Your Hardware</CardTitle>
            <CardDescription>
              Pick the board you will use, then add the sensors or parts you will connect to it.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-3">
                Your Board
              </label>
              {libraryError && (
                <div className="mb-3 flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-400">
                  <span>We could not reach the server, so this is the built-in board list.</span>
                  <button
                    type="button"
                    onClick={loadLibrary}
                    className="inline-flex items-center gap-1 font-semibold underline"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Try again
                  </button>
                </div>
              )}
              {boards.length === 0 && !libraryError && (
                <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Loading boards…
                </div>
              )}
              <div className="grid gap-3 sm:grid-cols-3">
                {boards.map((b) => {
                  const flash = b.specs?.flash_mb;
                  const psram = b.specs?.psram_mb || 0;
                  const pinCount = b.pin_map ? Object.keys(b.pin_map).length : 0;
                  const connectivityLabel = {
                    wifi: 'Wi-Fi',
                    ethernet: 'Ethernet',
                    ble: 'BLE only',
                    none: 'No network',
                  }[b.connectivity];
                  const otaLimited = typeof flash === 'number' && flash < 4;

                  return (
                    <div
                      key={b.id}
                      role="button"
                      tabIndex={0}
                      aria-pressed={selectedBoard === b.id}
                      onClick={() => setSelectedBoard(b.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelectedBoard(b.id);
                        }
                      }}
                      className={`p-4 rounded-xl border cursor-pointer transition-all focus:outline-none focus:ring-2 focus:ring-primary ${
                        selectedBoard === b.id
                          ? 'border-primary bg-primary/5 ring-1 ring-primary'
                          : 'border-border hover:bg-muted/50'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <Cpu className="h-5 w-5 text-primary" />
                        <div className="flex items-center gap-1.5">
                          {selectedBoard === b.id && (
                            <CheckCircle2 className="h-4 w-4 text-primary" />
                          )}
                          <Badge variant={b.status === 'tested' ? 'confirmed' : b.status === 'draft' ? 'defaulted' : 'open'}>
                            {b.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="font-semibold text-sm text-foreground">{b.name}</div>
                      <div className="text-xs text-muted-foreground mt-1">{b.mcu}</div>
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {connectivityLabel && (
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            {connectivityLabel}
                          </span>
                        )}
                        {typeof flash === 'number' && (
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            {flash} MB flash
                          </span>
                        )}
                        {psram > 0 && (
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            +{psram} MB PSRAM
                          </span>
                        )}
                        {pinCount > 0 && (
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            {pinCount} pins mapped
                          </span>
                        )}
                      </div>
                      {otaLimited && (
                        <div className="text-[10px] text-amber-600 dark:text-amber-500 mt-2">
                          OTA needs 4 MB flash; this board is OTA-limited.
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-3">
                Sensors & Parts
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

                {/* Other / Custom Hardware Component Option */}
                <div
                  onClick={() => setIsCustomPeripheralSelected(!isCustomPeripheralSelected)}
                  className={`p-3.5 rounded-xl border cursor-pointer flex items-start gap-3 transition-all ${
                    isCustomPeripheralSelected
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-dashed border-border hover:bg-muted/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isCustomPeripheralSelected}
                    onChange={() => {}}
                    className="mt-1"
                  />
                  <div className="text-xs space-y-1">
                    <div className="font-semibold text-foreground flex items-center gap-2">
                      <span>Other Component</span>
                      <span className="text-[10px] text-primary bg-primary/10 px-1.5 py-0.5 rounded font-mono font-medium">
                        Custom
                      </span>
                    </div>
                    <p className="text-muted-foreground">Type your own custom sensor, module, or actuator.</p>
                  </div>
                </div>
              </div>

              {/* Input field when "Other" is selected */}
              {isCustomPeripheralSelected && (
                <div className="mt-3.5 p-4 rounded-xl border border-primary/30 bg-primary/5 space-y-2 animate-in fade-in">
                  <div className="flex items-center gap-2">
                    <Plus className="h-4 w-4 text-primary" />
                    <label htmlFor="custom-peripherals-input" className="text-xs font-semibold text-foreground">
                      Add Another Part
                    </label>
                  </div>
                  <Input
                    id="custom-peripherals-input"
                    placeholder="e.g. Capacitive Soil Moisture Sensor v2, Neo-6M GPS, WS2812B RGB LED, Active Buzzer..."
                    value={customPeripheralsText}
                    onChange={(e) => setCustomPeripheralsText(e.target.value)}
                    className="bg-background text-xs"
                    autoFocus
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Type the parts you have, separated by commas. We will work out how to wire them up.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Behavior */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>How It Should Behave</CardTitle>
            <CardDescription>
              In your own words: how often it checks its sensors, when it turns things on, and how it saves power.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label
                  htmlFor="behavior-spec"
                  className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  How It Should Work
                </label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    behaviorDirtyRef.current = false;
                    generateBehavior();
                  }}
                  disabled={behaviorLoading}
                  className="gap-2"
                >
                  {behaviorLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3.5 w-3.5" />
                  )}
                  <span>{behaviorLoading ? 'Generating...' : 'Regenerate'}</span>
                </Button>
              </div>
              <Textarea
                id="behavior-spec"
                rows={9}
                value={behaviorPrompt}
                disabled={behaviorLoading}
                onChange={(e) => {
                  behaviorDirtyRef.current = true;
                  setBehaviorPrompt(e.target.value);
                  if (behaviorSource === 'error') setBehaviorSource(null);
                }}
                placeholder={
                  behaviorLoading
                    ? 'Writing a first draft from your goal and parts...'
                    : 'For example: check the sensor every 30 seconds, turn the fan on above 30 degrees, and send a reading every 5 minutes.'
                }
              />
              <p className="text-[11px] text-muted-foreground">
                {behaviorSource === 'ai' &&
                  'Drafted by AI from your Step 1 goal and Step 2 hardware. Edit anything you want before submitting.'}
                {behaviorSource === 'template' &&
                  'Draft generated from your goal and hardware (AI unavailable). Edit it freely before submitting.'}
                {behaviorSource === 'error' &&
                  'Automatic draft failed. Write the behavior yourself or press Regenerate.'}
                {!behaviorSource &&
                  !behaviorLoading &&
                  'AI drafts this from your Step 1 goal and Step 2 hardware. Every word stays editable.'}
                {behaviorLoading &&
                  'Reading your goal and hardware to draft the behavior rules...'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Interface Type */}
      {currentStep === 4 && (
        <Card>
          <CardHeader>
            <CardTitle>How You Will Control It</CardTitle>
            <CardDescription>
              Pick the screen you want for this device. You can change it later.
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
                  See what your device is measuring. Live charts, alerts when a value goes out of range, and a health check for each device. No buttons to press.
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
                  Same live charts, plus buttons to switch things on and off. Sign-in keeps the controls private to you.
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
            disabled={behaviorLoading}
            className="gap-2"
            title={behaviorLoading ? 'Waiting for the behavior draft to finish' : undefined}
          >
            <span>Next Step</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={submitting || behaviorLoading}
            className="gap-2 shadow-lg px-6"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Generating code...</span>
              </>
            ) : (
              <span>Submit</span>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
