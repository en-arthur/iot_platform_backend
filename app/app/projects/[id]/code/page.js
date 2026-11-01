'use client';

import React, { useState, useEffect, use } from 'react';
import dynamic from 'next/dynamic';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import {
  FileCode2,
  FolderTree,
  ShieldCheck,
  Save,
  AlertTriangle,
  Loader2,
  Check,
  File,
} from 'lucide-react';

// Dynamically import Monaco Editor to avoid SSR window issues
const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

export default function CodeViewerPage({ params }) {
  const unwrappedParams = use(params);
  const projectId = unwrappedParams.id;

  const [files, setFiles] = useState([]);
  const [selectedFilePath, setSelectedFilePath] = useState('firmware/main.cpp');
  const [fileContent, setFileContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [showConflictDialog, setShowConflictDialog] = useState(false);

  useEffect(() => {
    async function loadFiles() {
      setLoading(true);
      try {
        const fileList = await api.getFiles(projectId);
        setFiles(fileList);
        const current = fileList.find((f) => f.path === selectedFilePath) || fileList[0];
        if (current) {
          setSelectedFilePath(current.path);
          setFileContent(current.content);
          setOriginalContent(current.content);
        }
      } finally {
        setLoading(false);
      }
    }
    loadFiles();
  }, [projectId]);

  const activeFile = files.find((f) => f.path === selectedFilePath);

  const handleSelectFile = (file) => {
    setSelectedFilePath(file.path);
    setFileContent(file.content);
    setOriginalContent(file.content);
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await api.updateFile(projectId, selectedFilePath, fileContent);
      setOriginalContent(fileContent);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const getLanguage = (path) => {
    if (path.endsWith('.cpp') || path.endsWith('.h')) return 'cpp';
    if (path.endsWith('.py')) return 'python';
    if (path.endsWith('.jsx') || path.endsWith('.js')) return 'javascript';
    if (path.endsWith('.json')) return 'json';
    return 'plaintext';
  };

  const hasUnsavedChanges = fileContent !== originalContent;
  const protectedRegions = activeFile?.protected_regions || [];

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-8.5rem)] overflow-hidden">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between border-b border-border bg-card px-4 py-2.5">
        <div className="flex items-center gap-3">
          <FileCode2 className="h-4 w-4 text-primary" />
          <span className="font-mono text-xs font-bold text-foreground">{selectedFilePath}</span>
          {hasUnsavedChanges && (
            <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" title="Unsaved changes" />
          )}
        </div>

        <div className="flex items-center gap-2">
          {protectedRegions.length > 0 && (
            <Badge variant="confirmed" className="gap-1.5 text-[11px] hidden sm:inline-flex">
              <ShieldCheck className="h-3 w-3 text-emerald-500" />
              <span>{protectedRegions.length} Protected Region(s) Preserved</span>
            </Badge>
          )}

          <Button
            size="sm"
            onClick={handleSave}
            disabled={!hasUnsavedChanges || saving}
            className="h-8 gap-1.5 text-xs shadow-sm"
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : saveSuccess ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span>Saved!</span>
              </>
            ) : (
              <>
                <Save className="h-3.5 w-3.5" />
                <span>Save Code</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Editor & File Tree Grid */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* Left Column: File Tree (Col 1-3) */}
        <div className="col-span-12 md:col-span-3 border-r border-border bg-card/50 flex flex-col overflow-y-auto">
          <div className="p-3 border-b border-border/80 text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <FolderTree className="h-3.5 w-3.5 text-primary" />
            <span>Generated File Tree</span>
          </div>

          <div className="p-2 space-y-1">
            {files.map((file) => {
              const isSelected = file.path === selectedFilePath;
              return (
                <button
                  key={file.path}
                  onClick={() => handleSelectFile(file)}
                  className={`w-full text-left p-2 rounded-lg text-xs font-mono transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-primary text-primary-foreground font-bold shadow-sm'
                      : 'text-foreground hover:bg-muted'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <File className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{file.path}</span>
                  </div>
                  <span className="text-[10px] opacity-75 capitalize shrink-0 ml-1">
                    {file.type}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Protected Region Info */}
          {protectedRegions.length > 0 && (
            <div className="m-3 p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5 text-xs space-y-1.5 mt-auto">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-600 dark:text-emerald-400">
                <ShieldCheck className="h-4 w-4" />
                <span>Protected Regions Active</span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Lines {protectedRegions[0].start_line} - {protectedRegions[0].end_line} contain protected user code. AI regeneration will not overwrite this section.
              </p>
            </div>
          )}
        </div>

        {/* Center/Right Column: Monaco Editor (Col 4-12) */}
        <div className="col-span-12 md:col-span-9 flex flex-col bg-slate-950">
          {loading ? (
            <div className="flex-1 flex items-center justify-center text-xs text-slate-400">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              <span>Loading Monaco editor...</span>
            </div>
          ) : (
            <Editor
              height="100%"
              theme="vs-dark"
              language={getLanguage(selectedFilePath)}
              value={fileContent}
              onChange={(value) => setFileContent(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                fontFamily: 'JetBrains Mono, Menlo, Monaco, Courier New, monospace',
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 2,
                wordWrap: 'on',
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
