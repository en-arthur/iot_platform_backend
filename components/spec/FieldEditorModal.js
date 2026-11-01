'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input, Textarea } from '@/components/ui/input';
import { FieldBadge } from './FieldBadge';

export function FieldEditorModal({ open, onOpenChange, sectionKey, fieldKey, fieldData, onSave }) {
  const [val, setVal] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [isOverride, setIsOverride] = useState(false);

  useEffect(() => {
    if (fieldData) {
      setVal(
        typeof fieldData.value === 'object' && fieldData.value !== null
          ? JSON.stringify(fieldData.value, null, 2)
          : fieldData.value ?? ''
      );
      setOverrideReason(fieldData.override_reason || '');
      setIsOverride(Boolean(fieldData.override_reason));
    }
  }, [fieldData, open]);

  const handleSave = () => {
    let parsedVal = val;
    // Check if JSON
    if (typeof val === 'string' && (val.startsWith('{') || val.startsWith('['))) {
      try {
        parsedVal = JSON.parse(val);
      } catch {
        // keep as string
      }
    }
    onSave?.(sectionKey, fieldKey, parsedVal, isOverride ? overrideReason : '');
    onOpenChange(false);
  };

  if (!fieldData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <div className="flex items-center justify-between">
          <DialogTitle className="font-mono text-base">{`${sectionKey}.${fieldKey}`}</DialogTitle>
          <FieldBadge state={fieldData.state} source={fieldData.source} />
        </div>
        <DialogDescription>
          Edit this spec parameter. Modifying confirmed fields returns project to draft and bumps version.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4 py-2">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Field Value
          </label>
          {typeof val === 'string' && val.length > 50 ? (
            <Textarea
              rows={4}
              value={val}
              onChange={(e) => setVal(e.target.value)}
              className="font-mono text-xs"
            />
          ) : (
            <Input
              value={val}
              onChange={(e) => setVal(e.target.value)}
              className="font-mono text-xs"
            />
          )}
        </div>

        {/* Override with Reason Toggle */}
        <div className="pt-2 border-t border-border">
          <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-foreground">
            <input
              type="checkbox"
              checked={isOverride}
              onChange={(e) => setIsOverride(e.target.checked)}
            />
            <span>Override library / platform default with explicit reason</span>
          </label>

          {isOverride && (
            <div className="mt-2.5 space-y-1">
              <Input
                placeholder="State engineering justification for override..."
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                className="text-xs"
              />
              <p className="text-[11px] text-muted-foreground">
                Documented reasons persist into the provenance and verification record.
              </p>
            </div>
          )}
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
          Cancel
        </Button>
        <Button size="sm" onClick={handleSave}>
          Save Field Changes
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
