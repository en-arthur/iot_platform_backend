'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Cpu, HardDrive, Zap, Network } from 'lucide-react';

export function DependenciesPanel({ spec }) {
  const mcu = spec?.hardware?.fields?.board_id?.value || 'ESP32-S3';
  const i2cAddr = spec?.peripherals?.fields?.bme280_i2c_addr?.value || '0x76';
  const sda = spec?.peripherals?.fields?.bme280_sda_pin?.value || 'GPIO4';
  const scl = spec?.peripherals?.fields?.bme280_scl_pin?.value || 'GPIO5';
  const relay = spec?.peripherals?.fields?.fan_relay_pin?.value || 'GPIO9';
  const button = spec?.peripherals?.fields?.manual_override_button_pin?.value || 'GPIO4';

  const hasCollision = sda === button;

  return (
    <div className="p-4 space-y-4 overflow-y-auto h-full text-xs">
      <div>
        <h4 className="font-bold text-foreground mb-1">Hardware Map & Dependencies</h4>
        <p className="text-muted-foreground">Direct silicon mapping for {mcu}</p>
      </div>

      <div className="rounded-xl border border-border bg-card p-3.5 space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <span className="font-semibold text-foreground flex items-center gap-1.5">
            <Network className="h-4 w-4 text-primary" />
            <span>I2C Bus 0</span>
          </span>
          <Badge variant="confirmed">Active</Badge>
        </div>
        <div className="space-y-1.5 font-mono text-[11px]">
          <div className="flex justify-between">
            <span className="text-muted-foreground">SDA Pin:</span>
            <span className="font-bold">{sda}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">SCL Pin:</span>
            <span className="font-bold">{scl}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Device Address:</span>
            <span className="text-primary font-bold">{i2cAddr} (BME280)</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-3.5 space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <span className="font-semibold text-foreground flex items-center gap-1.5">
            <Zap className="h-4 w-4 text-amber-500" />
            <span>GPIO Allocation</span>
          </span>
          {hasCollision ? (
            <Badge variant="destructive">Conflict</Badge>
          ) : (
            <Badge variant="confirmed">Valid</Badge>
          )}
        </div>
        <div className="space-y-1.5 font-mono text-[11px]">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Relay Out:</span>
            <span className="font-bold">{relay}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Button In:</span>
            <span className={hasCollision ? 'text-destructive font-bold' : 'font-bold'}>
              {button} {hasCollision && '(COLLISION!)'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
