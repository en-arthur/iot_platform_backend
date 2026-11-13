'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { loadIdentity } from '@/lib/profile';
import {
  Settings,
  User,
  Key,
  Lock,
  Trash2,
  Copy,
  Check,
  RotateCw,
  LogOut,
  AlertTriangle,
} from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('');
  const [email, setEmail] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const identity = await loadIdentity();
        if (!identity || cancelled) return;
        setFullName(identity.name === 'Account' ? '' : identity.name);
        setRole(identity.role === 'Signed in' ? '' : identity.role);
        setEmail(identity.email);
      } catch {
        // Leave the fields empty if the profile cannot be read.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // API Token state
  const [apiToken, setApiToken] = useState('iot_live_9a8b7c6d5e4f3a2b1c0d_prod');
  const [copiedToken, setCopiedToken] = useState(false);
  const [rotating, setRotating] = useState(false);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState('');

  // Delete account modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const handleCopyToken = () => {
    navigator.clipboard.writeText(apiToken);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const handleRotateToken = () => {
    setRotating(true);
    setTimeout(() => {
      setApiToken(`iot_live_${Math.random().toString(36).substring(2, 18)}_prod`);
      setRotating(false);
    }, 500);
  };

  const handleChangePassword = (e) => {
    e.preventDefault();
    setPasswordMsg('Password successfully changed.');
    setCurrentPassword('');
    setNewPassword('');
    setTimeout(() => setPasswordMsg(''), 3000);
  };

  const handleDeleteAccount = () => {
    if (deleteConfirmText === 'DELETE') {
      document.cookie = 'ai_iot_mock_auth=; path=/; max-age=0';
      router.push('/');
    }
  };

  return (
    <div className="container max-w-4xl p-6 md:p-10 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Settings className="h-6 w-6 text-primary" />
          <span>Account & Security Settings</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your engineer profile, API bearer credentials, and workspace security preferences.
        </p>
      </div>

      {/* Profile Section */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <h3 className="font-semibold text-base flex items-center gap-2">
          <User className="h-4 w-4 text-primary" />
          <span>Profile Information</span>
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Full Name
            </label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Engineering Role
            </label>
            <Input value={role} onChange={(e) => setRole(e.target.value)} />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Email Address
            </label>
            <Input value={email} disabled className="bg-muted text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* API Tokens Section */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-base flex items-center gap-2">
            <Key className="h-4 w-4 text-primary" />
            <span>FastAPI Bearer Tokens</span>
          </h3>
          <span className="text-[11px] font-mono text-muted-foreground">Masked for Security</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Use this token for CLI deployments, CI/CD automated flashing, and direct backend API validation.
        </p>
        <div className="flex items-center gap-2">
          <Input
            readOnly
            value={`${apiToken.substring(0, 12)}••••••••••••••••••••••••`}
            className="font-mono text-xs bg-muted"
          />
          <Button size="icon" variant="outline" onClick={handleCopyToken} title="Copy Token">
            {copiedToken ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleRotateToken}
            disabled={rotating}
            className="gap-1.5 text-xs"
          >
            <RotateCw className={`h-3.5 w-3.5 ${rotating ? 'animate-spin' : ''}`} />
            <span>Rotate Key</span>
          </Button>
        </div>
      </div>

      {/* Password Management */}
      <form onSubmit={handleChangePassword} className="rounded-xl border border-border bg-card p-6 space-y-4">
        <h3 className="font-semibold text-base flex items-center gap-2">
          <Lock className="h-4 w-4 text-primary" />
          <span>Change Password</span>
        </h3>
        {passwordMsg && (
          <div className="text-xs text-emerald-500 font-semibold">{passwordMsg}</div>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Current Password
            </label>
            <Input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              New Password
            </label>
            <Input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </div>
        </div>
        <Button type="submit" size="sm">Update Password</Button>
      </form>

      {/* Theme Setting */}
      <div className="rounded-xl border border-border bg-card p-6 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-base">Interface Appearance</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Toggle between dark and light themes</p>
        </div>
        <ThemeToggle />
      </div>

      {/* Danger Zone */}
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-base text-destructive flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            <span>Delete Account</span>
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Permanently remove your account, spec versions, and provisioned device secrets.
          </p>
        </div>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setDeleteModalOpen(true)}
        >
          Delete Account
        </Button>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogHeader>
          <DialogTitle className="text-destructive">Are you absolutely sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. Type <strong className="text-foreground">DELETE</strong> to confirm permanent deletion.
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <Input
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            placeholder="Type DELETE"
            className="font-mono"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => setDeleteModalOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            disabled={deleteConfirmText !== 'DELETE'}
            onClick={handleDeleteAccount}
          >
            Permanently Delete
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}
