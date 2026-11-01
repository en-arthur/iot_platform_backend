'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

export function Tooltip({ text, children, className }) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className={cn('relative inline-flex items-center', className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && text && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2.5 py-1 text-xs font-medium text-background shadow-md animate-in fade-in-0 zoom-in-95 pointer-events-none"
        >
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-foreground" />
        </div>
      )}
    </div>
  );
}
