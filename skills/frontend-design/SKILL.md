---
name: frontend-design
description: Generate bold, production-grade UI components and pages with real aesthetic intent. Forces past generic AI output into distinctive, professional interfaces.
version: 1.0.0
metadata:
  openclaw:
    requires: {}
---

# Frontend Design

Creates distinctive, production-ready UI — not generic AI slop.
React, HTML/CSS, Tailwind, Svelte. Dark themes, cannabis aesthetics, cyberpunk, clean minimal.
Matches the visual identity of GreenchClaw and NexusClaw.

## Usage

```
Design a login page for GreenchClaw
Create a dashboard component for NexusClaw
Build a skill card UI
Design a dark theme settings panel
Create a cannabis-themed UI component
Make a status indicator widget
```

## Design principles

**Always apply:**
- Dark backgrounds (#0a0d12 or similar deep dark)
- Real visual hierarchy — not flat same-weight text
- Micro-interactions and hover states
- Consistent spacing system (4px/8px/16px/24px/32px)
- Meaningful use of color (not rainbow soup)
- Readable at all sizes

**Never do:**
- Purple gradient on white as the only design
- Generic blue buttons with no personality
- Flat list of items with no visual grouping
- Times New Roman or default browser fonts
- 100% width containers with no max-width
- Missing focus states on interactive elements

## GreenchClaw design tokens

```css
--gc-bg-base: #0a1a0d;
--gc-bg-surface: #0f2414;
--gc-bg-elevated: #1a3420;
--gc-accent-primary: #00cc44;
--gc-accent-secondary: #7b2d8b;
--gc-accent-cannabis: #4a7c3f;
--gc-text-primary: #e8f5e9;
--gc-text-secondary: #81c784;
--gc-text-muted: #4a7c3f;
--gc-border: #1a3420;
--gc-border-active: #00cc44;
--gc-glow: 0 0 20px rgba(0,204,68,0.3);
```

## NexusClaw design tokens

```css
--nx-bg-base: #0a0d12;
--nx-bg-surface: #111620;
--nx-bg-elevated: #1a2030;
--nx-accent-primary: #00ff88;
--nx-accent-secondary: #9b59ff;
--nx-accent-tertiary: #ff7d3b;
--nx-text-primary: #e8f0fe;
--nx-text-secondary: #8899aa;
--nx-border: #1e2d40;
--nx-glow: 0 0 20px rgba(0,255,136,0.25);
```

## Component patterns

**Cards:**
- Rounded corners (8-12px)
- Subtle border (1px solid var(--border))
- Hover: border changes to accent color + subtle glow
- Always have padding (16-24px)

**Buttons:**
- Primary: solid accent background, dark text
- Secondary: outlined, accent border + text
- Danger: red (#ff4466) — only for destructive actions
- Always have hover + active + focus states

**Status indicators:**
- Green dot (pulsing animation) = active/healthy
- Yellow dot = warning
- Red dot = error/offline
- Grey dot = unknown/disabled

**Data tables:**
- Zebra striping with subtle bg difference
- Sticky header with blur backdrop
- Sortable columns with directional arrow
- Row hover highlight

## Output format

Always provide:
1. Complete, copy-pasteable component code
2. CSS variables at the top
3. Comments explaining key design decisions
4. Responsive breakpoints if needed

For React: use functional components with hooks
For HTML: include all CSS inline in `<style>` tag
For Svelte: include `<style>` section with scoped CSS

## Cannabis theme guidelines

When designing for GreenchClaw:
- Use deep greens and purples as primary palette
- Subtle leaf/organic shapes in decorative elements
- Glow effects in cannabis green (#00cc44)
- Never make it look cheap or drug-related — keep it sophisticated
- Think: premium botanical, not head shop
