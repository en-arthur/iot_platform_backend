'use client';

import React, { useState, useEffect, use } from 'react';
import { api } from '@/lib/api';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Radio, Key, Play, Copy, Check, Loader2, AlertTriangle, RefreshCw, ExternalLink } from 'lucide-react';

export default function LiveInterfacePage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const { project, spec } = useSpecStore();

  const [devices, setDevices] = useState([]);
  const [deploying, setDeploying] = useState(false);
  const [deployed, setDeployed] = useState(project?.lifecycle === 'deployed');
  const [newDeviceSecretModal, setNewDeviceSecretModal] = useState(null);
  const [copiedSecret, setCopiedSecret] = useState(false);
  
  // E2B interface state
  const [interfaceUrl, setInterfaceUrl] = useState(null);
  const [loadingInterface, setLoadingInterface] = useState(true);
  const [interfaceError, setInterfaceError] = useState('');

  const interfaceType =
    spec?.interface?.fields?.interface_type?.value || project?.interface_type || 'web app';

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const devs = await api.getDevices(projectId);
        if (!cancelled) setDevices(Array.isArray(devs) ? devs : []);
      } catch {
        if (!cancelled) setDevices([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  useEffect(() => {
    if (project?.lifecycle === 'deployed') setDeployed(true);
  }, [project]);

  // Auto-load interface when deployed
  useEffect(() => {
    let cancelled = false;
    
    (async () => {
      if (!deployed) {
        setLoadingInterface(false);
        return;
      }
      
      setLoadingInterface(true);
      setInterfaceError('');
      
      try {
        const response = await fetch(`/api/projects/${projectId}/interface/url`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to load interface');
        }

        const data = await response.json();
        if (!cancelled) {
          if (data.url) {
            setInterfaceUrl(data.url);
          } else if (data.deployed === false) {
            setInterfaceError('No interface generated yet. Generate code first in the Code tab.');
          }
        }
      } catch (err) {
        if (!cancelled) {
          setInterfaceError(err.message || 'Failed to load interface');
        }
      } finally {
        if (!cancelled) {
          setLoadingInterface(false);
        }
      }
    })();
    
    return () => { cancelled = true; };
  }, [projectId, deployed]);

  const handleDeploy = async () => {
    setDeploying(true);
    try {
      await api.deployProject(projectId);
      setDeployed(true);
    } finally {
      setDeploying(false);
    }
  };

  const handleProvisionDevice = async () => {
    const newDev = await api.provisionDevice(projectId, { name: `Device ${devices.length + 1}` });
    setDevices((prev) => [...prev, newDev]);
    setNewDeviceSecretModal(newDev);
  };

  const handleRefreshInterface = async () => {
    // Destroy old sandbox and reload
    try {
      await fetch(`/api/projects/${projectId}/interface/destroy`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      });
    } catch (err) {
      console.warn('Failed to destroy old interface:', err);
    }
    
    setInterfaceUrl(null);
    setLoadingInterface(true);
    
    // Trigger reload
    try {
      const response = await fetch(`/api/projects/${projectId}/interface/url`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.url) {
          setInterfaceUrl(data.url);
        }
      }
    } catch (err) {
      setInterfaceError(err.message || 'Failed to refresh interface');
    } finally {
      setLoadingInterface(false);
    }
  };

  const handleCopySecret = () => {
    if (newDeviceSecretModal?.secret) {
      navigator.clipboard.writeText(newDeviceSecretModal.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

  return (
    <div className="container max-w-7xl p-6 md:p-8 space-y-6 h-full overflow-y-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Radio className="h-6 w-6 text-emerald-500" />
              <span>Live {interfaceType === 'web app' ? 'Web App' : 'Dashboard'}</span>
            </h1>
            <Badge variant={interfaceType === 'web app' ? 'confirmed' : 'defaulted'}>
              {interfaceType === 'web app' ? 'Web App' : 'Dashboard'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Your generated interface, running live on E2B. It reads real telemetry from your device.
          </p>
        </div>
        <div className="flex gap-2">
          {!deployed ? (
            <Button onClick={handleDeploy} disabled={deploying} className="gap-2 shadow">
              {deploying ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              <span>Deploy to Cloud</span>
            </Button>
          ) : (
            <>
              {interfaceUrl && (
                <Button 
                  onClick={handleRefreshInterface} 
                  disabled={loadingInterface}
                  size="sm" 
                  variant="outline" 
                  className="gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Refresh</span>
                </Button>
              )}
              <Button onClick={handleProvisionDevice} size="sm" variant="outline" className="gap-2">
                <Key className="h-4 w-4 text-primary" />
                <span>Provision Device</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {!deployed ? (
        <div className="rounded-xl border border-border bg-card p-10 flex flex-col items-center text-center gap-3">
          <Radio className="h-8 w-8 text-muted-foreground" />
          <div className="text-sm font-semibold text-foreground">Deploy to see your live interface</div>
          <p className="text-xs text-muted-foreground max-w-md">
            Deploy the project, provision a device, and its readings will appear here in the generated interface.
          </p>
        </div>
      ) : loadingInterface ? (
        <div className="rounded-xl border border-border bg-card p-10 flex items-center justify-center text-xs text-muted-foreground gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading interface preview from E2B sandbox...
        </div>
      ) : interfaceError ? (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-2 text-xs text-muted-foreground">
          <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
          <span>{interfaceError}</span>
        </div>
      ) : interfaceUrl ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live on E2B</span>
            </div>
            <a 
              href={interfaceUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-primary hover:underline"
            >
              <span>Open in new tab</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <div className="rounded-xl border border-border bg-white overflow-hidden">
            <iframe
              title="Generated interface preview"
              src={interfaceUrl}
              sandbox="allow-scripts allow-same-origin allow-forms"
              className="w-full h-[72vh] border-0"
            />
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-10 flex flex-col items-center text-center gap-3">
          <Radio className="h-8 w-8 text-muted-foreground" />
          <div className="text-sm font-semibold text-foreground">No interface preview available</div>
          <p className="text-xs text-muted-foreground max-w-md">
            Generate code first in the Code tab, then return here to see the live interface.
          </p>
        </div>
      )}

      {newDeviceSecretModal && (
        <Dialog open={Boolean(newDeviceSecretModal)} onOpenChange={() => setNewDeviceSecretModal(null)}>
          <DialogHeader>
            <div className="flex items-center gap-2 text-amber-500">
              <Key className="h-5 w-5" />
              <DialogTitle>Provisioning Secret Returned ONCE</DialogTitle>
            </div>
            <DialogDescription>
              Copy this device key immediately. For security, it will never be displayed again.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-3">
            <div className="text-xs font-semibold text-foreground">
              Device: {newDeviceSecretModal.name} ({newDeviceSecretModal.id})
            </div>
            <div className="flex items-center gap-2">
              <Input readOnly value={newDeviceSecretModal.secret} className="font-mono text-xs select-all bg-muted" />
              <Button size="icon" variant="outline" onClick={handleCopySecret} className="shrink-0">
                {copiedSecret ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Keep this key somewhere safe. Your device needs it the first time it connects.
            </p>
          </div>

          <DialogFooter>
            <Button onClick={() => setNewDeviceSecretModal(null)}>I Have Saved This Key</Button>
          </DialogFooter>
        </Dialog>
      )}
    </div>
  );
}
