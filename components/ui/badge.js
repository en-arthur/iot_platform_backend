import React from 'react';
import { cn } from '@/lib/utils';

export function Badge({ className, variant = 'default', children, ...props }) {
  const variants = {
    default: 'bg-primary/10 text-primary border-primary/20',
    secondary: 'bg-secondary text-secondary-foreground border-border',
    destructive: 'bg-destructive/15 text-destructive border-destructive/30',
    outline: 'text-foreground border-border',
    // Field States
    confirmed: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
    defaulted: 'bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30',
    inferred: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30',
    open: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
    from_library: 'bg-sky-500/15 text-sky-600 dark:text-sky-400 border-sky-500/30',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variants[variant] || variants.default,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
