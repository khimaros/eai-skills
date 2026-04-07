#!/usr/bin/env python3
"""local pre-build for the eai-skills repo.

two jobs:
  1. bake persona/workspace/*.md into the JSON block in persona/scripts/index.html
     so the runtime can seed localStorage on first load.
  2. render README.md into a standalone index.html at the repo root, so the
     pages site has a real landing page even with .nojekyll on.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / 'persona' / 'workspace'
INDEX = ROOT / 'persona' / 'scripts' / 'index.html'
PAGES = [
    # (markdown source, html output, title)
    (ROOT / 'README.md',           ROOT / 'index.html',         'eai-skills'),
    (ROOT / 'persona' / 'README.md', ROOT / 'persona' / 'index.html', 'persona'),
]

BEGIN = '<!-- BEGIN persona-default-traits -->'
END = '<!-- END persona-default-traits -->'

def collect():
    if not WORKSPACE.is_dir():
        return {}
    return {
        p.name: p.read_text(encoding='utf-8')
        for p in sorted(WORKSPACE.iterdir())
        if p.is_file() and not p.name.startswith('.')
    }

def bake_traits():
    traits = collect()
    payload = json.dumps(traits, indent=2, ensure_ascii=False)
    block = (
        f'{BEGIN}\n'
        f'<script type="application/json" id="persona-default-traits">\n'
        f'{payload}\n'
        f'</script>\n'
        f'{END}'
    )
    html = INDEX.read_text(encoding='utf-8')
    pattern = re.compile(re.escape(BEGIN) + r'.*?' + re.escape(END), re.DOTALL)
    if not pattern.search(html):
        sys.exit(f'error: markers {BEGIN!r}..{END!r} not found in {INDEX}')
    # use a lambda so re.sub doesn't interpret backslash escapes (e.g. \n)
    # in the replacement string — that would un-escape the JSON payload.
    INDEX.write_text(pattern.sub(lambda _m: block, html), encoding='utf-8')
    verify_baked_json(traits)
    print(f'baked {len(traits)} default trait(s) into {INDEX.relative_to(ROOT)}')

def verify_baked_json(expected):
    """re-read the baked block and ensure it's valid json that round-trips.
    catches the historical bug where re.sub interpreted \\n in the replacement
    string as a literal newline, un-escaping the json payload — json.loads is
    strict about raw control chars in strings, and the equality check catches
    any other write-side mangling."""
    html = INDEX.read_text(encoding='utf-8')
    m = re.search(
        r'<script type="application/json" id="persona-default-traits">(.*?)</script>',
        html, re.DOTALL,
    )
    if not m:
        sys.exit(f'error: default-traits script tag not found in {INDEX}')
    try:
        parsed = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        sys.exit(f'error: baked default-traits block is not valid json: {e}')
    if parsed != expected:
        sys.exit('error: baked default-traits did not round-trip equal to source')

def render_pages():
    if not shutil.which('pandoc'):
        sys.exit('error: pandoc not found on PATH; install pandoc to build pages')
    for src, out, title in PAGES:
        if not src.is_file():
            sys.exit(f'error: {src} not found')
        subprocess.run(
            [
                'pandoc', str(src),
                '--from', 'gfm',
                '--to', 'html5',
                '--standalone',
                '--metadata', f'title={title}',
                '--output', str(out),
            ],
            check=True,
        )
        print(f'rendered {src.relative_to(ROOT)} -> {out.relative_to(ROOT)}')

def main():
    bake_traits()
    render_pages()

if __name__ == '__main__':
    main()
