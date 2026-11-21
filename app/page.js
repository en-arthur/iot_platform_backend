'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
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
  ChevronRight,
  HelpCircle,
  AlertTriangle,
  RefreshCw,
  Lock,
  Sliders,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/layout/ThemeToggle';

const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      delay: i * 0.1,
      ease: [0.25, 0.4, 0.25, 1],
    },
  }),
};

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col overflow-x-hidden">
      {/* Sticky Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
          <Link href="/" className="flex items-center space-x-2.5 font-bold text-lg tracking-tight">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md">
              <Cpu className="h-5 w-5" />
            </div>
            <span>DeviceStack</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
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
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeInUp}
                custom={0}
                className="lg:col-span-7 space-y-6 text-center lg:text-left"
              >
                <motion.h1
                  variants={fadeInUp}
                  custom={1}
                  className="text-4xl font-extrabold tracking-tighter sm:text-5xl lg:text-6xl text-foreground font-heading"
                >
                  From Hardware Description to a <span className="text-primary underline decoration-primary/40 underline-offset-8">Working Device</span> in Minutes.
                </motion.h1>

                <motion.p
                  variants={fadeInUp}
                  custom={2}
                  className="text-lg text-muted-foreground sm:text-xl max-w-2xl mx-auto lg:mx-0 leading-relaxed"
                >
                  Describe what your device does in simple words. We turn your requirements into ready-to-run device code, a cloud backend, and a web dashboard—no coding needed.
                </motion.p>

                <motion.div
                  variants={fadeInUp}
                  custom={3}
                  className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start pt-2"
                >
                  <Link href="/sign-up">
                    <Button size="lg" className="w-full sm:w-auto gap-2 text-base px-7 shadow-lg hover:shadow-primary/20 transition-all">
                      Create Your Device
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Link href="/sign-in">
                    <Button variant="outline" size="lg" className="w-full sm:w-auto text-base hover:bg-muted/80">
                      Sign In
                    </Button>
                  </Link>
                </motion.div>

                <motion.p variants={fadeInUp} custom={4} className="text-xs text-muted-foreground pt-1">
                  Free to start • No credit card required • Works with hardware you already own
                </motion.p>
              </motion.div>

              {/* Application Demo Visual */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }}
                className="lg:col-span-5"
              >
                <div className="rounded-2xl border border-border bg-gradient-to-br from-card/95 to-card/80 p-6 shadow-2xl backdrop-blur relative overflow-hidden group hover:border-primary/40 transition-all">
                  {/* Demo Header */}
                  <div className="flex items-center justify-between pb-4 border-b border-border/60">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Activity className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-foreground">Smart Greenhouse Monitor</h3>
                        <p className="text-xs text-muted-foreground">Live Dashboard</p>
                      </div>
                    </div>
                    <Badge variant="confirmed" className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                      Online
                    </Badge>
                  </div>

                  {/* Telemetry Cards */}
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <div className="rounded-lg border border-border/60 bg-background/60 p-3">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Temperature</div>
                      <div className="text-2xl font-bold text-foreground">28.4°C</div>
                      <div className="text-[10px] text-emerald-600 mt-0.5">Normal range</div>
                    </div>
                    <div className="rounded-lg border border-border/60 bg-background/60 p-3">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Humidity</div>
                      <div className="text-2xl font-bold text-foreground">62%</div>
                      <div className="text-[10px] text-sky-600 mt-0.5">Optimal</div>
                    </div>
                    <div className="rounded-lg border border-border/60 bg-background/60 p-3">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Soil Moisture</div>
                      <div className="text-2xl font-bold text-foreground">45%</div>
                      <div className="text-[10px] text-amber-600 mt-0.5">Water soon</div>
                    </div>
                    <div className="rounded-lg border border-border/60 bg-background/60 p-3">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Light Level</div>
                      <div className="text-2xl font-bold text-foreground">850 lx</div>
                      <div className="text-[10px] text-emerald-600 mt-0.5">Adequate</div>
                    </div>
                  </div>

                  {/* Controls */}
                  <div className="mt-5 space-y-2">
                    <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Quick Actions</div>
                    <div className="flex gap-2">
                      <button className="flex-1 rounded-lg border border-border/60 bg-background/60 px-3 py-2 text-xs font-medium hover:bg-primary/10 hover:border-primary/40 transition-colors">
                        💧 Water Now
                      </button>
                      <button className="flex-1 rounded-lg border border-border/60 bg-background/60 px-3 py-2 text-xs font-medium hover:bg-primary/10 hover:border-primary/40 transition-colors">
                        🌡️ Set Alert
                      </button>
                    </div>
                  </div>

                  {/* Footer Status */}
                  <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                      Last sync: 2 seconds ago
                    </span>
                    <span>Device ID: GH-001</span>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Problem Statement */}
        <section className="py-20 bg-muted/30 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8 text-center">
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-50px' }}
              variants={fadeInUp}
            >
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Building Connected Devices Shouldn&apos;t Be This Hard
              </h2>
              <p className="mt-4 text-base text-muted-foreground max-w-2xl mx-auto">
                Most smart device projects fail before launch. Wrong pins, mismatched code, broken cloud connections—we handle all of that for you.
              </p>
            </motion.div>

            <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 text-left">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.1 }}
                whileHover={{ y: -6 }}
                className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-destructive/40 transition-all"
              >
                <div className="h-10 w-10 rounded-lg bg-destructive/10 flex items-center justify-center mb-4">
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">Wrong Pin = Broken Device</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  Connect the wrong pin and your device won&apos;t work. We make sure every connection is correct before you build anything.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.2 }}
                whileHover={{ y: -6 }}
                className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-amber-500/40 transition-all"
              >
                <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center mb-4">
                  <RefreshCw className="h-5 w-5 text-amber-500" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">Cloud & Device Out of Sync</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  Change your sensor? Your dashboard breaks. We keep your device code and cloud dashboard perfectly in sync, automatically.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.3 }}
                whileHover={{ y: -6 }}
                className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-primary/40 transition-all"
              >
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <Lock className="h-5 w-5 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">Security Is an Afterthought</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  Most DIY projects have zero security. We build in encryption, secure connections, and safe updates from day one.
                </p>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Key Features */}
        <section id="features" className="py-20 bg-muted/20 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Everything You Need to Launch Your Device
              </h2>
              <p className="mt-3 text-muted-foreground">
                From idea to working product. We handle the technical details so you can focus on what matters.
              </p>
            </div>

            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: Layers,
                  title: 'One Master Plan for Everything',
                  desc: 'Your project specs, sensors, commands, and security settings all live in one place. Change something once, everything updates.',
                },
                {
                  icon: Cpu,
                  title: 'Works with Real Hardware',
                  desc: 'Pre-tested with popular boards you can buy today. No guessing which pins to use or why things don&apos;t work.',
                },
                {
                  icon: Activity,
                  title: 'Test Before You Build',
                  desc: 'Verify your device code compiles correctly before flashing. Catch errors early, save time.',
                },
                {
                  icon: Terminal,
                  title: 'Dashboard or Full Control Panel',
                  desc: 'Choose simple monitoring dashboards or full web apps where users can send commands to physical devices.',
                },
                {
                  icon: ShieldCheck,
                  title: 'Secure by Default',
                  desc: 'Built-in encryption, secure connections, and one-time device passwords. No security expertise needed.',
                },
                {
                  icon: Radio,
                  title: 'Safe Firmware Updates',
                  desc: 'Update your devices over Wi-Fi. If something goes wrong, they automatically roll back to the working version.',
                },
              ].map((feat, i) => {
                const Icon = feat.icon;
                return (
                  <motion.div
                    key={feat.title}
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: i * 0.08 }}
                    whileHover={{ y: -4 }}
                    className="rounded-xl border border-border bg-card p-6 hover:border-primary/40 transition-all shadow-sm"
                  >
                    <Icon className="h-6 w-6 text-primary mb-3" />
                    <h3 className="font-semibold text-base text-foreground">{feat.title}</h3>
                    <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{feat.desc}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Supported Hardware */}
        <section id="hardware" className="py-20 bg-muted/20 border-b border-border/40">
          <div className="container max-w-7xl px-4 sm:px-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-12">
              <div>
                <h2 className="text-3xl font-bold tracking-tight text-foreground">Compatible Hardware</h2>
                <p className="mt-2 text-muted-foreground">Works with boards you can buy today. Plug in and start building.</p>
              </div>
              <a
                href="mailto:support@devicestack.io?subject=Request%20Board%20Support"
                className="mt-4 md:mt-0 text-sm font-medium text-primary hover:underline inline-flex items-center gap-1"
              >
                Need a different board? <ChevronRight className="h-4 w-4" />
              </a>
            </div>

            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {/* ESP32-S3 DevKitC-1 */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                whileHover={{ y: -4 }}
                className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-foreground">ESP32-S3 DevKitC-1</h3>
                  <Badge variant="confirmed">Tested</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Dual-core 240MHz, 8MB Flash, Wi-Fi + BLE, Native USB. Flash directly from your browser.
                </p>
                <div className="text-[10px] font-mono bg-muted px-2 py-1.5 rounded">
                  Espressif • ~$8 USD
                </div>
              </motion.div>

              {/* ESP32 DevKit V1 */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.05 }}
                whileHover={{ y: -4 }}
                className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-foreground">ESP32 DevKit V1</h3>
                  <Badge variant="confirmed">Tested</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Classic ESP32, 240MHz dual-core, 4MB Flash, Wi-Fi + Bluetooth. Most common budget board.
                </p>
                <div className="text-[10px] font-mono bg-muted px-2 py-1.5 rounded">
                  DOIT / Espressif • ~$5 USD
                </div>
              </motion.div>

              {/* ESP32-C3 */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                whileHover={{ y: -4 }}
                className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-foreground">ESP32-C3 SuperMini</h3>
                  <Badge variant="confirmed">Tested</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  RISC-V 160MHz, 4MB Flash, Wi-Fi + BLE 5.0. Ultra compact form factor for space-constrained projects.
                </p>
                <div className="text-[10px] font-mono bg-muted px-2 py-1.5 rounded">
                  Espressif • ~$3 USD
                </div>
              </motion.div>

              {/* NodeMCU */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.15 }}
                whileHover={{ y: -4 }}
                className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-foreground">NodeMCU ESP8266</h3>
                  <Badge variant="confirmed">Tested</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  ESP8266 80MHz, 4MB Flash, Wi-Fi 2.4GHz. Popular for simple IoT projects and learning.
                </p>
                <div className="text-[10px] font-mono bg-muted px-2 py-1.5 rounded">
                  NodeMCU • ~$4 USD
                </div>
              </motion.div>

              {/* Raspberry Pi Pico W */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                whileHover={{ y: -4 }}
                className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-foreground">Raspberry Pi Pico W</h3>
                  <Badge variant="defaulted">Coming Soon</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  RP2040 dual ARM Cortex-M0+, 2MB Flash, Wi-Fi. Drag-and-drop UF2 flashing.
                </p>
                <div className="text-[10px] font-mono bg-muted px-2 py-1.5 rounded">
                  Raspberry Pi • ~$6 USD
                </div>
              </motion.div>

              {/* More Coming */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.25 }}
                className="rounded-xl border border-dashed border-border bg-muted/20 p-5 flex flex-col items-center justify-center text-center"
              >
                <Cpu className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm font-medium text-foreground">30+ More Boards</p>
                <p className="text-xs text-muted-foreground mt-1">
                  ESP32-S2, ESP32-C6, WEMOS D1 Mini, and more ESP32/ESP8266 variants supported
                </p>
              </motion.div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 bg-muted/20 border-b border-border/40">
          <div className="container max-w-4xl px-4 sm:px-8">
            <h2 className="text-3xl font-bold tracking-tight text-foreground text-center">Common Questions</h2>
            <div className="mt-10 space-y-4">
              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  Do I need to know how to code?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  No. Describe what you want your device to do in plain English, and we generate all the code automatically. You can review it if you want, or just flash it to your device.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  What&apos;s the difference between a Dashboard and a Web App?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  A <strong>Dashboard</strong> shows your device data (charts, numbers, alerts). A <strong>Web App</strong> lets you control your device remotely—turn things on/off, change settings, and more.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  Can I flash my board directly from the browser?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  Yes! For ESP32-S3 boards, just plug in your device via USB, click Flash, and you&apos;re done. No software to install. Works in Chrome, Edge, and Opera.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-primary" />
                  Is my data secure?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  Yes. All connections between your devices and the cloud are encrypted. Each device gets a unique password that only you see once. We follow industry security standards.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 text-center">
          <div className="container max-w-4xl px-4 sm:px-8">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Ready to Bring Your Idea to Life?
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Start building your smart device today. No coding required, no credit card needed.
            </p>
            <div className="mt-8 flex justify-center gap-4">
              <Link href="/sign-up">
                <Button size="lg" className="px-8 shadow-lg">Create Your Device Free</Button>
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
            <span className="font-semibold text-foreground">DeviceStack Technologies</span>
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
