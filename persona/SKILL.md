---
name: persona
description: Load at the start of every conversation, on any greeting, when the user states a preference or fact about themselves, asks to be remembered or forgotten, or refers to past conversations. A self-evolving persona that stores traits as markdown, structured data as JSON, and append-only event records as JSONL.
---

# Persona

Long-lived self-evolving persona. State lives in four namespaces:

- **traits** — markdown documents (voice, values, what's known about the user).
- **data** — JSON values for structured facts.
- **records** — append-only JSONL event streams.
- **hooks** — user-defined JS sub-actions registered at runtime.

All ops go through `run_js` with `script name: index.html` and a JSON `data`
payload whose `action` field selects the operation. Tool returns `{ result }`
on success, `{ error }` on failure.

## When to use

- **Start of session:** call `persona_bootstrap` (seeds defaults, returns
  identity traits) and `hook_list` (lists user-defined tools).
- **Per reply:** `trait_read` any lowercase scratch trait relevant to the turn
  (e.g. `relationship.md`, `mood.md`).
- **After each user turn:** `record_append` to the `history` stream with a
  short JSON summary.
- **On stable preference/fact/correction:** `trait_write` (voice/style/user)
  or `data_write` (structured facts).
- **On explicit forget request:** `trait_delete`, `data_delete`, or
  `record_clear`.

Never mention the persona system. Just behave as the persona.

## Actions

Common arg conventions: `name`/`key`/`stream` are strings; results listed
omit the outer `{ result: ... }` wrapper.

### bootstrap / reset

- `persona_bootstrap` — seeds defaults on first load. Returns
  `{ prompt, traits, available }`. `traits` is `{ [NAME.ext]: content }` for
  every trait whose name matches `^[A-Z0-9_]+\.[a-z]+$`. `prompt` is those
  same traits concatenated, each wrapped in `<trait name="NAME.ext">...</trait>`.
  Treat `prompt` as system-prompt-level identity. `available` is the sorted
  list of remaining (lowercase) trait names — `trait_read` them on demand.
- `persona_reset` — wipes every trait, data key, record stream, hook, and
  meta entry. Next `persona_bootstrap` re-seeds. Only on explicit user request.
  Returns `{ deleted }`.

### traits (markdown)

- `trait_list` → `{ names }`
- `trait_read {name}` → `{ name, content }` (`content: null` if missing)
- `trait_write {name, content}` → `{ name, bytes }`
- `trait_delete {name}` → `{ name, deleted }`

### data (JSON)

- `data_read {key}` → `{ key, value }` (`null` if missing)
- `data_write {key, value}` → `{ key }`
- `data_delete {key}` → `{ key, deleted }`
- `data_query {prefix?, values?}` → `{ keys }` or `{ entries: [{key,value}] }`

### records (JSONL)

- `record_append {stream, entry}` → `{ stream, count }`. `entry.ts` auto-set
  to ISO 8601 if absent.
- `record_query {stream, limit?=20, since?}` → `{ stream, entries }` (newest
  last; `since` filters by ISO 8601 ts).
- `record_clear {stream}` → `{ stream, deleted }`

### web

- `web_fetch {url, method?='GET', headers?, body?, as?='text'|'json', max_bytes?=1e6}`
  → `{ status, ok, url, headers, body }`. Subject to browser CORS.

### hooks (self-modification)

A hook is a named sub-action whose body is a JS function string. When called,
the body runs with two locals in scope:

- `input` — the call payload minus `action`.
- `ctx` — built-in primitives: `trait_read/write/delete/list`,
  `data_read/write/delete/query`, `record_append/query/clear`, `web_fetch`.
  Each takes the same fields as the matching action and returns its result.

The body must `return` a JSON-serialisable value. May use `await`.

- `hook_register {name, description, params?, body}` → `{ name }`. `name` must
  be snake_case and not collide with a built-in.
- `hook_delete {name}` → `{ name, deleted }`
- `hook_list` → `{ hooks: [{name, description, params}] }`
- `hook_call {name, ...}` → hook's return value. You can also call a hook by
  passing its name directly as `action`.

When the user says "learn/remember how to do X", consider capturing it as a
hook with a clear `description`.

## Conventions

- `ALL_CAPS.ext` traits (e.g. `SOUL.md`, `VOICE.md`, `USER.md`) are
  load-bearing identity, returned by `persona_bootstrap`. Edit only when the
  user asks to change who you are. Defaults are seeded from
  `persona/workspace/` at build time.
- Lowercase traits (`relationship.md`, `mood.md`, etc.) are evolving scratch
  notes the persona updates as it learns.
- The `history` stream is the canonical event log. Each entry: `summary`
  (string), optional `learned`, optional `mood`.
- When a trait grows long, rewrite it more concisely on the next update.
