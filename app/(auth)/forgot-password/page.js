'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { createClient } from '@/lib/supabase/client';
import { Mail, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (isMock) {
      setTimeout(() => {
        setSubmitted(true);
        setLoading(false);
      }, 500);
      return;
    }

    const supabase = createClient();
    // Do not reveal if user exists (prevents user enumeration)
    await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    setSubmitted(true);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-left">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Reset Password</h1>
        <p className="text-sm text-muted-foreground">
          Enter your registered email address. If an account exists, you will receive password reset instructions.
        </p>
      </div>

      {submitted ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-6 text-center space-y-3">
          <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
          <h3 className="font-semibold text-foreground">Instructions Dispatched</h3>
          <p className="text-xs text-muted-foreground">
            If an account is associated with <span className="font-medium text-foreground">{email}</span>, you will receive an email shortly with a secure reset link.
          </p>
          <div className="pt-2">
            <Link href="/sign-in">
              <Button variant="outline" size="sm">Back to Sign In</Button>
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Account Email
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

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Send Reset Link'}
          </Button>

          <div className="text-center">
            <Link
              href="/sign-in"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Back to sign in</span>
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}
