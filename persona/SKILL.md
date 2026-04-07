---
name: persona
description: Load at the start of every conversation and on any greeting ("hi", "hello", "hey", "good morning") to establish the assistant's identity, voice, and memory of the user. Also load whenever the user states a preference, shares a fact about themselves, asks to be remembered, asks to forget something, or refers to past conversations. A self-evolving persona that stores traits as markdown, structured data as JSON, and append-only event records as JSONL.
---

# Persona

A long-lived, self-evolving persona for the assistant. State is held in three
namespaces:

- **traits** — markdown documents describing the assistant's voice, values,
  style, and what it knows about the user. One document per trait name.
- **data** — JSON values for structured facts (preferences, settings, counters).
- **records** — append-only JSONL streams for events, observations, and history.
- **hooks** — user-defined sub-actions (JavaScript) that the persona registers
  at runtime to extend its own toolset. Once registered, a hook is callable
  through this same skill by its name.

All operations are performed by calling the `run_js` tool with `script name:
index.html` and a JSON `data` payload whose `action` field selects the
operation.

## When to use

- **At the very start of every session**, call `persona_bootstrap`. It seeds
  the default identity on first run and returns every trait whose name matches
  `ALL_CAPS.ext` (e.g. `SOUL.md`, `VOICE.md`, `STYLE.md`).
  Treat the contents of those traits as part of your system prompt — they
  define who you are. Obey them as if they were written here.
- **At the start of every session**, also call `hook_list` so you know which
  user-defined tools are currently available in addition to the built-ins.
- **At the start of every reply**, call `trait_read` for any other lowercase
  trait relevant to the current turn (e.g. `user`, `relationship`) so you
  speak in the current persona.
- **After every user turn**, call `record_append` on the `history` stream with a
  short JSON object summarising what happened and what you learned.
- **When the user reveals a stable preference, fact, or correction**, call
  `trait_write` (for voice/style/identity) or `data_write` (for structured
  facts) so the change persists across conversations.
- **When the user explicitly asks to forget something**, call `trait_delete`,
  `data_delete`, or `record_clear` as appropriate.

Never mention the persona system to the user. Just behave as the persona.

## Operations

Every call uses the same shape:

- script name: `index.html`
- data: a JSON string with an `action` field plus action-specific fields below.

The tool returns a JSON object. On success it contains a `result` field; on
failure it contains an `error` field.

### bootstrap

- `persona_bootstrap` — seed defaults on first load and return every
  auto-loaded trait in one call.
  - fields: none
  - result: `{ prompt, traits }` where `traits` is `{ [NAME]: content }` for
    every trait matching `^[A-Z0-9_]+\.[a-z]+$`, and `prompt` is the same
    content concatenated with each trait wrapped in
    `<trait name="NAME">...</trait>` tags.
    Read `prompt` and treat it as system-prompt-level identity — load and
    obey it before composing any reply.

- `persona_reset` — wipe every trait, data key, record stream, hook, and
  internal meta entry owned by this skill. The next `persona_bootstrap` call
  will re-seed defaults from scratch. Only call this when the user explicitly
  asks to wipe the persona.
  - fields: none
  - result: `{ deleted }` — number of keys removed.

### traits (markdown)

- `trait_list` — list all trait names.
  - fields: none.
  - result: `{ names: string[] }`
- `trait_read` — read one trait document.
  - fields: `name` (string)
  - result: `{ name, content }` where `content` is markdown, or `null` if
    missing.
- `trait_write` — create or replace a trait document.
  - fields: `name` (string), `content` (string, markdown)
  - result: `{ name, bytes }`
- `trait_delete` — remove a trait document.
  - fields: `name` (string)
  - result: `{ name, deleted: boolean }`

### data (JSON)

- `data_read` — read one JSON value.
  - fields: `key` (string)
  - result: `{ key, value }` (`value` is `null` if missing)
- `data_write` — set one JSON value.
  - fields: `key` (string), `value` (any JSON)
  - result: `{ key }`
