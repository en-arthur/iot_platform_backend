import Link from 'next/link';
import { Cpu } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b py-4">
        <div className="container max-w-5xl px-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Cpu className="h-5 w-5 text-primary" />
            <span>DeviceStack</span>
          </Link>
        </div>
      </header>
      <main className="container max-w-4xl px-4 py-12 flex-1 space-y-6">
        <h1 className="text-3xl font-bold">Privacy Policy</h1>
        <p className="text-muted-foreground text-sm">Last updated: November 1, 2026</p>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">1. Data Collection & Direct Reads</h2>
          <p className="text-sm text-muted-foreground">
            We store device specifications, telemetry schemas, and generation logs in Supabase. Your project data is protected by strict Row-Level Security (RLS) policies.
          </p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">2. Hardware Credentials</h2>
          <p className="text-sm text-muted-foreground">
            Device secrets and MQTT credentials generated during provisioning are returned exactly ONCE and never permanently logged in plaintext.
          </p>
        </section>
      </main>
    </div>
  );
}
