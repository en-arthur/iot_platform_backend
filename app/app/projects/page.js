'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { formatDate } from '@/lib/utils';
import { Plus, Cpu, ArrowRight, RefreshCw, Layout, Layers } from 'lucide-react';

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

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
    } finally {
      setLoading(false);
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
                    <span className="text-xs font-mono text-muted-foreground">v{project.version || 1}.0</span>
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
    </div>
  );
}
