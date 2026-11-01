import { createClient } from '@/lib/supabase/client';
import {
  BoardSchema,
  PeripheralSchema,
  ProjectSchema,
  ProjectListSchema,
  ValidationResponseSchema,
  VerificationRunSchema,
  GeneratedFileSchema,
  DeviceSchema,
} from '@/lib/types';
import {
  MOCK_BOARDS,
  MOCK_PERIPHERALS,
  MOCK_PROJECTS,
  MOCK_SPEC_12_SECTIONS,
  MOCK_VALIDATION_ISSUES,
  MOCK_GENERATED_FILES,
  MOCK_VERIFICATION_RUN,
  MOCK_DEVICES,
  MOCK_TELEMETRY,
} from './mocks';

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1`;
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

// In-memory state for mock mutation persistence during session
const state = {
  projects: [...MOCK_PROJECTS],
  specs: {
    'proj-greenhouse-01': JSON.parse(JSON.stringify(MOCK_SPEC_12_SECTIONS)),
  },
  validationIssues: {
    'proj-greenhouse-01': [...MOCK_VALIDATION_ISSUES],
  },
  files: {
    'proj-greenhouse-01': [...MOCK_GENERATED_FILES],
  },
  verificationRuns: {
    'proj-greenhouse-01': JSON.parse(JSON.stringify(MOCK_VERIFICATION_RUN)),
  },
  devices: [...MOCK_DEVICES],
  versions: {
    'proj-greenhouse-01': [
      {
        version_number: 1,
        created_at: '2026-10-28T14:30:00Z',
        author: 'Sarah Chen',
        summary: 'Initial project spec creation from plain language prompt.',
        lifecycle: 'draft',
      },
    ],
  },
};

/**
 * Standardized API Error class
 */
export class ApiError extends Error {
  constructor(message, status = 500, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Get JWT bearer token from current Supabase session
 */
async function getAuthToken() {
  if (USE_MOCKS) return 'mock-jwt-token';
  try {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  } catch {
    return null;
  }
}

/**
 * Generic fetch wrapper for FastAPI backend
 */
async function request(endpoint, options = {}) {
  const token = await getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        data?.detail || data?.message || `Request failed with status ${response.status}`,
        response.status,
        data
      );
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Network request failed', 500);
  }
}

/* =========================================================================
   API CLIENT IMPLEMENTATION (with mock switch)
   ========================================================================= */

export const api = {
  // Health
  async getHealth() {
    if (USE_MOCKS) return { status: 'healthy', version: '1.0.0-mock' };
    return request('/health');
  },

  // Library
  async getBoards() {
    if (USE_MOCKS) return MOCK_BOARDS;
    const data = await request('/library/boards');
    return MOCK_BOARDS; // Fallback or BoardSchema.array().parse(data);
  },

  async getBoardById(id) {
    if (USE_MOCKS) {
      const b = MOCK_BOARDS.find((x) => x.id === id);
      if (!b) throw new ApiError('Board not found', 404);
      return b;
    }
    return request(`/library/boards/${id}`);
  },

  async getPeripherals(query = '') {
    if (USE_MOCKS) {
      if (!query) return MOCK_PERIPHERALS;
      return MOCK_PERIPHERALS.filter(
        (p) =>
          p.name.toLowerCase().includes(query.toLowerCase()) ||
          p.category.toLowerCase().includes(query.toLowerCase())
      );
    }
    return request(`/library/peripherals?query=${encodeURIComponent(query)}`);
  },

  // Projects
  async getProjects() {
    if (USE_MOCKS) return state.projects;
    const data = await request('/projects');
    return ProjectListSchema.parse(data);
  },

  async getProject(id) {
    if (USE_MOCKS) {
      const p = state.projects.find((x) => x.id === id);
      if (!p) throw new ApiError('Project not found', 404);
      return p;
    }
    const data = await request(`/projects/${id}`);
    return ProjectSchema.parse(data);
  },

  async createProject(payload) {
    if (USE_MOCKS) {
      const newProj = {
        id: `proj-${Date.now().toString(36)}`,
        name: payload.name || 'Untitled IoT Project',
        description: payload.description || payload.goal || '',
        board_id: payload.board_id || 'esp32-s3-devkitc-1',
        interface_type: payload.interface_type || 'dashboard',
        lifecycle: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        version: 1,
      };
      state.projects.unshift(newProj);
      state.specs[newProj.id] = JSON.parse(JSON.stringify(MOCK_SPEC_12_SECTIONS));
      state.specs[newProj.id].metadata.fields.project_name.value = newProj.name;
      state.specs[newProj.id].metadata.fields.description.value = newProj.description;
      state.specs[newProj.id].interface.fields.interface_type.value = newProj.interface_type;
      return newProj;
    }
    const data = await request('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return ProjectSchema.parse(data);
  },

  async deleteProject(id) {
    if (USE_MOCKS) {
      state.projects = state.projects.filter((p) => p.id !== id);
      delete state.specs[id];
      delete state.validationIssues[id];
      delete state.files[id];
      delete state.versions[id];
      return { success: true, id };
    }
    return request(`/projects/${id}`, { method: 'DELETE' });
  },

  // Spec
  async getProjectSpec(projectId) {
    if (USE_MOCKS) {
      const spec = state.specs[projectId] || state.specs['proj-greenhouse-01'];
      return spec;
    }
    return request(`/projects/${projectId}/spec`);
  },

  async patchSpecFields(projectId, fieldsList) {
    // fieldsList: [{ path, value, state, override_reason? }]
    if (USE_MOCKS) {
      const spec = state.specs[projectId] || state.specs['proj-greenhouse-01'];
      for (const item of fieldsList) {
        const parts = item.path.split('.');
        if (parts.length === 2) {
          const [sec, fld] = parts;
          if (spec[sec] && spec[sec].fields && spec[sec].fields[fld]) {
            spec[sec].fields[fld] = {
              ...spec[sec].fields[fld],
              value: item.value,
              state: item.state || spec[sec].fields[fld].state,
              source: 'user',
              override_reason: item.override_reason || spec[sec].fields[fld].override_reason,
            };
          }
        }
      }

      // Check if project was confirmed -> creating edits returns to draft & bumps version
      const proj = state.projects.find((p) => p.id === projectId);
      if (proj && proj.lifecycle === 'confirmed') {
        proj.lifecycle = 'draft';
        proj.version += 1;
        state.versions[projectId] = state.versions[projectId] || [];
        state.versions[projectId].push({
          version_number: proj.version,
          created_at: new Date().toISOString(),
          author: 'Engineer',
          summary: `Updated fields: ${fieldsList.map((f) => f.path).join(', ')}`,
          lifecycle: 'draft',
        });
      }

      // Automatically re-evaluate mock pin conflicts and open fields
      const buttonPin = spec.peripherals?.fields?.manual_override_button_pin?.value;
      const bmeSda = spec.peripherals?.fields?.bme280_sda_pin?.value;
      const targetDate = spec.metadata?.fields?.target_deployment_date?.value;

      state.validationIssues[projectId] = [];
      if (buttonPin === bmeSda) {
        state.validationIssues[projectId].push({
          id: 'iss-err-1',
          layer: 'electrical',
          severity: 'error',
          field_path: 'peripherals.manual_override_button_pin',
          message: `Electrical Pin Collision: ${buttonPin} is mapped to both BME280 I2C SDA and Button Input. Remap Button.`,
        });
      }
      if (!targetDate) {
        state.validationIssues[projectId].push({
          id: 'iss-block-open',
          layer: 'completeness',
          severity: 'error',
          field_path: 'metadata.target_deployment_date',
          message: 'Blocking field "target_deployment_date" is currently open and required.',
        });
      }
      return { success: true, updated_count: fieldsList.length, spec };
    }

    return request(`/projects/${projectId}/spec/fields`, {
      method: 'PATCH',
      body: JSON.stringify(fieldsList),
    });
  },

  async validateSpec(projectId) {
    if (USE_MOCKS) {
      const issues = state.validationIssues[projectId] || state.validationIssues['proj-greenhouse-01'] || [];
      return ValidationResponseSchema.parse(issues);
    }
    const data = await request(`/projects/${projectId}/spec/validate`, {
      method: 'POST',
    });
    return ValidationResponseSchema.parse(data);
  },

  async confirmSpec(projectId) {
    if (USE_MOCKS) {
      const issues = state.validationIssues[projectId] || state.validationIssues['proj-greenhouse-01'] || [];
      const blocking = issues.filter((i) => i.severity === 'error');
      if (blocking.length > 0) {
        throw new ApiError(
          `Cannot confirm spec: ${blocking.length} blocking issues exist.`,
          409,
          { blocking_issues: blocking }
        );
      }
      const proj = state.projects.find((p) => p.id === projectId);
      if (proj) {
        proj.lifecycle = 'confirmed';
        proj.updated_at = new Date().toISOString();
      }
      return { success: true, lifecycle: 'confirmed', project: proj };
    }
    return request(`/projects/${projectId}/spec/confirm`, { method: 'POST' });
  },

  // Versions
  async getVersions(projectId) {
    if (USE_MOCKS) {
      return state.versions[projectId] || [
        {
          version_number: 1,
          created_at: '2026-10-28T14:30:00Z',
          author: 'Sarah Chen',
          summary: 'Initial project spec creation from plain language prompt.',
          lifecycle: 'draft',
        },
      ];
    }
    return request(`/projects/${projectId}/versions`);
  },

  async getVersionDiff(projectId, a, b) {
    if (USE_MOCKS) {
      return {
        base_version: a,
        target_version: b,
        differences: [
          {
            field_path: 'peripherals.manual_override_button_pin',
            from: 'GPIO4',
            to: 'GPIO10',
            reason: 'Remapped to resolve pin conflict with BME280 SDA',
          },
          {
            field_path: 'metadata.target_deployment_date',
            from: null,
            to: '2026-12-01',
            reason: 'Target deployment deadline specified',
          },
        ],
      };
    }
    return request(`/projects/${projectId}/versions/${a}/diff/${b}`);
  },

  // Proposals
  async approveProposal(projectId, proposalId) {
    if (USE_MOCKS) {
      // Execute the proposal fix
      const spec = state.specs[projectId] || state.specs['proj-greenhouse-01'];
      if (spec.peripherals?.fields?.manual_override_button_pin) {
        spec.peripherals.fields.manual_override_button_pin.value = 'GPIO10';
        spec.peripherals.fields.manual_override_button_pin.state = 'confirmed';
      }
      if (spec.metadata?.fields?.target_deployment_date) {
        spec.metadata.fields.target_deployment_date.value = '2026-12-01';
        spec.metadata.fields.target_deployment_date.state = 'confirmed';
      }

      // Clear blocking issues
      state.validationIssues[projectId] = [];

      // Bump version
      const proj = state.projects.find((p) => p.id === projectId);
      if (proj) {
        proj.version += 1;
        proj.lifecycle = 'validated';
        state.versions[projectId] = state.versions[projectId] || [];
        state.versions[projectId].push({
          version_number: proj.version,
          created_at: new Date().toISOString(),
          author: 'AI Assistant (Approved)',
          summary: 'Approved Proposal: Resolve GPIO4 Pin Conflict & Target Deployment Date',
          lifecycle: 'validated',
        });
      }

      return { success: true, message: 'Proposal approved and applied.', new_version: proj?.version || 2 };
    }
    return request(`/projects/${projectId}/proposals/${proposalId}/approve`, { method: 'POST' });
  },

  async rejectProposal(projectId, proposalId) {
    if (USE_MOCKS) {
      return { success: true, message: 'Proposal rejected without changes.' };
    }
    return request(`/projects/${projectId}/proposals/${proposalId}/reject`, { method: 'POST' });
  },

  // Files
  async getFiles(projectId) {
    if (USE_MOCKS) {
      return state.files[projectId] || state.files['proj-greenhouse-01'];
    }
    const data = await request(`/projects/${projectId}/files`);
    return GeneratedFileSchema.array().parse(data);
  },

  async updateFile(projectId, filePath, content) {
    if (USE_MOCKS) {
      const files = state.files[projectId] || state.files['proj-greenhouse-01'];
      const file = files.find((f) => f.path === filePath);
      if (file) {
        file.content = content;
      }
      return { success: true, path: filePath };
    }
    return request(`/projects/${projectId}/files/${encodeURIComponent(filePath)}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  },

  // Verification & Runs
  async triggerVerify(projectId) {
    if (USE_MOCKS) {
      const proj = state.projects.find((p) => p.id === projectId);
      if (proj) proj.lifecycle = 'verified';
      return { run_id: 'run-gh-test-901' };
    }
    return request(`/projects/${projectId}/verify`, { method: 'POST' });
  },

  async getVerificationRun(runId) {
    if (USE_MOCKS) {
      return state.verificationRuns['proj-greenhouse-01'];
    }
    const data = await request(`/runs/${runId}`);
    return VerificationRunSchema.parse(data);
  },

  async submitSelfTestResults(runId, results) {
    if (USE_MOCKS) {
      return { success: true, passed: true, submitted_at: new Date().toISOString() };
    }
    return request(`/runs/${runId}/selftest`, {
      method: 'POST',
      body: JSON.stringify(results),
    });
  },

  // Devices & Commands
  async getDevices(projectId) {
    if (USE_MOCKS) {
      return state.devices.filter((d) => !projectId || d.project_id === projectId);
    }
    const data = await request(`/projects/${projectId}/devices`);
    return DeviceSchema.array().parse(data);
  },

  async provisionDevice(projectId, payload) {
    if (USE_MOCKS) {
      const newDev = {
        id: `dev-${Math.random().toString(36).substring(2, 9)}`,
        name: payload.name || 'Greenhouse Node',
        project_id: projectId,
        status: 'online',
        last_seen: 'Just now',
        ip_address: '192.168.1.150',
        firmware_version: 'v1.0.0',
        secret: `sec_live_${Math.random().toString(36).substring(2, 12)}_${Date.now()}`, // Returned ONCE!
      };
      state.devices.push(newDev);
      return newDev;
    }
    return request(`/projects/${projectId}/devices`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async sendDeviceCommand(deviceId, command) {
    if (USE_MOCKS) {
      return {
        success: true,
        device_id: deviceId,
        command,
        timestamp: new Date().toISOString(),
      };
    }
    return request(`/devices/${deviceId}/commands`, {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  },

  // Deploy
  async deployProject(projectId) {
    if (USE_MOCKS) {
      const proj = state.projects.find((p) => p.id === projectId);
      if (proj) proj.lifecycle = 'deployed';
      return { success: true, lifecycle: 'deployed', deployed_at: new Date().toISOString() };
    }
    return request(`/projects/${projectId}/deploy`, { method: 'POST' });
  },

  // Telemetry (mock readings)
  async getTelemetry(deviceId) {
    return MOCK_TELEMETRY;
  },
};
