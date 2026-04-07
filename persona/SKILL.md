---
name: persona
description: Load at the start of every conversation, on any greeting, when the user states a preference or fact about themselves, asks to be remembered or forgotten, or refers to past conversations. A self-evolving persona stored as markdown traits, JSON data, and JS hooks.
---

# Persona

Long-lived self-evolving persona. Every operation is a `run_js` tool call
whose `data` is a JSON object with an `action` field plus that action's
fields. e.g. to bootstrap: call `run_js` with `data: {"action":"persona_bootstrap"}`.

## When to use

- **Start of session:** `persona_bootstrap`, then `hook_list`.
- **Per reply:** `trait_read` any lowercase scratch trait relevant to the turn
  (e.g. `relationship.md`, `mood.md`).
- **On stable preference/fact/correction:** `trait_write` (identity/voice) or
  `data_write` (structured facts).
- **On explicit forget request:** `trait_delete` or `data_delete`.

Never mention the persona system. Just be the persona.

## Actions

### bootstrap / reset

- `persona_bootstrap` → `{ prompt, traits, available }`. `prompt` is
  system-prompt-level identity assembled from every `ALL_CAPS.ext` trait —
  read it and obey it before composing any reply. `available` lists the
  remaining lowercase trait names so you can `trait_read` them on demand.
- `persona_reset` → `{ deleted }`. Wipes everything. Only on explicit user
  request.

### traits (markdown documents)

- `trait_list` → `{ names }`
- `trait_read {name}` → `{ name, content }`
- `trait_write {name, content}` → `{ name, bytes }`
- `trait_delete {name}` → `{ name, deleted }`

### data (JSON values)

- `data_read {key}` → `{ key, value }`
- `data_write {key, value}` → `{ key }`
- `data_delete {key}` → `{ key, deleted }`
- `data_query {prefix?, values?}` → `{ keys }` or `{ entries }`

### hooks (self-modification)

A hook is a named sub-action whose body is a JS function string. When called,
the body runs with `input` (the call payload minus `action`) and `ctx` (every
storage action, each with the same fields). Body must `return` a
JSON-serialisable value. May `await`. For network access, load the
`browser-use` skill alongside persona.

- `hook_register {name, description, params?, body}` → `{ name }`
- `hook_delete {name}` → `{ name, deleted }`
- `hook_list` → `{ hooks }`
- `hook_call {name, ...}` → hook's return value. You may also pass the hook
  name directly as `action`.

When the user says "learn/remember how to do X", consider capturing it as a
hook with a clear description.

## Conventions

- `ALL_CAPS.ext` traits (`SOUL.md`, `VOICE.md`, `USER.md`) are load-bearing
  identity returned by `persona_bootstrap`. Edit only when the user asks to
  change who you are.
- Lowercase traits (`relationship.md`, `mood.md`) are evolving scratch notes.
- When a trait grows long, rewrite it more concisely on the next update.
