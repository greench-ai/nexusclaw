<!--
  NexusClaw — Claude Preview Window Component
  Drop into: apps/ui/src/lib/components/ClaudePreview.svelte
  
  Shows live streaming response with token count, model, thinking level.
  Mount in the main chat layout alongside the message thread.
-->

<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  // ── Props ──────────────────────────────────────────────────────────────────
  export let gatewayWsUrl: string = 'ws://localhost:19789/ws';
  export let visible: boolean = true;

  // ── State ──────────────────────────────────────────────────────────────────
  let streaming = false;
  let currentText = '';
  let model = '';
  let thinkingLevel = '';
  let tokenCount = 0;
  let inputTokens = 0;
  let sessionId = 'main';
  let ws: WebSocket | null = null;
  let containerEl: HTMLElement;

  const THINKING_LABELS: Record<string, string> = {
    off: 'off', minimal: 'min', low: 'low',
    medium: 'med', high: 'high', xhigh: 'max',
  };

  // ── WebSocket ──────────────────────────────────────────────────────────────
  function connect() {
    ws = new WebSocket(gatewayWsUrl);
    ws.onopen = () => console.log('[NexusClaw Preview] WS connected');
    ws.onclose = () => setTimeout(connect, 3000);
    ws.onerror = () => ws?.close();

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (_) {}
    };
  }

  function handleMessage(msg: any) {
    switch (msg.type) {
      case 'stream.start':
        streaming = true;
        currentText = '';
        tokenCount = 0;
        model = msg.model ?? '';
        thinkingLevel = msg.thinkingLevel ?? '';
        sessionId = msg.session ?? 'main';
        break;

      case 'stream.delta':
        currentText += msg.delta ?? '';
        tokenCount = msg.tokens ?? tokenCount;
        // Auto-scroll
        if (containerEl) {
          containerEl.scrollTop = containerEl.scrollHeight;
        }
        break;

      case 'stream.end':
        streaming = false;
        tokenCount = msg.totalTokens ?? tokenCount;
        inputTokens = msg.inputTokens ?? 0;
        break;

      case 'stream.error':
        streaming = false;
        currentText += `\n\n⚠ Error: ${msg.error}`;
        break;
    }
  }

  onMount(() => {
    if (visible) connect();
  });

  onDestroy(() => {
    ws?.close();
  });

  // Toggle visibility
  function toggle() { visible = !visible; }

  // Clear preview
  function clear() { currentText = ''; tokenCount = 0; streaming = false; }
</script>

{#if visible}
<div class="claude-preview" class:streaming>
  <!-- Header -->
  <div class="preview-header">
    <div class="preview-title">
      <span class="indicator" class:active={streaming}></span>
      Preview
      {#if sessionId !== 'main'}
        <span class="session-tag">{sessionId}</span>
      {/if}
    </div>
    <div class="preview-meta">
      {#if model}
        <span class="meta-chip model">{model.split('/').pop()}</span>
      {/if}
      {#if thinkingLevel && thinkingLevel !== 'off'}
        <span class="meta-chip thinking">🧠 {THINKING_LABELS[thinkingLevel] ?? thinkingLevel}</span>
      {/if}
      {#if tokenCount > 0}
        <span class="meta-chip tokens">↑{inputTokens} ↓{tokenCount}</span>
      {/if}
    </div>
    <div class="preview-actions">
      <button class="btn-icon" on:click={clear} title="Clear">✕</button>
      <button class="btn-icon" on:click={toggle} title="Hide">−</button>
    </div>
  </div>

  <!-- Content -->
  <div class="preview-content" bind:this={containerEl}>
    {#if currentText}
      <pre class="preview-text">{currentText}{#if streaming}<span class="cursor">▋</span>{/if}</pre>
    {:else}
      <div class="preview-empty">
        {#if streaming}
          <span class="loading">Generating...</span>
        {:else}
          <span>Preview will appear here during response generation.</span>
        {/if}
      </div>
    {/if}
  </div>
</div>
{:else}
  <!-- Collapsed pill -->
  <button class="preview-pill" on:click={toggle}>
    <span class="indicator" class:active={streaming}></span>
    Preview
  </button>
{/if}

<style>
  .claude-preview {
    display: flex;
    flex-direction: column;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    overflow: hidden;
    height: 100%;
    min-height: 200px;
    font-family: var(--font-ui);
    transition: border-color 0.2s;
  }

  .claude-preview.streaming {
    border-color: var(--accent-primary);
    box-shadow: var(--glow);
  }

  .preview-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .preview-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    flex: 1;
  }

  .indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-muted);
    flex-shrink: 0;
    transition: all 0.3s;
  }

  .indicator.active {
    background: var(--accent-primary);
    box-shadow: 0 0 6px var(--accent-primary);
    animation: pulse 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .session-tag {
    font-size: 9px;
    background: var(--accent-muted);
    color: var(--accent-primary);
    padding: 1px 5px;
    border-radius: 3px;
  }

  .preview-meta {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .meta-chip {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 3px;
    background: var(--bg-base);
    border: 1px solid var(--border);
  }

  .meta-chip.model  { color: var(--accent-secondary); }
  .meta-chip.thinking { color: var(--accent-tertiary); }
  .meta-chip.tokens { color: var(--text-secondary); }

  .preview-actions {
    display: flex;
    gap: 4px;
  }

  .btn-icon {
    width: 22px;
    height: 22px;
    background: none;
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
  }
  .btn-icon:hover {
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }

  .preview-content {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    scrollbar-width: thin;
    scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
  }

  .preview-text {
    font-family: var(--font-ui);
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-primary);
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
  }

  .cursor {
    color: var(--accent-primary);
    animation: blink 0.8s step-end infinite;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  .preview-empty {
    font-size: 12px;
    color: var(--text-muted);
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    line-height: 1.6;
  }

  .loading {
    color: var(--accent-primary);
    animation: pulse 1s ease-in-out infinite;
  }

  .preview-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    color: var(--text-muted);
    font-family: var(--font-ui);
    font-size: 11px;
    cursor: pointer;
    transition: all 0.18s;
  }

  .preview-pill:hover {
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }
</style>
