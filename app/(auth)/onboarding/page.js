'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input, Textarea } from '@/components/ui/input';
import { createClient } from '@/lib/supabase/client';
import { Cpu, Loader2, ArrowRight } from 'lucide-react';

const ROLES = [
  { id: 'hardware_engineer', label: 'Hardware Engineer', desc: 'PCB design, embedded C/C++, pinouts' },
  { id: 'software_developer', label: 'Software Developer', desc: 'Full-stack, APIs, cloud backends' },
  { id: 'founder', label: 'Founder / Product Lead', desc: 'Rapid prototyping and connected product MVPs' },
  { id: 'other', label: 'Other', desc: 'Researcher, student, hobbyist' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('hardware_engineer');
  const [projectGoal, setProjectGoal] = useState('');
  const [loading, setLoading] = useState(false);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (isMock) {
      setTimeout(() => {
        router.push('/app/projects');
      }, 500);
      return;
    }

    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (user) {
      await supabase.from('profiles').upsert({
        id: user.id,
        full_name: fullName,
        role,
        target_goal: projectGoal,
        updated_at: new Date().toISOString(),
      });
    }

    router.push('/app/projects');
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-left">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Welcome to DeviceStack</h1>
        <p className="text-sm text-muted-foreground">
          Tell us about yourself so we can tailor the hardware library and compiler pipeline defaults.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Your Full Name
          </label>
          <Input
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Sarah Chen"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Primary Role
          </label>
          <div className="grid gap-2">
            {ROLES.map((r) => (
              <label
                key={r.id}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  role === r.id
                    ? 'border-primary bg-primary/5 text-foreground'
                    : 'border-border hover:bg-muted/50 text-muted-foreground'
                }`}
              >
                <input
                  type="radio"
                  name="role"
                  value={r.id}
                  checked={role === r.id}
                  onChange={() => setRole(r.id)}
                  className="mt-1"
                />
                <div className="text-sm">
                  <div className="font-semibold text-foreground">{r.label}</div>
                  <div className="text-xs text-muted-foreground">{r.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            What do you plan to build? (Optional)
          </label>
          <Textarea
            value={projectGoal}
            onChange={(e) => setProjectGoal(e.target.value)}
            placeholder="e.g. Smart greenhouse environmental telemetry with deep sleep and fan relay..."
            rows={2}
          />
        </div>

        <Button type="submit" disabled={loading} className="w-full gap-2">
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <span>Complete Setup & Enter Workspace</span>
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </form>
    </div>
  );
}
