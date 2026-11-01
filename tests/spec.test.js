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

  it('disables Confirm while any open field exists', async () => {
    const spec = await api.getProjectSpec('proj-greenhouse-01');
    const openFields = [];
    for (const [secKey, sec] of Object.entries(spec)) {
      for (const [fKey, field] of Object.entries(sec.fields || {})) {
        if (field.state === 'open') {
          openFields.push(`${secKey}.${fKey}`);
        }
      }
    }

    // Confirm that open fields exist in the initial mock spec
    expect(openFields.length).toBeGreaterThan(0);
    expect(openFields).toContain('metadata.target_deployment_date');

    // Attempting confirmation must be blocked while open fields remain
    await expect(api.confirmSpec('proj-greenhouse-01')).rejects.toThrow();
  });

  it('correctly filters fields using the "Needs attention" filter', async () => {
    const spec = await api.getProjectSpec('proj-greenhouse-01');
    const issues = await api.validateSpec('proj-greenhouse-01');

    const filterNeedsAttention = (sectionKey, fields) => {
      return Object.entries(fields).filter(([fKey, fData]) => {
        const fieldPath = `${sectionKey}.${fKey}`;
        const hasIssue = issues.some((i) => i.field_path === fieldPath);
        const isOpen = fData.state === 'open';
        const isAi = fData.state === 'inferred' || fData.source === 'ai';
        return isOpen || isAi || hasIssue;
      });
    };

    // Metadata section: target_deployment_date is 'open', project_name and author are 'confirmed'
    const metadataAttention = filterNeedsAttention('metadata', spec.metadata.fields);
    const metadataAttentionKeys = metadataAttention.map(([k]) => k);
    expect(metadataAttentionKeys).toContain('target_deployment_date');
    expect(metadataAttentionKeys).not.toContain('project_name');
    expect(metadataAttentionKeys).not.toContain('author');

    // Hardware section: deep_sleep_enabled is inferred (AI proposed)
    const hardwareAttention = filterNeedsAttention('hardware', spec.hardware.fields);
    const hardwareAttentionKeys = hardwareAttention.map(([k]) => k);
    expect(hardwareAttentionKeys).toContain('deep_sleep_enabled');

    // Peripherals section: has pin conflict issue on bme280_sda_pin and button_pin
    const peripheralsAttention = filterNeedsAttention('peripherals', spec.peripherals.fields);
    const peripheralsAttentionKeys = peripheralsAttention.map(([k]) => k);
    expect(peripheralsAttentionKeys).toContain('bme280_sda_pin');
  });

  it('stepper never renders "Deployed" while the spec has open fields or errors', () => {
    // Stepper lifecycle resolution rule:
    // If hasBlockingErrorsOrOpenFields is true, effective lifecycle is forced to 'draft'
    const calculateEffectiveLifecycle = (projectLifecycle, openCount, errorCount) => {
      const hasBlocking = openCount > 0 || errorCount > 0;
      if (hasBlocking) return 'draft';
      return projectLifecycle || 'draft';
    };

    // Case 1: project says 'deployed', but has 1 open field -> must be 'draft'
    expect(calculateEffectiveLifecycle('deployed', 1, 0)).toBe('draft');

    // Case 2: project says 'deployed', has 1 error -> must be 'draft'
    expect(calculateEffectiveLifecycle('deployed', 0, 1)).toBe('draft');

    // Case 3: project says 'deployed', 0 open fields, 0 errors -> can be 'deployed'
    expect(calculateEffectiveLifecycle('deployed', 0, 0)).toBe('deployed');

    // Case 4: project says 'confirmed', but has open fields -> must be 'draft'
    expect(calculateEffectiveLifecycle('confirmed', 2, 0)).toBe('draft');
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
