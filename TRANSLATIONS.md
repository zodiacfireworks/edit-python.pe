# Translation Workflow

This project uses `pybabel` for translations, completely managed through `poethepoet` (poe) tasks.
The translation files are packaged internally within `src/edit_python_pe/locale/` so they are automatically included in PyPI wheel distributions.

## General Workflow

### 1. Generating or Updating `.po` files (`makemessages`)
When you add new `_("...")` strings in the source code, run:
```bash
uv run poe makemessages
```
This automatically extracts all translation strings from `src/edit_python_pe/` into `messages.pot` and **updates all existing locales** (e.g. `es`, `fr`, etc.) with the new strings, keeping existing translations intact.

### 2. Compiling `.mo` files (`compilemessages`)
After you finish translating the `.po` files, you must compile them into the binary `.mo` format so the application can read them.
```bash
uv run poe compilemessages
```
This command compiles all languages in the `locale` directory simultaneously.

---

## Adding a New Language

If you want to add an entirely new language (for example, German `de`), use the `messages:init` command:
```bash
uv run poe messages:init --lang de
```
This extracts the strings and initializes the completely new directory `src/edit_python_pe/locale/de/LC_MESSAGES/messages.po`.

---

## Auto-Translating via Google Translate

The project includes an automatic translation script (`bin/translate.py`) powered by `deep-translator`. If you wish to automatically translate an existing `.po` file (e.g. for French `fr`), run:
```bash
uv run poe messages:translate --lang fr
```
*Note: This will overwrite empty `msgstr` entries in the `.po` file using Google Translate. Remember to run `poe compilemessages` after doing this to generate the updated `.mo` file!*
