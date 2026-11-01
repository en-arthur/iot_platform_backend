import Link from 'next/link';
import { Cpu } from 'lucide-react';

export default function TermsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b py-4">
        <div className="container max-w-5xl px-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Cpu className="h-5 w-5 text-primary" />
            <span>AI IoT Builder</span>
          </Link>
        </div>
      </header>
      <main className="container max-w-4xl px-4 py-12 flex-1 space-y-6">
        <h1 className="text-3xl font-bold">Terms of Service</h1>
        <p className="text-muted-foreground text-sm">Last updated: November 1, 2026</p>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">1. Overview</h2>
          <p className="text-sm text-muted-foreground">
            AI IoT Builder provides hardware engineers with assisted specification, firmware synthesis, and cloud backend generation. By accessing our services, you agree to these Terms.
          </p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">2. Firmware Safety & Engineering Disclaimers</h2>
          <p className="text-sm text-muted-foreground">
            While AI IoT Builder enforces strict pinout and bus validation checks, all firmware must be independently reviewed and verified on physical hardware by a qualified engineer before deployment in safety-critical environments.
          </p>
        </section>
      </main>
    </div>
  );
}
