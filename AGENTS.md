# Bildblick project instructions

## Required design reference

For every new or modified user interface in this repository:

1. Read `design-system/DESIGN.md` and inspect the matching examples in `design-system/index.html` before editing UI code.
2. Follow `design-system/tokens.json` for colors, spacing, typography and shape. Reuse `ui_theme.py`, `ChoiceButtons`, `SliderField` and `ToolDialog` where applicable.
3. Keep effects and finite visual variants directly selectable. Use sliders for continuous visual parameters, exact numeric inputs for dimensions, and meaningful symbols with labels for drawing tools.
4. If a required component or interaction pattern is missing, add it to the design reference first. Keep the contract, examples, tokens and affected GTK implementation consistent.
5. Verify relevant normal, focus, disabled, loading, empty and error states, keyboard operation, and compact window layouts. State any unverified platform limitations honestly.

The app remains native GTK. The HTML/CSS/TypeScript site is the local design contract and component gallery. It does not automatically migrate existing dialogs. Native file, font, color and print dialogs may retain system styling. Explicit user instructions take precedence.
