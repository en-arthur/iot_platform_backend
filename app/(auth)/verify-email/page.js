'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { createClient } from '@/lib/supabase/client';
import { MailCheck, RefreshCw, ArrowLeft } from 'lucide-react';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || 'your email';

  const [cooldown, setCooldown] = useState(60);
  const [resending, setResending] = useState(false);
  const [message, setMessage] = useState('');

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleResend = async () => {
    if (cooldown > 0 || resending) return;
    setResending(true);
    setMessage('');

    if (isMock) {
      setTimeout(() => {
        setResending(false);
        setCooldown(60);
        setMessage('A new verification email has been sent!');
      }, 500);
      return;
    }

    const supabase = createClient();
    const { error } = await supabase.auth.resend({
      type: 'signup',
      email,
    });

    setResending(false);
    if (error) {
      setMessage(`Error: ${error.message}`);
    } else {
      setCooldown(60);
      setMessage('A fresh verification link has been delivered to your inbox.');
    }
  };

  return (
    <div className="space-y-6 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
        <MailCheck className="h-7 w-7" />
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Verify Your Email</h1>
        <p className="text-sm text-muted-foreground">
          We sent an activation link to <span className="font-semibold text-foreground">{email}</span>. Please verify your address to continue.
        </p>
      </div>

      {message && (
        <div className="rounded-lg bg-muted p-3 text-xs text-muted-foreground">
          {message}
        </div>
      )}

      <div className="space-y-3 pt-2">
        <Button
          onClick={handleResend}
          disabled={cooldown > 0 || resending}
          variant="outline"
          className="w-full gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${resending ? 'animate-spin' : ''}`} />
          <span>
            {cooldown > 0 ? `Resend email in ${cooldown}s` : 'Resend verification email'}
          </span>
        </Button>

        <div>
          <Link
            href="/sign-in"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            <span>Return to sign in</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
