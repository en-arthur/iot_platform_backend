import { describe, it, expect } from 'vitest';
import { api } from '../lib/api';
import { SpecFieldSchema, ValidationResponseSchema } from '../lib/types';

describe('AI IoT Builder Spec & Contract Tests', () => {
  it('validates 12-section spec field format matches contract', async () => {
    const spec = await api.getProjectSpec('proj-greenhouse-01');
    expect(spec).toBeDefined();

    // Verify all 12 sections exist
    const sections = [
      'metadata',
      'hardware',
      'peripherals',
      'behavior',
      'data_model',
      'connectivity',
      'cloud_backend',
      'interface',
      'security',
      'updates',
      'verification',
      'provenance',
    ];

    for (const sec of sections) {
      expect(spec[sec]).toBeDefined();
      expect(spec[sec].fields).toBeDefined();
      for (const [key, field] of Object.entries(spec[sec].fields)) {
        // Runtime validate against Zod SpecFieldSchema
        expect(() => SpecFieldSchema.parse(field)).not.toThrow();
      }
    }
  });

  it('blocks spec confirmation when blocking electrical or completeness issues exist', async () => {
    await expect(api.confirmSpec('proj-greenhouse-01')).rejects.toThrow(/Cannot confirm spec/);
  });

  it('approves AI proposal, resolves pin collision, and creates new version', async () => {
    const res = await api.approveProposal('proj-greenhouse-01', 'prop-fix-pin-conflict');
    expect(res.success).toBe(true);
    expect(res.new_version).toBeGreaterThanOrEqual(2);

    // Verify issues cleared
    const issues = await api.validateSpec('proj-greenhouse-01');
    const errors = issues.filter((i) => i.severity === 'error');
    expect(errors.length).toBe(0);

    // Now confirm spec succeeds
    const confirmRes = await api.confirmSpec('proj-greenhouse-01');
    expect(confirmRes.success).toBe(true);
    expect(confirmRes.lifecycle).toBe('confirmed');
  });
});
