// NexusClaw — Theme Switcher
// Drop into NexusClaw UI: apps/ui/src/lib/components/ThemeSwitcher.ts

export const THEMES = [
  { id: 'aurora',   name: 'Aurora',   preview: ['#00ff88', '#9b59ff', '#ff7d3b'], dark: true  },
  { id: 'midnight', name: 'Midnight', preview: ['#00d4ff', '#4a9eff', '#7c3aed'], dark: true  },
  { id: 'obsidian', name: 'Obsidian', preview: ['#ff2244', '#cccccc', '#aa4422'], dark: true  },
  { id: 'arctic',   name: 'Arctic',   preview: ['#0066ff', '#00aacc', '#6633ff'], dark: false },
  { id: 'ember',    name: 'Ember',    preview: ['#ff8c00', '#ff4500', '#ffcc00'], dark: true  },
  { id: 'matrix',   name: 'Matrix',   preview: ['#00ff41', '#00cc33', '#008f11'], dark: true  },
  { id: 'sakura',   name: 'Sakura',   preview: ['#e05573', '#f48fb1', '#c2185b'], dark: false },
  { id: 'void',     name: 'Void',     preview: ['#bb44ff', '#7700ff', '#ff44bb'], dark: true  },
  { id: 'solar',    name: 'Solar',    preview: ['#c8920a', '#e8a820', '#9a6800'], dark: false },
  { id: 'stealth',  name: 'Stealth',  preview: ['#777777', '#999999', '#555555'], dark: true  },
] as const;

export type ThemeId = typeof THEMES[number]['id'];

const STORAGE_KEY = 'nexusclaw-theme';
const DEFAULT_THEME: ThemeId = 'aurora';

export const ThemeSwitcher = {
  /** Apply theme to document root */
  set(id: ThemeId): void {
    document.documentElement.setAttribute('data-theme', id);
    localStorage.setItem(STORAGE_KEY, id);
    document.dispatchEvent(new CustomEvent('nexusclaw:theme-change', { detail: { theme: id } }));
  },

  /** Get active theme id */
  active(): ThemeId {
    return (document.documentElement.getAttribute('data-theme') as ThemeId) ?? DEFAULT_THEME;
  },

  /** Load theme from localStorage or default */
  init(): void {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
    const valid = THEMES.find(t => t.id === saved);
    ThemeSwitcher.set(valid ? saved! : DEFAULT_THEME);
  },

  /** Mount switcher widget into a container element */
  mount(selector: string): void {
    const container = document.querySelector(selector);
    if (!container) return;

    const active = ThemeSwitcher.active();

    container.innerHTML = `
      <div class="nexusclaw-theme-switcher" role="listbox" aria-label="Select theme">
        ${THEMES.map(t => `
          <button
            class="theme-btn ${t.id === active ? 'active' : ''}"
            data-theme-id="${t.id}"
            role="option"
            aria-selected="${t.id === active}"
            title="${t.name}"
          >
            <span class="theme-dots">
              ${t.preview.map(c => `<span class="dot" style="background:${c}"></span>`).join('')}
            </span>
            <span class="theme-name">${t.name}</span>
          </button>
        `).join('')}
      </div>
    `;

    container.querySelectorAll<HTMLButtonElement>('.theme-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.themeId as ThemeId;
        ThemeSwitcher.set(id);
        container.querySelectorAll('.theme-btn').forEach(b => {
          b.classList.toggle('active', b === btn);
          b.setAttribute('aria-selected', String(b === btn));
        });
      });
    });
  },
};

// ─── Switcher CSS ──────────────────────────────────────────────────────────────
export const SWITCHER_CSS = `
.nexusclaw-theme-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 11px;
  transition: all var(--transition);
  white-space: nowrap;
}

.theme-btn:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
  background: var(--bg-hover);
}

.theme-btn.active {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  background: var(--accent-muted);
}

.theme-dots {
  display: flex;
  gap: 3px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
`;
