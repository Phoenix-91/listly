# ToDo — Glassmorphism Dark UI Edition

A Python + Tkinter To-Do List app styled after a modern glassmorphism dashboard: dark background, soft rounded "glass" cards, a sidebar with filters and category counts, colored category badges, and smooth hover interactions.

## Features

- Add tasks with **category** (Work / Personal / Study / Health) and an optional **due date** label
- Rounded, glass-style task cards with a soft top sheen
- Hover a task to reveal its delete (🗑) button — no clutter until you need it
- Circular checkbox toggle with animated fill on completion
- Sidebar navigation: **All / Pending / Completed**, with live counts
- Per-category counters in the sidebar
- Header stats line: total / pending / completed
- All data saved instantly to `tasks.json` — persists across restarts
- No external libraries — pure Python standard library (`tkinter`, `json`)

## Run it

```
python todo_app.py
```

Requires Python 3.7+ with Tkinter (bundled with standard Python installers).

## Notes on the "glass" effect

Tkinter has no native blur/transparency for widgets, so the glassmorphism look is simulated with:
- Rounded-corner `Canvas` panels (`GlassCard` class) drawn as smooth polygons
- Layered, slightly-lighter background tones to mimic translucency
- A thin top highlight line on each card for a subtle sheen
- Soft color blending (`mix()` helper) for hover states and category badge backgrounds

## Project structure

```
todo_app/
├── todo_app.py   # Entire app: data layer + UI
├── tasks.json     # Auto-created after your first saved task
└── README.md
```
