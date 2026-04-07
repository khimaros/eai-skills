# persona

a self-evolving, long-lived persona for the [google ai edge gallery](https://github.com/google-ai-edge/gallery).
state lives in the skill webview's `localStorage` across three namespaces:

- **traits** — markdown documents (voice, values, identity, knowledge of the user)
- **data** — JSON values for structured facts
- **hooks** — user-defined JavaScript sub-actions the persona can register at runtime

traits whose name matches `^[A-Z0-9_]+\.[a-z]+$` (e.g. `IDENTITY.md`,
`SOUL.md`, `VOICE.md`, `USER.md`) are auto-loaded at session
start by `persona_bootstrap` and treated as system-prompt-level identity.
all other traits are evolving scratch space the persona updates over time.

**load it in the gallery from:**

```
https://khimaros.github.io/eai-skills/persona/
```

verify with `https://khimaros.github.io/eai-skills/persona/SKILL.md`.

## layout

```
persona/
  SKILL.md           # skill manifest read by the gallery
  README.md          # this file (rendered to persona/index.html)
  scripts/
    index.html       # webview backend (built artifact)
  workspace/         # source of truth for default ALL_CAPS traits
    IDENTITY.md
    SOUL.md
    VOICE.md
    BOOTSTRAP.md
```

## defaults

the files in `workspace/` are the source of truth for the persona's
seeded identity. they are baked into `scripts/index.html` at build time
and copied into `localStorage` on the very first session.

- `IDENTITY.md` — name and continuity stance
- `SOUL.md` — values
- `VOICE.md` — how the persona speaks and formats replies
- `BOOTSTRAP.md` — one-shot onboarding script; the persona deletes this
  trait after writing `USER.md`

edit any file in `workspace/`, then `make` to rebuild.

## development

from the repo root:

```
make
```

this regenerates the embedded JSON block in `scripts/index.html` and
renders this README into `persona/index.html`. commit both source and
built artifacts.
