#!/usr/bin/env python3
"""bake persona/workspace/*.md into persona/scripts/index.html.

reads every regular file under persona/workspace/ and writes a JSON map
{filename: contents} into the marked <script> block in index.html. the
runtime reads this block to seed localStorage on first load.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / 'persona' / 'workspace'
INDEX = ROOT / 'persona' / 'scripts' / 'index.html'

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

def main():
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
    INDEX.write_text(pattern.sub(block, html), encoding='utf-8')
    print(f'baked {len(traits)} default trait(s) into {INDEX.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
