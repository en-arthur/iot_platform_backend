'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';

/**
 * Reusable Hook for Server-Sent Events (SSE) with cancellation, reconnect, and typed handlers.
 *
 * @param {Object} options
 * @param {Function} [options.onToken] - (token: string) => void
 * @param {Function} [options.onQuestion] - (question: string) => void
 * @param {Function} [options.onSpecProposal] - (proposal: object) => void
 * @param {Function} [options.onToolCall] - (toolCall: object) => void
 * @param {Function} [options.onLog] - (logMessage: string) => void
 * @param {Function} [options.onStatus] - (status: string) => void
 * @param {Function} [options.onError] - (error: any) => void
 * @param {Function} [options.onDone] - () => void
 */
export function useEventStream(options = {}) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);
  const mockTimerRef = useRef(null);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (mockTimerRef.current) {
      clearTimeout(mockTimerRef.current);
      mockTimerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const startStream = useCallback(
    async (url, body = {}, mockType = 'chat') => {
      cancel();
      setIsStreaming(true);
      setError(null);

      // Simulation mode when NEXT_PUBLIC_USE_MOCKS=true
      if (USE_MOCKS) {
        simulateMockStream(mockType, body, options, setIsStreaming, mockTimerRef);
        return;
      }

      // Real SSE execution via fetch + ReadableStream
      abortControllerRef.current = new AbortController();
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          body: JSON.stringify(body),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`SSE stream failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim()) continue;
            let eventType = 'message';
            let dataStr = '';

            const subLines = line.split('\n');
            for (const sub of subLines) {
              if (sub.startsWith('event:')) {
                eventType = sub.replace('event:', '').trim();
              } else if (sub.startsWith('data:')) {
                dataStr = sub.replace('data:', '').trim();
              }
            }

            try {
              const data = dataStr ? JSON.parse(dataStr) : null;
              dispatchTypedEvent(eventType, data, options);
            } catch {
              dispatchTypedEvent(eventType, dataStr, options);
            }
          }
        }

        if (options.onDone) options.onDone();
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message);
          if (options.onError) options.onError(err);
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [cancel, options]
  );

  useEffect(() => {
    return () => cancel();
  }, [cancel]);

  return {
    isStreaming,
    error,
    startStream,
    cancel,
  };
}

/**
 * Dispatch typed event to configured callbacks
 */
function dispatchTypedEvent(type, payload, options) {
  switch (type) {
    case 'token':
      options.onToken?.(payload?.token || payload);
      break;
    case 'question':
      options.onQuestion?.(payload);
      break;
    case 'spec_proposal':
      options.onSpecProposal?.(payload);
      break;
    case 'tool_call':
      options.onToolCall?.(payload);
      break;
    case 'log':
      options.onLog?.(payload?.message || payload);
      break;
    case 'status':
      options.onStatus?.(payload?.status || payload);
      break;
    case 'error':
      options.onError?.(payload);
      break;
    case 'done':
      options.onDone?.();
      break;
    default:
      if (options.onToken && typeof payload === 'string') {
        options.onToken(payload);
      }
  }
}

/**
 * Mock stream runner for development & testing
 */
function simulateMockStream(type, body, options, setIsStreaming, mockTimerRef) {
  const steps = [];

  if (type === 'chat') {
    const userPrompt = body.message || 'Optimize power budget';
    const tokens = [
      `I analyzed your hardware profile regarding "${userPrompt}". `,
      'The BME280 sensor draws ~3.6 μA in ultra-low-power mode. ',
      'However, I detected an electrical collision on GPIO4 between your tactile push button and the I2C SDA line. ',
      'I recommend reassigning the tactile button to GPIO10 and updating the target deployment schedule. ',
      'Here is the formal proposal for your review:'
    ];

    tokens.forEach((t) => steps.push({ type: 'token', payload: { token: t }, delay: 250 }));
    steps.push({
      type: 'spec_proposal',
      payload: {
        proposal_id: 'prop-fix-pin-conflict',
        summary: 'Remap Push Button to GPIO10 to resolve I2C SDA collision and confirm schedule',
        changes: [
          {
            path: 'peripherals.manual_override_button_pin',
            old: 'GPIO4',
            new: 'GPIO10',
            reason: 'Eliminate electrical bus lockup by moving button to open GPIO10.',
          },
          {
            path: 'metadata.target_deployment_date',
            old: null,
            new: '2026-12-01',
            reason: 'Default target milestone schedule to clear completeness gate.',
          },
        ],
      },
      delay: 400,
    });
    steps.push({
      type: 'question',
      payload: 'Would you like to activate deep sleep wake on button press via RTC GPIO10 as well?',
      delay: 300,
    });
    steps.push({ type: 'done', payload: {}, delay: 100 });
  } else if (type === 'generate') {
    steps.push({ type: 'status', payload: { status: 'Synthesizing ESP-IDF C++ firmware...' }, delay: 300 });
    steps.push({ type: 'log', payload: 'Configuring I2C bus driver at 400kHz with SDA=GPIO4, SCL=GPIO5', delay: 300 });
    steps.push({ type: 'status', payload: { status: 'Compiling FastAPI ingestion schemas...' }, delay: 400 });
    steps.push({ type: 'log', payload: 'Bound commands TRIGGER_FAN_FORCE_ON and REBOOT_NODE', delay: 300 });
    steps.push({ type: 'status', payload: { status: 'Generating Web App control bundle...' }, delay: 400 });
    steps.push({ type: 'done', payload: {}, delay: 100 });
  } else if (type === 'deploy') {
    steps.push({ type: 'status', payload: { status: 'Provisioning secure device credentials...' }, delay: 300 });
    steps.push({ type: 'log', payload: 'Issued ECDSA P-256 client certificate', delay: 300 });
    steps.push({ type: 'status', payload: { status: 'Deploying cloud ingestion containers...' }, delay: 400 });
    steps.push({ type: 'log', payload: 'Subscribed to MQTT broker at mqtt.iotbuilder.cloud:8883', delay: 300 });
    steps.push({ type: 'status', payload: { status: 'Live deployment ready!' }, delay: 200 });
    steps.push({ type: 'done', payload: {}, delay: 100 });
  }

  let index = 0;
  function next() {
    if (index >= steps.length) {
      setIsStreaming(false);
      options.onDone?.();
      return;
    }
    const item = steps[index++];
    dispatchTypedEvent(item.type, item.payload, options);
    mockTimerRef.current = setTimeout(next, item.delay);
  }

  mockTimerRef.current = setTimeout(next, 100);
}
