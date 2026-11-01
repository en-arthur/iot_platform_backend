import Link from 'next/link';
import {
  Cpu,
  Layers,
  ShieldCheck,
  Zap,
  Radio,
  FileCode2,
  CheckCircle2,
  Terminal,
  Activity,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  HelpCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/layout/ThemeToggle';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Sticky Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
          <Link href="/" className="flex items-center space-x-2.5 font-bold text-lg tracking-tight">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md">
              <Cpu className="h-5 w-5" />
            </div>
            <span>AI IoT Builder</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#hardware" className="hover:text-foreground transition-colors">Hardware</a>
          </nav>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/sign-in">
              <Button variant="ghost" size="sm">Sign In</Button>
            </Link>
            <Link href="/sign-up">
              <Button size="sm" className="shadow">Get Started Free</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-20 pb-16 md:pt-28 md:pb-24 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="grid gap-12 lg:grid-cols-12 lg:items-center">
              <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
                <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1 text-xs font-semibold text-primary">
                  <Zap className="h-3.5 w-3.5" />
                  <span>ESP32-S3 Hardware Emulation & Browser Flashing Live</span>
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl text-foreground">
                  From Hardware Description to a <span className="text-primary underline decoration-primary/40 underline-offset-8">Working Device</span> in Minutes.
                </h1>
                <p className="text-lg text-muted-foreground sm:text-xl max-w-2xl mx-auto lg:mx-0">
                  Hardware engineers describe their IoT device in plain language. AI proposes a verified project spec. You review, approve, and get production C++ firmware, cloud FastAPI backend, and web app verified on real silicon.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start pt-2">
                  <Link href="/sign-up">
                    <Button size="lg" className="w-full sm:w-auto gap-2 text-base px-7">
                      Start Building Free
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Link href="/app/projects/proj-greenhouse-01">
                    <Button variant="outline" size="lg" className="w-full sm:w-auto text-base">
                      Explore Greenhouse Demo
                    </Button>
                  </Link>
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  No credit card required • Strict contract validation • Single source-of-truth spec
                </p>
              </div>

              {/* Product Visual / Spec Architecture Card */}
              <div className="lg:col-span-5">
                <div className="rounded-2xl border border-border bg-card/80 p-5 shadow-2xl backdrop-blur relative overflow-hidden">
                  <div className="flex items-center justify-between pb-3 border-b border-border/60">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-red-500/80 inline-block" />
                      <span className="h-3 w-3 rounded-full bg-amber-500/80 inline-block" />
                      <span className="h-3 w-3 rounded-full bg-emerald-500/80 inline-block" />
                      <span className="text-xs font-mono text-muted-foreground ml-2">spec_v1.0.json</span>
                    </div>
                    <Badge variant="confirmed">Confirmed</Badge>
                  </div>
                  <div className="mt-4 space-y-3 font-mono text-xs text-slate-300 bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-emerald-400 font-semibold">// 1. Hardware Definition</div>
                    <div>&quot;mcu&quot;: <span className="text-amber-300">&quot;ESP32-S3 240MHz&quot;</span>,</div>
                    <div>&quot;bus&quot;: <span className="text-sky-300">&quot;I2C (SDA: GPIO4, SCL: GPIO5)&quot;</span>,</div>
                    <div className="text-purple-400 font-semibold mt-3">// 2. Behavioral Rule</div>
                    <div>&quot;threshold&quot;: <span className="text-amber-300">&quot;temperature &gt; 30.0°C&quot;</span>,</div>
                    <div>&quot;action&quot;: <span className="text-emerald-300">&quot;TRIGGER_FAN_FORCE_ON&quot;</span>,</div>
                    <div className="text-sky-400 font-semibold mt-3">// 3. Target Output Bundle</div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      <span>ESP-IDF C++ Firmware (Dual OTA)</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      <span>FastAPI Telemetry Ingestion</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Web App Control Center</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Problem Statement */}
        <section className="py-20 bg-muted/30 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Why IoT Development Is Still Painful
            </h2>
            <p className="mt-4 text-base text-muted-foreground max-w-2xl mx-auto">
              Building connected hardware usually means juggling mismatched pinouts, writing tedious driver glue code, and building fragmented cloud APIs from scratch.
            </p>
            <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 text-left">
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <div className="h-10 w-10 rounded-lg bg-destructive/10 text-destructive flex items-center justify-center font-bold mb-4">
                  !
                </div>
                <h3 className="text-lg font-semibold text-foreground">Pin Collisions & Bus Lockups</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Assigning a shared GPIO to both an I2C line and a switch bricks your prototype during field deployment.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <div className="h-10 w-10 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold mb-4">
                  ⚙
                </div>
                <h3 className="text-lg font-semibold text-foreground">Backend & Firmware Desync</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Changing a sensor metric unit or payload schema breaks cloud ingestion parsers and dashboards silently.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold mb-4">
                  🔒
                </div>
                <h3 className="text-lg font-semibold text-foreground">Unverified AI Hallucinations</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Generic LLMs generate code for hardware registers that don&apos;t exist. We enforce strict schema rules and real compilation.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works: 4 Steps */}
        <section id="how-it-works" className="py-20 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="text-center max-w-3xl mx-auto">
              <Badge variant="default">The Engineering Process</Badge>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                How It Works in 4 Steps
              </h2>
              <p className="mt-3 text-muted-foreground">
                The single project spec is your source of truth. AI proposes changes; you confirm; nothing generates without your sign-off.
              </p>
            </div>

            <div className="mt-14 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              <div className="relative rounded-xl border border-border bg-card p-6 shadow-sm">
                <span className="text-3xl font-black text-primary/30">01</span>
                <h3 className="mt-2 text-lg font-semibold text-foreground">Describe Device</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  State your sensors, behavior, thresholds, and target interface in plain language.
                </p>
              </div>

              <div className="relative rounded-xl border border-border bg-card p-6 shadow-sm">
                <span className="text-3xl font-black text-primary/30">02</span>
                <h3 className="mt-2 text-lg font-semibold text-foreground">Review & Confirm Spec</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Examine the 12-section model. Pin conflicts and open fields are resolved before generation is unlocked.
                </p>
              </div>

              <div className="relative rounded-xl border border-border bg-card p-6 shadow-sm">
                <span className="text-3xl font-black text-primary/30">03</span>
                <h3 className="mt-2 text-lg font-semibold text-foreground">Generate & Verify</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Stream C++ firmware and FastAPI backend generation. Pipeline validates compilation, emulation, and self-tests.
                </p>
              </div>

              <div className="relative rounded-xl border border-border bg-card p-6 shadow-sm">
                <span className="text-3xl font-black text-primary/30">04</span>
                <h3 className="mt-2 text-lg font-semibold text-foreground">Flash & Deploy</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Plug in your real ESP32 board and flash over Web Serial directly from Chrome. Provision and monitor live.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Key Features */}
        <section id="features" className="py-20 bg-muted/20 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Built for Hardware & Systems Engineers
              </h2>
              <p className="mt-3 text-muted-foreground">
                Every feature respects the physical reality of embedded systems and silicon constraints.
              </p>
            </div>

            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-border bg-card p-6">
                <Layers className="h-6 w-6 text-primary mb-3" />
                <h3 className="font-semibold text-base text-foreground">One Source-of-Truth Spec</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  12 structured sections cover metadata, peripherals, MQTT connectivity, security, OTA rollback, and provenance.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6">
                <Cpu className="h-6 w-6 text-primary mb-3" />
                <h3 className="font-semibold text-base text-foreground">Verified Hardware Library</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Pre-validated pinouts, I2C addresses, and timing characteristics for popular MCUs and sensors.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6">
                <Activity className="h-6 w-6 text-primary mb-3" />
                <h3 className="font-semibold text-base text-foreground">Build & Test on Real Silicon</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Automated test suites run against virtual QEMU emulators and submit physical on-device self-test reports.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6">
                <Terminal className="h-6 w-6 text-primary mb-3" />
                <h3 className="font-semibold text-base text-foreground">Dashboard or Full Web App</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Choose between pure telemetry monitoring or an interactive Web App with RBAC and authorized device commands.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6">
                <ShieldCheck className="h-6 w-6 text-primary mb-3" />
                <h3 className="font-semibold text-base text-foreground">Secure by Default</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Mutual TLS 1.3, ECDSA P-256 certificates, AES flash encryption, and one-time provisioned device secrets.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6">
                <Radio className="h-6 w-6 text-primary mb-3" />
                <h3 className="font-semibold text-base text-foreground">Dual-Partition OTA Rollback</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Over-the-air firmware upgrades automatically revert to partition A if on-boot self-tests fail.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Trust Section for Engineers */}
        <section className="py-20 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="rounded-2xl border border-primary/20 bg-primary/5 p-8 sm:p-12">
              <div className="max-w-3xl">
                <Badge variant="default">Engineering Transparency</Badge>
                <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                  Inspect Every Line. Edit Protected Regions. Trust Build Logs.
                </h2>
                <p className="mt-4 text-muted-foreground leading-relaxed">
                  We never lock you into a proprietary black box. You have full access to generated C++ firmware, Python FastAPI servers, and React interface files in the embedded Monaco editor. Insert your own custom calibration code inside protected regions—AI updates will never overwrite your manual edits.
                </p>
                <div className="mt-8 flex flex-wrap gap-4">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <span>Protected Code Annotations</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <span>Raw Streaming Compiler Logs</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <span>Side-by-Side Version Diffing</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Supported Hardware */}
        <section id="hardware" className="py-20 bg-muted/20 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-12">
              <div>
                <h2 className="text-3xl font-bold tracking-tight text-foreground">Supported Hardware</h2>
                <p className="mt-2 text-muted-foreground">Verified pinouts and toolchain recipes ready out-of-the-box.</p>
              </div>
              <a
                href="mailto:hardware@iotbuilder.dev?subject=Request%20Board%20Support"
                className="mt-4 md:mt-0 text-sm font-medium text-primary hover:underline inline-flex items-center gap-1"
              >
                Request a board <ChevronRight className="h-4 w-4" />
              </a>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-foreground">ESP32-S3 DevKitC-1</h3>
                  <Badge variant="confirmed">Tested</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  Xtensa dual-core 240MHz, 8MB Flash, 2MB PSRAM, Wi-Fi 4 + BLE 5.0, Native USB OTG.
                </p>
                <div className="text-xs font-mono bg-muted p-2.5 rounded">
                  Status: Full Web Serial Flashing + HIL QEMU Simulation
                </div>
              </div>

              <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-foreground">Raspberry Pi Pico W</h3>
                  <Badge variant="defaulted">Draft</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  RP2040 Dual ARM Cortex-M0+, CYW43439 802.11n wireless, UF2 bootloader.
                </p>
                <div className="text-xs font-mono bg-muted p-2.5 rounded">
                  Status: Pinout mapped, UF2 binary export available
                </div>
              </div>

              <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-foreground">STM32 Nucleo-L476RG</h3>
                  <Badge variant="open">Unverified</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  ARM Cortex-M4 @ 80 MHz, 1MB Flash, ultra-low power modes.
                </p>
                <div className="text-xs font-mono bg-muted p-2.5 rounded">
                  Status: Community schema in review
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 bg-muted/20 border-b border-border/40">
          <div className="container max-w-4xl px-4 sm:px-8">
            <h2 className="text-3xl font-bold tracking-tight text-foreground text-center">Frequently Asked Questions</h2>
            <div className="mt-10 space-y-4">
              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  What is the difference between a Dashboard and a Web App?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  A <strong>Dashboard</strong> is read-only telemetry monitoring (charts, tiles, alert thresholds). A <strong>Web App</strong> bundles full user authentication, role-based controls, and interactive command dispatch that triggers physical actuators according to the behavior section.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  Does AI directly write code to my MCU without my consent?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Never. AI only produces <strong>Spec Proposals</strong> with an explicit breakdown of old vs new values. You must review and click <strong>Approve</strong>. Spec confirmation is blocked if any electrical or completeness errors exist.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  Can I flash boards directly from the web browser?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Yes! We use the Web Serial API combined with <code>esptool-js</code>. Connect your ESP32-S3 over standard USB-C in Chrome, Edge, or Opera, and flash compiled firmware binaries in seconds.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 text-center">
          <div className="container max-w-4xl px-4 sm:px-8">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Ready to Build Your Next Connected Device?
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Describe your device, confirm the spec, and flash real hardware today.
            </p>
            <div className="mt-8 flex justify-center gap-4">
              <Link href="/sign-up">
                <Button size="lg" className="px-8 shadow-lg">Get Started Free</Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 text-sm text-muted-foreground">
        <div className="container max-w-7xl px-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Cpu className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">AI IoT Builder</span>
            <span>&copy; {new Date().getFullYear()} All rights reserved.</span>
          </div>
          <div className="flex gap-6">
            <Link href="/terms" className="hover:text-foreground">Terms of Service</Link>
            <Link href="/privacy" className="hover:text-foreground">Privacy Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
