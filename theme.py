"""Color palettes. `theme` below is the active one.

It's a plain dict on purpose, not a dataclass or anything fancier -
widgets just do theme["accent"] at paint time instead of caching a copy,
so swapping palettes is one dict.update() and everyone repaints in the
new colors on their own.
"""

THEMES = {

    "Malevolent Shrine": {
        "bg": "#070404", "panel": "#100808", "panel2": "#180a0a", "panel3": "#220d0d",
        "accent": "#e5142c", "accent2": "#8a1116", "accent3": "#ff5b6a",
        "green": "#22c55e", "yellow": "#eab308", "red": "#ff1e3c",
        "text": "#f2e0e0", "muted": "#6e4444", "border": "#341414", "glow": "#b91c1c",
        "alt_row": "#130707", "sakura": (200, 40, 45),
    },
    "Hollow Purple": {
        "bg": "#0a0812", "panel": "#0f0d1a", "panel2": "#161228", "panel3": "#1c1735",
        "accent": "#a78bfa", "accent2": "#f472b6", "accent3": "#67e8f9",
        "green": "#34d399", "yellow": "#fbbf24", "red": "#f87171",
        "text": "#e2d9f3", "muted": "#5b5280", "border": "#251f40", "glow": "#7c3aed",
        "alt_row": "#130f24", "sakura": (240, 170, 210),
    },
    "Aqua": {
        "bg": "#060d18", "panel": "#0a1525", "panel2": "#0f1e35", "panel3": "#152540",
        "accent": "#38bdf8", "accent2": "#818cf8", "accent3": "#34d399",
        "green": "#4ade80", "yellow": "#fbbf24", "red": "#fb7185",
        "text": "#e0f2fe", "muted": "#4a6080", "border": "#1e3a5f", "glow": "#0284c7",
        "alt_row": "#0d1a2e", "sakura": (150, 210, 255),
    },
    "Sakura Dawn": {
        "bg": "#1a0d0f", "panel": "#261318", "panel2": "#321a1f", "panel3": "#3d2028",
        "accent": "#fb7185", "accent2": "#f9a8d4", "accent3": "#fda4af",
        "green": "#86efac", "yellow": "#fde68a", "red": "#fca5a5",
        "text": "#fce7f3", "muted": "#9d6070", "border": "#5c2d38", "glow": "#e11d48",
        "alt_row": "#2a1419", "sakura": (255, 182, 193),
    },
    "Forest Elfs": {
        "bg": "#060f0a", "panel": "#0b1a11", "panel2": "#112317", "panel3": "#162d1e",
        "accent": "#4ade80", "accent2": "#a3e635", "accent3": "#67e8f9",
        "green": "#34d399", "yellow": "#fbbf24", "red": "#f87171",
        "text": "#dcfce7", "muted": "#3d6b4a", "border": "#1a4028", "glow": "#16a34a",
        "alt_row": "#0d1f13", "sakura": (180, 240, 190),
    },
    "Eye Burner": {
        "bg": "#f5f0ff", "panel": "#ffffff", "panel2": "#f0ebff", "panel3": "#e8e0ff",
        "accent": "#7c3aed", "accent2": "#db2777", "accent3": "#0891b2",
        "green": "#16a34a", "yellow": "#d97706", "red": "#dc2626",
        "text": "#1e1530", "muted": "#8b7aaa", "border": "#ddd6fe", "glow": "#7c3aed",
        "alt_row": "#f8f4ff", "sakura": (220, 170, 210),
    },
}

# default on launch - AniHighTaskManager.onThemeChanged swaps this out
# via theme.update() whenever someone picks something else from the dropdown
theme = dict(THEMES["Malevolent Shrine"])