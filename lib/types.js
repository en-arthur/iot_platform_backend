import { z } from 'zod';

/**
 * @typedef {'confirmed' | 'defaulted' | 'inferred' | 'open' | 'from_library'} SpecFieldState
 * @typedef {'user' | 'platform_default' | 'ai' | 'library'} SpecFieldSource
 * @typedef {'draft' | 'validated' | 'confirmed' | 'generated' | 'verified' | 'deployed'} ProjectLifecycle
 * @typedef {'completeness' | 'electrical' | 'logical' | 'resource' | 'security'} ValidationLayer
 * @typedef {'error' | 'warning' | 'info'} IssueSeverity
 * @typedef {'dashboard' | 'web app'} InterfaceType
 */

// Zod Schemas for Runtime Validation

export const SpecFieldStateSchema = z.enum([
  'confirmed',
  'defaulted',
  'inferred',
  'open',
  'from_library',
]);

export const SpecFieldSourceSchema = z.enum([
  'user',
  'platform_default',
  'ai',
  'library',
]);

export const SpecFieldSchema = z.object({
  value: z.any(),
  state: SpecFieldStateSchema,
  source: SpecFieldSourceSchema,
  override_reason: z.string().optional(),
});

export const ValidationIssueSchema = z.object({
  id: z.string(),
  layer: z.enum(['completeness', 'electrical', 'logical', 'resource', 'security']),
  severity: z.enum(['error', 'warning', 'info']),
  field_path: z.string(),
  message: z.string(),
});

export const ValidationResponseSchema = z.array(ValidationIssueSchema);

export const LifecycleSchema = z.enum([
  'draft',
  'validated',
  'confirmed',
  'generated',
  'verified',
  'deployed',
]);

export const ProjectSchema = z.object({
  id: z.string(),
  name: z.string(),
  // Backend returns `description: null` when omitted, so accept null too.
  description: z.string().nullish().transform((v) => v ?? ''),
  board_id: z.string(),
  interface_type: z.enum(['dashboard', 'web app']).default('dashboard'),
  lifecycle: LifecycleSchema,
  created_at: z.string(),
  updated_at: z.string(),
  version: z.number().default(1),
});

export const ProjectListSchema = z.array(ProjectSchema);

export const BoardSchema = z.object({
  id: z.string(),
  name: z.string(),
  vendor: z.string(),
  mcu: z.string(),
  status: z.enum(['tested', 'draft', 'unverified']),
  specs: z.record(z.any()).optional(),
  pin_map: z.record(z.any()).optional(),
});

export const PeripheralSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  interface: z.string(),
  default_address: z.string().optional(),
  pins_required: z.array(z.string()).optional(),
  status: z.enum(['tested', 'draft', 'unverified']).default('tested'),
});

export const ProposalChangeSchema = z.object({
  path: z.string(),
  old: z.any().optional(),
  new: z.any(),
  reason: z.string(),
});

export const SpecProposalSchema = z.object({
  proposal_id: z.string(),
  summary: z.string(),
  changes: z.array(ProposalChangeSchema),
});

export const ProtectedRegionSchema = z.object({
  start_line: z.number(),
  end_line: z.number(),
  reason: z.string(),
});

export const GeneratedFileSchema = z.object({
  path: z.string(),
  content: z.string(),
  type: z.enum(['firmware', 'backend', 'interface', 'config']),
  protected_regions: z.array(ProtectedRegionSchema).optional().default([]),
});

export const TestResultSchema = z.object({
  id: z.string(),
  name: z.string(),
  layer: z.string().optional(),
  passed: z.boolean(),
  message: z.string().optional(),
  fix_proposal: SpecProposalSchema.optional(),
});

export const PipelineStepSchema = z.object({
  name: z.enum(['compile', 'simulate', 'flash', 'selftest']),
  status: z.enum(['pending', 'running', 'success', 'failed']),
  duration_ms: z.number().optional(),
  details: z.string().optional(),
});

export const VerificationRunSchema = z.object({
  run_id: z.string(),
  project_id: z.string(),
  status: z.enum(['queued', 'running', 'passed', 'failed']),
  steps: z.array(PipelineStepSchema).default([]),
  // Backend returns a single newline-delimited string; the UI needs an array.
  logs: z.preprocess(
    (v) => (typeof v === 'string' ? v.split('\n').filter((line) => line.trim() !== '') : v ?? []),
    z.array(z.string())
  ),
  tests: z.array(TestResultSchema).default([]),
  created_at: z.string().optional().default(''),
});

export const DeviceSchema = z.object({
  id: z.string(),
  name: z.string(),
  project_id: z.string(),
  status: z.enum(['online', 'offline', 'error', 'provisioned']),
  last_seen: z.string().nullish(),
  ip_address: z.string().nullish(),
  firmware_version: z.string().nullish(),
  secret: z.string().optional(), // Returned only once at provisioning
});

export const TelemetryReadingSchema = z.object({
  id: z.string(),
  device_id: z.string(),
  timestamp: z.string(),
  metric: z.string(),
  value: z.number(),
  unit: z.string(),
});
