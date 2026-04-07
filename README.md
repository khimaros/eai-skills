# eai-skills

skills for the [google ai edge gallery](https://github.com/google-ai-edge/gallery).

## skills

- [persona](persona/) — a self-evolving, long-lived persona.
  load it in the gallery from
  `https://khimaros.github.io/eai-skills/persona/`.

## development

```
make
```

bakes default trait files into each skill's webview script and renders
each `README.md` into a sibling `*.html` for github pages. commit both
sources and built artifacts.

`.nojekyll` at the repo root disables jekyll so files are served as-is,
which is required by the gallery's skill loader.
