'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { createClient } from '@/lib/supabase/client';
import { Lock, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [success, setSuccess] = useState(false);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

  const handleReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match');
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long');
      setLoading(false);
      return;
    }

    if (isMock) {
      setTimeout(() => {
        setSuccess(true);
        setLoading(false);
        setTimeout(() => router.push('/sign-in'), 1500);
      }, 500);
      return;
    }

    const supabase = createClient();
    const { error } = await supabase.auth.updateUser({
      password,
    });

    if (error) {
      setErrorMessage(error.message);
      setLoading(false);
    } else {
      setSuccess(true);
      setLoading(false);
      setTimeout(() => router.push('/app/projects'), 1500);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-left">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Set New Password</h1>
        <p className="text-sm text-muted-foreground">
          Choose a secure new password for your AI IoT Builder account.
        </p>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {success ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-6 text-center space-y-2">
          <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
          <h3 className="font-semibold text-foreground">Password Updated!</h3>
          <p className="text-xs text-muted-foreground">Redirecting to your workspace...</p>
        </div>
      ) : (
        <form onSubmit={handleReset} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              New Password (min 8 characters)
            </label>
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

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Confirm New Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="pl-9"
              />
            </div>
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Update Password'}
          </Button>
        </form>
      )}
    </div>
  );
}