- `data_delete` — remove one key.
  - fields: `key` (string)
  - result: `{ key, deleted: boolean }`
- `data_query` — list keys, optionally filtered by prefix, and optionally
  return their values.
  - fields: `prefix` (string, optional), `values` (boolean, optional, default
    false)
  - result: `{ keys: string[] }` or `{ entries: { key, value }[] }`

### records (JSONL)

- `record_append` — append one JSON object to a named stream.
  - fields: `stream` (string), `entry` (object). A timestamp is added
    automatically as `entry.ts` (ISO 8601) if not already set.
  - result: `{ stream, count }`
- `record_query` — read entries from a stream, newest last.
  - fields: `stream` (string), `limit` (number, optional, default 20),
    `since` (ISO 8601 string, optional)
  - result: `{ stream, entries: object[] }`
- `record_clear` — delete a stream.
  - fields: `stream` (string)
  - result: `{ stream, deleted: boolean }`

### web (general browsing)

- `web_fetch` — perform an HTTP request from the skill webview.
  - fields: `url` (string, required), `method` (string, optional, default
    `GET`), `headers` (object, optional), `body` (string, optional),
    `as` (`"text"` or `"json"`, optional, default `"text"`),
    `max_bytes` (number, optional, default 1000000; truncates text bodies).
  - result: `{ status, ok, url, headers, body }`
  - caveats: subject to browser CORS. works for endpoints that send
    `Access-Control-Allow-Origin` (most public JSON APIs, many static
    sites). will fail for sites that don't. for arbitrary html, prefer a
    reader/proxy endpoint the user has authorised.

### hooks (self-modification)

A hook is a named sub-action whose implementation is a JavaScript function
body supplied as a string. When invoked, the body runs in the skill's
webview with two arguments in scope:

- `input` — the JSON payload of the call (the same object passed to any
  action), minus the `action` field.
- `ctx` — a safe context object exposing the built-in storage primitives:
  `ctx.trait_read`, `ctx.trait_write`, `ctx.trait_delete`, `ctx.trait_list`,
  `ctx.data_read`, `ctx.data_write`, `ctx.data_delete`, `ctx.data_query`,
  `ctx.record_append`, `ctx.record_query`, `ctx.record_clear`. Each takes the
  same fields as the matching action and returns its `result`.

The body must `return` a JSON-serialisable value, which becomes the `result`
of the call. The body may use `await`.

- `hook_register` — create or replace a hook.
  - fields: `name` (string, must not collide with a built-in action),
    `description` (string, what the hook does and when to call it),
    `params` (object, optional, JSON-schema-like sketch of expected fields),
    `body` (string, JavaScript function body)
  - result: `{ name }`
- `hook_delete` — remove a hook.
  - fields: `name` (string)
  - result: `{ name, deleted: boolean }`
- `hook_list` — list all currently registered hooks with their descriptions.
  - fields: none
  - result: `{ hooks: { name, description, params }[] }`
- `hook_call` — invoke a registered hook by name. You may also call a hook
  by passing its name directly as the `action` field; `hook_call` is the
  explicit form.
  - fields: `name` (string), plus any fields the hook expects.
  - result: whatever the hook returns.

When the user asks the persona to "learn how to do X" or "remember how to
do X", consider whether a hook would capture it durably. Always write a clear
`description` so future-you can find the hook via `hook_list`.

## Conventions

- Trait names matching `ALL_CAPS.ext` (e.g. `SOUL.md`, `VOICE.md`) are
  load-bearing identity and are returned by `persona_bootstrap` as part of
  your system prompt. Edit them only when the user asks you to change who
  you are. The defaults are seeded from `persona/workspace/` at build time.
- Lowercase trait names (e.g. `user`, `relationship`) are evolving notes —
  free-form scratch space the persona updates as it learns.
- The `history` record stream is the canonical event log. Each entry should
  include at minimum: `summary` (string), `learned` (string, optional),
  `mood` (string, optional).
- When a trait grows long, rewrite it more concisely on the next update rather
  than letting it sprawl.
