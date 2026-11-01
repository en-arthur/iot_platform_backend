import Link from 'next/link';
import { Cpu, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/layout/ThemeToggle';

export default function PricingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border/40 py-4">
        <div className="container max-w-7xl px-4 sm:px-8 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Cpu className="h-5 w-5 text-primary" />
            <span>AI IoT Builder</span>
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/sign-in"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/sign-up"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <main className="container max-w-7xl px-4 sm:px-8 py-16 flex-1">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="default">Pricing Plans</Badge>
          <h1 className="text-4xl font-extrabold mt-3 text-foreground">Scalable Hardware Engineering</h1>
          <p className="mt-3 text-muted-foreground">Select the right tier for your hardware prototyping or fleet production.</p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-xl font-bold">Hobby / Maker</h3>
              <div className="text-3xl font-extrabold mt-4">$0 <span className="text-sm font-normal text-muted-foreground">/mo</span></div>
              <p className="text-sm text-muted-foreground mt-2">Free prototyping for weekend tinkerers.</p>
              <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> 3 active projects</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Web Serial browser flasher</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Community hardware library</li>
              </ul>
            </div>
            <Link href="/sign-up" className="mt-8"><Button variant="outline" className="w-full">Sign Up Free</Button></Link>
          </div>

          <div className="rounded-xl border-2 border-primary bg-card p-6 shadow-lg flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold">Pro Engineer</h3>
                <Badge variant="default">Most Popular</Badge>
              </div>
              <div className="text-3xl font-extrabold mt-4">$49 <span className="text-sm font-normal text-muted-foreground">/mo</span></div>
              <p className="text-sm text-muted-foreground mt-2">Full toolchain for professional embedded developers.</p>
              <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Unlimited projects & spec versions</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> QEMU & Wokwi simulation pipelines</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Web App bundles with role-based auth</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Protected code regions preservation</li>
              </ul>
            </div>
            <Link href="/sign-up" className="mt-8"><Button className="w-full">Start 14-Day Trial</Button></Link>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-xl font-bold">Team / Fleet</h3>
              <div className="text-3xl font-extrabold mt-4">$199 <span className="text-sm font-normal text-muted-foreground">/mo</span></div>
              <p className="text-sm text-muted-foreground mt-2">Enterprise fleet OTA deployment & verified security.</p>
              <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Fleet OTA rollbacks & health checks</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Private peripheral libraries</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Self-hosted FastAPI backend</li>
              </ul>
            </div>
            <Link href="/sign-up" className="mt-8"><Button variant="outline" className="w-full">Contact Sales</Button></Link>
          </div>
        </div>
      </main>
    </div>
  );
}
