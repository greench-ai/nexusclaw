# NexusClaw UI Themes

10 built-in themes, switchable live from the header.

## Usage

Themes are CSS variable sets loaded via the theme switcher.
The active theme is stored in `ui.theme` in your config.

## Available Themes

| ID | Name | Style |
|----|------|-------|
| `aurora` | Aurora | Green / Purple / Orange — default NexusClaw |
| `midnight` | Midnight | Deep navy / cyan |
| `obsidian` | Obsidian | Black / red / silver |
| `arctic` | Arctic | White / ice blue |
| `ember` | Ember | Dark amber / orange glow |
| `matrix` | Matrix | Terminal black / green |
| `sakura` | Sakura | Soft pink / white / rose |
| `void` | Void | Pure dark / violet |
| `solar` | Solar | Warm white / gold |
| `stealth` | Stealth | Grey / charcoal / slate |

## Integration

In the NexusClaw UI, import the theme switcher:

```typescript
import { ThemeSwitcher } from './themes/switcher';

// Mount in header component
ThemeSwitcher.mount('#theme-switcher-container');

// Switch programmatically
ThemeSwitcher.set('midnight');

// Get active theme
ThemeSwitcher.active(); // → 'midnight'
```

## Adding Custom Themes

1. Copy `themes/aurora.css` as a template
2. Change the `data-theme` attribute value
3. Update all CSS variables
4. Add to `themes/index.ts` manifest
5. Theme will appear in the switcher automatically
