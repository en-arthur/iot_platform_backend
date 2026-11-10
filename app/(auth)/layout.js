import Link from 'next/link';
import { Cpu, ShieldCheck, Zap, Terminal } from 'lucide-react';
import { ThemeToggle } from '@/components/layout/ThemeToggle';

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen grid lg:grid-cols-12 bg-background">
      {/* Branded Left Side Panel (Desktop) */}
      <div className="hidden lg:flex lg:col-span-5 relative flex-col justify-between p-10 bg-slate-950 text-white border-r border-slate-800">
        <div>
          <Link href="/" className="inline-flex items-center gap-2.5 font-bold text-xl tracking-tight">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md">
              <Cpu className="h-5 w-5" />
            </div>
            <span>DeviceStack</span>
          </Link>
          <div className="mt-20 space-y-6">
            <h2 className="text-3xl font-extrabold tracking-tight text-white leading-tight">
              One Place for Your Hardware & Software.
            </h2>
            <p className="text-slate-400 text-base leading-relaxed">
              Set up your device idea once. We take care of the code, check for pin mistakes, and connect it to the cloud so everything just works.
            </p>
            <div className="space-y-4 pt-6">
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                <span>Strict electrical & completeness gate enforcement</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <Zap className="h-5 w-5 text-amber-400" />
                <span>Browser Web Serial flashing for ESP32</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <Terminal className="h-5 w-5 text-sky-400" />
                <span>FastAPI backend generation with telemetry models</span>
              </div>
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-500">
          Trusted by embedded engineers and hardware innovators worldwide.
        </div>
      </div>

      {/* Auth Content Panel */}
      <div className="col-span-12 lg:col-span-7 flex flex-col justify-between p-6 sm:p-12 relative">
        <div className="flex justify-between items-center w-full max-w-md mx-auto">
          <Link href="/" className="lg:hidden flex items-center gap-2 font-bold text-lg">
            <Cpu className="h-5 w-5 text-primary" />
            <span>DeviceStack</span>
          </Link>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>

        <div className="w-full max-w-md mx-auto my-auto py-8">
          {children}
        </div>

        <div className="w-full max-w-md mx-auto text-center text-xs text-muted-foreground">
          By signing in, you agree to our{' '}
          <Link href="/terms" className="underline hover:text-foreground">Terms</Link> and{' '}
          <Link href="/privacy" className="underline hover:text-foreground">Privacy Policy</Link>.
        </div>
      </div>
    </div>
  );
}
