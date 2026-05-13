#!/usr/bin/env bash
set -euo pipefail

# Check changed source files (working tree + staged) vs last commit
changed=$(git diff --name-only HEAD 2>/dev/null || true)

if [[ -z "$changed" ]]; then
    exit 0
fi

unspecced=()

while IFS= read -r file; do
    [[ -z "$file" ]] && continue

    # Only consider source files
    [[ "$file" =~ \.(ts|tsx|js|jsx|py)$ ]] || continue

    # Skip test/spec files themselves
    [[ "$file" =~ \.(test|spec)\.(ts|tsx|js|jsx|py)$ ]] && continue

    # Skip deleted files
    [[ -f "$file" ]] || continue

    # Check for a sibling test file (any extension variant)
    base="${file%.*}"
    found=false
    for candidate in \
        "${base}.test.ts" "${base}.test.tsx" \
        "${base}.spec.ts" "${base}.spec.tsx" \
        "${base}.test.js" "${base}.test.jsx" \
        "${base}.spec.js" "${base}.spec.jsx" \
        "${base}.test.py" "${base}.spec.py"; do
        [[ -f "$candidate" ]] && found=true && break
    done

    [[ "$found" == "true" ]] || unspecced+=("$file")
done <<< "$changed"

if [[ ${#unspecced[@]} -eq 0 ]]; then
    exit 0
fi

file_list=$(printf '  - %s\n' "${unspecced[@]}")

jq -n --arg reason "These modified source files have no corresponding test file. Write specs before finishing:

${file_list}" \
    '{decision: "block", reason: $reason}'

exit 2
