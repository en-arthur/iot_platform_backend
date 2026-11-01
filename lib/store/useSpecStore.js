import { create } from 'zustand';
import { api } from '@/lib/api';

export const useSpecStore = create((set, get) => ({
  spec: null,
  project: null,
  issues: [],
  activeProposal: null,
  isLoading: false,
  isSaving: false,
  error: null,

  setProject: (project) => set({ project }),
  setSpec: (spec) => set({ spec }),
  setIssues: (issues) => set({ issues }),
  setActiveProposal: (proposal) => set({ activeProposal: proposal }),

  loadProjectAndSpec: async (projectId) => {
    set({ isLoading: true, error: null });
    try {
      const [proj, specData, issuesData] = await Promise.all([
        api.getProject(projectId),
        api.getProjectSpec(projectId),
        api.validateSpec(projectId),
      ]);
      set({
        project: proj,
        spec: specData,
        issues: issuesData,
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  /**
   * Optimistically update a single field with rollback if API fails
   */
  updateFieldOptimistic: async (projectId, sectionKey, fieldKey, newValue, overrideReason = '') => {
    const currentSpec = get().spec;
    if (!currentSpec || !currentSpec[sectionKey]?.fields?.[fieldKey]) return;

    // Snapshot previous state for rollback
    const previousField = { ...currentSpec[sectionKey].fields[fieldKey] };

    // Apply optimistic update
    const nextSpec = JSON.parse(JSON.stringify(currentSpec));
    nextSpec[sectionKey].fields[fieldKey] = {
      ...previousField,
      value: newValue,
      state: 'confirmed',
      source: 'user',
      override_reason: overrideReason || previousField.override_reason,
    };

    set({ spec: nextSpec, isSaving: true });

    try {
      const fieldPath = `${sectionKey}.${fieldKey}`;
      await api.patchSpecFields(projectId, [
        {
          path: fieldPath,
          value: newValue,
          state: 'confirmed',
          override_reason: overrideReason,
        },
      ]);

      // Refresh validation issues after update
      const updatedIssues = await api.validateSpec(projectId);
      set({ issues: updatedIssues, isSaving: false });
    } catch (err) {
      // Rollback on failure
      const rollbackSpec = JSON.parse(JSON.stringify(get().spec));
      rollbackSpec[sectionKey].fields[fieldKey] = previousField;
      set({ spec: rollbackSpec, error: `Failed to save changes: ${err.message}`, isSaving: false });
    }
  },

  /**
   * Approve currently active AI proposal
   */
  approveProposal: async (projectId, proposalId) => {
    set({ isSaving: true });
    try {
      await api.approveProposal(projectId, proposalId);
      // Reload spec and issues
      await get().loadProjectAndSpec(projectId);
      set({ activeProposal: null, isSaving: false });
    } catch (err) {
      set({ error: err.message, isSaving: false });
    }
  },

  /**
   * Reject currently active AI proposal
   */
  rejectProposal: async (projectId, proposalId) => {
    try {
      await api.rejectProposal(projectId, proposalId);
      set({ activeProposal: null });
    } catch (err) {
      set({ error: err.message });
    }
  },

  /**
   * Confirm the spec
   */
  confirmCurrentSpec: async (projectId) => {
    set({ isSaving: true });
    try {
      const res = await api.confirmSpec(projectId);
      set((state) => ({
        project: { ...state.project, lifecycle: 'confirmed' },
        isSaving: false,
      }));
      return res;
    } catch (err) {
      set({ error: err.message, isSaving: false });
      throw err;
    }
  },
}));
