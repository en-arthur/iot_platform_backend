'use client';

import React, { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { createClient } from '@/lib/supabase/client';
import { Loader2, Mail, Lock, AlertCircle } from 'lucide-react';

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get('redirect') || '/app/projects';

  const [mode, setMode] = useState('password'); // 'password' | 'magic_link'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [magicLinkSent, setMagicLinkSent] = useState(false);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

  const handleSignIn = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');

    if (isMock) {
      // Simulate successful auth in mock mode
      document.cookie = 'ai_iot_mock_auth=true; path=/; max-age=86400';
      setTimeout(() => {
        router.push(redirectPath);
      }, 500);
      return;
    }

    const supabase = createClient();

    if (mode === 'password') {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setErrorMessage(error.message);
        setLoading(false);
      } else {
        router.push(redirectPath);
      }
    } else {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback?redirect=${encodeURIComponent(redirectPath)}`,
        },
      });

      if (error) {
        setErrorMessage(error.message);
        setLoading(false);
      } else {
        setMagicLinkSent(true);
        setLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-left">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Sign In</h1>
        <p className="text-sm text-muted-foreground">
          Welcome back to DeviceStack. Enter your credentials to access your spec workspaces.
        </p>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {magicLinkSent ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-5 text-center space-y-2">
          <h3 className="font-semibold text-emerald-600 dark:text-emerald-400">Magic Link Sent!</h3>
          <p className="text-xs text-muted-foreground">
            Check your inbox at <span className="font-medium text-foreground">{email}</span> for your instant login link.
          </p>
          <Button variant="ghost" size="sm" onClick={() => setMagicLinkSent(false)} className="mt-3">
            Use password instead
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSignIn} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Work Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="engineer@company.com"
                className="pl-9"
              />
            </div>
          </div>

          {mode === 'password' && (
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-primary hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="pl-9"
                />
              </div>
            </div>
          )}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === 'password' ? 'Sign In' : 'Send Magic Link'}
          </Button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setMode(mode === 'password' ? 'magic_link' : 'password')}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {mode === 'password' ? 'Prefer passwordless? Sign in with Magic Link' : 'Sign in with Password instead'}
            </button>
          </div>
        </form>
      )}

      <div className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{' '}
        <Link href="/sign-up" className="font-semibold text-primary hover:underline">
          Sign up
        </Link>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-muted-foreground">Loading sign-in...</div>}>
      <SignInForm />
    </Suspense>
  );
}
