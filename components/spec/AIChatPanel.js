'use client';

import React, { useState } from 'react';
import { useEventStream } from '@/lib/hooks/useEventStream';
import { useSpecStore } from '@/lib/store/useSpecStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Sparkles,
  Send,
  Loader2,
  Check,
  X,
  HelpCircle,
  AlertTriangle,
  ArrowRight,
  StopCircle,
} from 'lucide-react';

export function AIChatPanel({ projectId }) {
  const { spec, activeProposal, setActiveProposal, approveProposal, rejectProposal, isSaving } = useSpecStore();

  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hello! I am your Hardware Specification Agent. I ensure your pinouts, power budgets, and commands are consistent. Ask me to resolve pin collisions, adjust sample rates, or add peripherals.',
    },
  ]);
  const [clarifyingQuestion, setClarifyingQuestion] = useState(null);

  const { isStreaming, startStream, cancel } = useEventStream({
    onToken: (token) => {
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'assistant' && last.isStreaming) {
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + token },
          ];
        }
        return [...prev, { role: 'assistant', content: token, isStreaming: true }];
      });
    },
    onQuestion: (question) => {
      setClarifyingQuestion(question);
    },
    onSpecProposal: (proposal) => {
      setActiveProposal(proposal);
    },
    onDone: () => {
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.isStreaming) {
          return [...prev.slice(0, -1), { ...last, isStreaming: false }];
        }
        return prev;
      });
    },
  });

  const handleSend = (textToSend = prompt) => {
    if (!textToSend.trim() || isStreaming) return;

    setMessages((prev) => [...prev, { role: 'user', content: textToSend }]);
    setPrompt('');
    setClarifyingQuestion(null);

    startStream('/api/v1/projects/' + projectId + '/chat', { message: textToSend }, 'chat');
  };

  const handleAnswerQuestion = (answer) => {
    handleSend(`Regarding "${clarifyingQuestion}": ${answer}`);
    setClarifyingQuestion(null);
  };

  return (
    <div className="flex flex-col h-full bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border p-3.5">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-xs font-bold text-foreground">AI Spec Engineer</span>
        </div>
        <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-mono font-medium">
          SSE Stream
        </span>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col text-xs ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-[88%] rounded-xl p-3 leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-muted/60 text-foreground border border-border/80'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Inline Clarifying Question Card */}
        {clarifyingQuestion && (
          <div className="rounded-xl border border-primary/30 bg-primary/5 p-3.5 space-y-3 animate-in fade-in">
            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
              <HelpCircle className="h-4 w-4 shrink-0" />
              <span>Clarification Required</span>
            </div>
            <p className="text-xs text-foreground/90">{clarifyingQuestion}</p>
            <div className="flex gap-2 pt-1">
              <Button
                size="sm"
                variant="outline"
                className="text-xs h-7"
                onClick={() => handleAnswerQuestion('Yes, enable RTC wake')}
              >
                Yes, enable RTC wake
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs h-7"
                onClick={() => handleAnswerQuestion('No, standard GPIO only')}
              >
                No, standard only
              </Button>
            </div>
          </div>
        )}

        {/* AI Spec Proposal Review Card */}
        {activeProposal && (
          <div className="rounded-xl border-2 border-primary/40 bg-card p-4 shadow-lg space-y-3.5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-border/60 pb-2">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>AI Proposed Spec Changes</span>
              </span>
              <Badge variant="inferred">Requires Sign-off</Badge>
            </div>

            <p className="text-xs text-muted-foreground">{activeProposal.summary}</p>

            {/* Changes list */}
            <div className="space-y-2 bg-muted/40 p-2.5 rounded-lg border border-border/60 font-mono text-[11px]">
              {activeProposal.changes.map((c, i) => (
                <div key={i} className="space-y-0.5 border-b border-border/40 last:border-0 pb-1.5 last:pb-0">
                  <div className="text-primary font-semibold">{c.path}</div>
                  <div className="text-slate-400 line-through">Old: {String(c.old ?? 'None')}</div>
                  <div className="text-emerald-500 font-bold">New: {String(c.new)}</div>
                  <div className="text-[10px] text-muted-foreground font-sans mt-0.5">{c.reason}</div>
                </div>
              ))}
            </div>

            {/* Approve / Reject Buttons */}
            <div className="flex items-center justify-end gap-2 pt-1">
              <Button
                size="sm"
                variant="outline"
                onClick={() => rejectProposal(projectId, activeProposal.proposal_id)}
                disabled={isSaving}
                className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-destructive"
              >
                <X className="h-3.5 w-3.5" />
                <span>Reject</span>
              </Button>
              <Button
                size="sm"
                onClick={() => approveProposal(projectId, activeProposal.proposal_id)}
                disabled={isSaving}
                className="h-8 gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                {isSaving ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <>
                    <Check className="h-3.5 w-3.5" />
                    <span>Approve & Bump Version</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-border bg-card/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <Input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask AI to resolve pin conflicts or edit specs..."
            disabled={isStreaming}
            className="text-xs h-9"
          />
          {isStreaming ? (
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={cancel}
              className="h-9 w-9 text-destructive"
              title="Stop streaming"
            >
              <StopCircle className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="submit" size="icon" disabled={!prompt.trim()} className="h-9 w-9">
              <Send className="h-4 w-4" />
            </Button>
          )}
        </form>
      </div>
    </div>
  );
}
