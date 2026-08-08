# UniversalConverter — UI Redesign & Rename

**Date:** 2026-08-08
**Status:** Approved
**Product name:** UniversalConverter (was OmniConvert)
**License:** MIT (public GitHub repo)

## 1. Purpose

Rebrand and visually redesign the existing OmniConvert desktop app so it is easier
to find and nicer to use:

- Rename the product, repository, EXE, window title, log file, and README to
  **UniversalConverter** so it matches what users search for ("universal converter").
- Replace the tabbed window with a sidebar-navigation layout, category accent
  colors, icons, a polished converter panel, and a searchable Formats page.
- Keep 100% of the conversion core, offline behavior, and the test suite untouched.

## 2. Rename Scope (searchability)

| Surface | Old | New |
|---|---|---|
| App/window title | OmniConvert | UniversalConverter |
| EXE | `dist/OmniConvert.exe` | `dist/UniversalConverter.exe` |
| Log file | `omni-convert.log` | `universal-converter.log` |
| Build script | `--name OmniConvert` in build.ps1 | `--name UniversalConverter` |
| PDF metadata | "OmniConvert" | "UniversalConverter" |
| GitHub repo (renamed, old URL redirects) | `TT88990/omni-convert` | `TT88990/universal-converter` |
| Test fixtures | "Hello OmniConvert!" | "Hello UniversalConverter!" |
| Release | v0.1.0 (archive, keep) | **v0.2.0** with new EXE + new notes |
| Repo topics (added) | — | converter, file-converter, image-converter, pdf, ffmpeg, python, windows, offline |

Historical files (`docs/superpowers/...`) keep original content — they are a
record of the project.

## 3. Layout & Navigation

- Window 1100×760, min size 900×600, dark theme, blue default accent.
- Left sidebar (~220px), constant across pages:
  - Brand block: icon tile + "UniversalConverter" + subtitle "Offline converter".
  - Nav buttons: Images, Documents, Audio, Video, Text, Hash, Formats —
    each with a category icon; active button shows a category-colored accent bar.
  - Footer: version badge (v0.2.0) + MIT note.
- Content area right: swaps between pages; no top tab row.

## 4. Shared Converter Page (Images/Documents/Audio/Video/Text)

- Header: page title + one-line description.
- Drop zone: dashed-border card, "Drag files here or click to add".
  When files exist it lists rows: extension badge (category accent) + file name + size.
  Invalid extensions for the category are skipped with a log note (core behavior unchanged).
- Action row: Output folder (entry + Browse), target format dropdown,
  Convert button in category accent (larger hit area).
- Status: progress bar + live line `3/4 converting intro.mp3 -> gif`.
- Log pane: monospace, smaller text, auto-scroll; still written to
  `universal-converter.log` by Runner (core untouched).

Category accents: Images=amber, Documents=blue, Audio=green, Video=pink,
Text=purple, Hash=teal, Formats=slate gray (#64748B). Default accent = #3B82F6.

## 5. Hash & Formats Pages

- Hash: same interaction (text/file mode, per-hash copy buttons, live refresh),
  restyled; file mode shows the hashed file name.
- Formats: searchable — filter entry live-filters every `src -> targets` row;
  category section headers with accent.

## 6. Theme & Icons

- New `omni/theme.py`: THEME dict — surfaces, text, accents per category, fonts,
  radius, spacing. Every widget reads from THEME (no hardcoded colors).
- New `omni/icons.py`: PIL-drawn pictograms (photo, document, music note, play
  triangle, "T", hash, grid) colored per category; rendered to PhotoImage at
  startup. No emoji, no external asset files.

## 7. Error Handling / Testing / Build

- Unchanged core: converters, runner, hashing, worker-thread progress.
- Tests: existing 66 tests keep passing (fixture strings updated); new tests:
  - `test_theme.py`: THEME exposes every key widgets need.
  - `test_icons.py`: every category yields a non-empty RGBA icon.
  - Extended selftest (`main.py --selftest`): app opens, all 7 pages exist,
    sidebar nav count == 7, drop of a fixture file populates a page.
- Build: `build.ps1` (pytest gate → PyInstaller onefile → `dist/UniversalConverter.exe`).

## 8. Publishing

1. Rename repo `gh repo rename universal-converter` (redirect automatic).
2. Rebuild EXE, verify `--selftest` OK.
3. New release **v0.2.0** "UniversalConverter — renamed, new sidebar UI"
   with `UniversalConverter.exe`.
4. Re-upload nothing to v0.1.0 (kept as archive); old links redirect.
5. Add repo topics (list above).

## 9. Out of Scope (YAGNI)

- Sidebar collapse, settings/preferences dialog, i18n/translations, update checker,
  light theme, real multi-process conversion, drag-reorder of files, history.