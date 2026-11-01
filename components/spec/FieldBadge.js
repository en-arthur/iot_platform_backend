import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip } from '@/components/ui/tooltip';
import { CheckCircle2, Bookmark, Sparkles, AlertCircle, BookOpen } from 'lucide-react';

const STATE_CONFIG = {
  confirmed: {
    label: 'Confirmed',
    icon: CheckCircle2,
    variant: 'confirmed',
    tooltip: 'Explicitly reviewed and confirmed by engineer',
  },
  defaulted: {
    label: 'Defaulted',
    icon: Bookmark,
    variant: 'defaulted',
    tooltip: 'Standard platform default setting',
  },
  inferred: {
    label: 'Inferred',
    icon: Sparkles,
    variant: 'inferred',
    tooltip: 'Inferred by AI based on your device description',
  },
  open: {
    label: 'Open',
    icon: AlertCircle,
    variant: 'open',
    tooltip: 'Blocking field: Action or value required before confirmation',
  },
  from_library: {
    label: 'Library',
    icon: BookOpen,
    variant: 'from_library',
    tooltip: 'Bound to verified hardware library component',
  },
};

/**
 * Field state badge with Icon, label and accessible tooltip
 * Contract rule: Field states get a badge, icon, and tooltip, never color alone.
 */
export function FieldBadge({ state, source, overrideReason }) {
  const config = STATE_CONFIG[state] || STATE_CONFIG.defaulted;
  const Icon = config.icon;

  const tooltipText = overrideReason
    ? `${config.tooltip} (Override: ${overrideReason})`
    : `${config.tooltip}${source ? ` • Source: ${source}` : ''}`;

  return (
    <Tooltip text={tooltipText}>
      <Badge variant={config.variant} className="cursor-help select-none">
        <Icon className="h-3 w-3" aria-hidden="true" />
        <span>{config.label}</span>
      </Badge>
    </Tooltip>
  );
}
