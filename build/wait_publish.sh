#!/usr/bin/env bash
# poll the deployed pages site until each tracked file's sha256 matches the
# committed local copy. used after `git push` to know when the new build is
# actually live.
set -euo pipefail

BASE="${BASE:-https://khimaros.github.io/eai-skills}"
TIMEOUT="${TIMEOUT:-300}"
INTERVAL="${INTERVAL:-5}"

# repo-relative paths to compare. each is fetched from $BASE/<path>.
FILES=(
    persona/scripts/index.html
    persona/SKILL.md
)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
deadline=$(( $(date +%s) + TIMEOUT ))

for path in "${FILES[@]}"; do
    local_hash=$(sha256sum "$ROOT/$path" | awk '{print $1}')
    url="$BASE/$path"
    printf 'waiting for %s\n  expect %s\n' "$url" "$local_hash"
    while :; do
        remote_hash=$(curl -fsSL "$url" 2>/dev/null | sha256sum | awk '{print $1}' || true)
        if [[ "$remote_hash" == "$local_hash" ]]; then
            printf '  ok\n'
            break
        fi
        if (( $(date +%s) >= deadline )); then
            printf '  TIMEOUT after %ss (last remote: %s)\n' "$TIMEOUT" "${remote_hash:-<none>}" >&2
            exit 1
        fi
        sleep "$INTERVAL"
    done
done

printf 'all tracked files are live at %s\n' "$BASE"
