'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { formatDate } from '@/lib/utils';
import { Plus, Cpu, ArrowRight, RefreshCw, Layout, Layers, Trash2, Loader2 } from 'lucide-react';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';

const LIFECYCLE_BADGES = {
  draft: { label: 'Draft', variant: 'defaulted' },
  validated: { label: 'Validated', variant: 'inferred' },
  confirmed: { label: 'Confirmed', variant: 'confirmed' },
  generated: { label: 'Generated', variant: 'from_library' },
  verified: { label: 'Verified', variant: 'confirmed' },
  deployed: { label: 'Deployed', variant: 'confirmed' },
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!projectToDelete) return;
    setDeleting(true);
    try {
      await api.deleteProject(projectToDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== projectToDelete.id));
      setProjectToDelete(null);
    } catch (err) {
      alert(`Failed to delete project: ${err.message}`);
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <div className="container max-w-7xl p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Hardware Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Keep all your device plans, code, and live setups organized in one place.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchProjects} disabled={loading} title="Refresh">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Link href="/app/projects/new">
            <Button size="sm" className="gap-2 shadow">
              <Plus className="h-4 w-4" />
              <span>New Project</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-xl border border-border bg-card/50 animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border p-12 text-center">
          <Cpu className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground">No IoT Projects Yet</h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
            Describe your first connected hardware device in plain language to generate firmware and cloud services.
          </p>
          <Link href="/app/projects/new" className="mt-6 inline-block">
            <Button>Create Your First Project</Button>
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => {
            const badgeConfig = LIFECYCLE_BADGES[project.lifecycle] || LIFECYCLE_BADGES.draft;
            return (
              <Card
                key={project.id}
                className="group relative flex flex-col justify-between hover:border-primary/50 transition-all hover:shadow-md"
              >
                <CardHeader>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <Badge variant={badgeConfig.variant} className="capitalize">
                      {badgeConfig.label}
                    </Badge>
                    <div className="flex items-center gap-2 relative z-10">
                      <span className="text-xs font-mono text-muted-foreground">v{project.version || 1}.0</span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          setProjectToDelete(project);
                        }}
                        className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                        title="Delete project"
                        aria-label={`Delete ${project.name}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <CardTitle className="text-base group-hover:text-primary transition-colors">
                    <Link href={`/app/projects/${project.id}`} className="focus:outline-none">
                      <span className="absolute inset-0" aria-hidden="true" />
                      {project.name}
                    </Link>
                  </CardTitle>
                  <CardDescription className="line-clamp-2 mt-1">
                    {project.description || 'No description provided.'}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4 pt-0">
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Cpu className="h-3.5 w-3.5 text-primary" />
                      <span className="truncate">{project.board_id}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Layout className="h-3.5 w-3.5 text-primary" />
                      <span className="capitalize">{project.interface_type || 'dashboard'}</span>
                    </div>
                  </div>

                  <div className="border-t border-border/60 pt-3 flex items-center justify-between text-xs text-muted-foreground">
                    <span>Updated {formatDate(project.updated_at)}</span>
                    <ArrowRight className="h-4 w-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={Boolean(projectToDelete)} onOpenChange={(open) => !open && setProjectToDelete(null)}>
        <DialogHeader>
          <DialogTitle className="text-destructive flex items-center gap-2">
            <Trash2 className="h-4 w-4" />
            <span>Delete Project</span>
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong className="text-foreground">{projectToDelete?.name}</strong>? This will remove its spec versions, firmware files, and live deployments.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setProjectToDelete(null)}
            disabled={deleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleConfirmDelete}
            disabled={deleting}
            className="gap-1.5"
          >
            {deleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
            <span>Delete Project</span>
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}
