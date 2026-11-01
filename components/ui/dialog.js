'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

export function Dialog({ open, onOpenChange, children }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={() => onOpenChange?.(false)}
      />
      {/* Content */}
      <div className="relative z-50 w-full max-w-lg rounded-xl border border-border bg-background p-6 shadow-2xl animate-in fade-in-0 zoom-in-95">
        <button
          onClick={() => onOpenChange?.(false)}
          className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </button>
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({ className, ...props }) {
  return <div className={cn('flex flex-col space-y-1.5 text-left mb-4', className)} {...props} />;
}

export function DialogTitle({ className, ...props }) {
  return <h2 className={cn('text-lg font-semibold leading-none tracking-tight', className)} {...props} />;
}

export function DialogDescription({ className, ...props }) {
  return <p className={cn('text-sm text-muted-foreground mt-1', className)} {...props} />;
}

export function DialogFooter({ className, ...props }) {
  return <div className={cn('flex items-center justify-end space-x-2 pt-4 mt-4 border-t', className)} {...props} />;
}
