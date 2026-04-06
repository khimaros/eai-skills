# eai-skills

skills for the [google ai edge gallery](https://github.com/google-ai-edge/gallery).

## persona

a self-evolving, long-lived persona backed by `localStorage`. stores
markdown traits, JSON data, JSONL event streams, and user-defined
JavaScript hooks. auto-loads any trait whose name matches `ALL_CAPS.ext`
as part of the system prompt at session start.

**load it in the gallery from:**

```
https://khimaros.github.io/eai-skills/persona/
```

verify with `https://khimaros.github.io/eai-skills/persona/SKILL.md`.

## layout

```
persona/
  SKILL.md              # skill manifest read by the gallery
  scripts/index.html    # webview backend (built artifact)
  workspace/            # source of truth for default ALL_CAPS traits
    SOUL.md
    VOICE.md
    STYLE.md
build/build.py          # bakes workspace/*.md into scripts/index.html
Makefile
```

## development

edit traits in `persona/workspace/`, then rebuild:

```
make
```

this regenerates the embedded JSON block in `persona/scripts/index.html`.
commit both the workspace source and the built `index.html`.

## hosting

served via github pages from `master` branch root. `.nojekyll` at the
repo root disables jekyll so files are served as-is, which is required
by the gallery's skill loader.
