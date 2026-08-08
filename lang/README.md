# Translations folder

This directory contains translation templates and the English source file for the bot UI texts.

Files:
- eng.json — English strings (used as default reference)
- translate-example.conf — a template listing all translation keys (empty values). Copy this file to create new translations (e.g. `lang/de.conf`) and fill in the translated values.
- .gitkeep — placeholder so the folder is visible in Git

How to add a new language
1. Copy `lang/translate-example.conf` to `lang/<lang>.conf` (e.g. `lang/de.conf`) and add your translations after the `=` for each key.
   - Keep the keys unchanged.
   - Preserve placeholders like `{page}`, `{name}`, `{time}`.
2. Or create a JSON file `lang/<lang>.json` with the same keys as in `eng.json`.
3. Run the setup CLI and choose the desired language/file, or set `translations.file=lang/<lang>.conf` and `translations.language=<lang>` in `config.properties`.

Notes
- JSON files are preferred by the bot if the `translations.file` ends with `.json`.
- The bot will fallback to the English string if a key is missing.
