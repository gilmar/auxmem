#!/bin/bash
# check_pypi_registry.sh: verify PyPI/TestPyPI availability for the koinome package name.
#
# Usage:
#   bash scripts/check_pypi_registry.sh
#
# Exit 0 when koinome is available on both indexes and legacy auxmem status is reported.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYPROJECT_NAME="$(python3 -c 'import re, pathlib; t=pathlib.Path("pyproject.toml").read_text(); m=re.search(r"^name\s*=\s*\"([^\"]+)\"", t, re.M); print(m.group(1) if m else "")')"
if [ "$PYPROJECT_NAME" != "koinome" ]; then
    echo "check_pypi_registry.sh: expected pyproject.toml name koinome, got ${PYPROJECT_NAME:-<missing>}" >&2
    exit 1
fi

pypi_status() {
    local index_url="$1"
    local package="$2"
    curl -sS -o /dev/null -w "%{http_code}" "${index_url%/}/pypi/${package}/json"
}

echo "== PyPI registry check =="
echo "intended package: koinome (from pyproject.toml)"

koinome_pypi="$(pypi_status https://pypi.org koinome)"
koinome_test="$(pypi_status https://test.pypi.org koinome)"
auxmem_pypi="$(pypi_status https://pypi.org auxmem)"
auxmem_test="$(pypi_status https://test.pypi.org auxmem)"

echo "koinome on PyPI:      ${koinome_pypi} (want 404 — name available)"
echo "koinome on TestPyPI:  ${koinome_test} (want 404 — name available)"
echo "auxmem on PyPI:       ${auxmem_pypi} (legacy; occupied if 200)"
echo "auxmem on TestPyPI:   ${auxmem_test}"

failed=0
if [ "$koinome_pypi" != "404" ]; then
    echo "check_pypi_registry.sh: koinome already exists on PyPI" >&2
    failed=1
fi
if [ "$koinome_test" != "404" ]; then
    echo "check_pypi_registry.sh: koinome already exists on TestPyPI" >&2
    failed=1
fi

if [ "$auxmem_pypi" = "200" ]; then
    echo ""
    echo "legacy auxmem on PyPI (do not publish new Koinome releases under this name):"
    curl -sS "https://pypi.org/pypi/auxmem/json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
info = data['info']
releases = sorted(data.get('releases', {}))
print(f'  latest metadata version: {info.get(\"version\")}')
print(f'  indexed releases: {\", \".join(releases)}')
"
    echo "  see docs/RELEASE.md — yank mistaken 2.0.0 before abandoning the auxmem project page"
fi

if [ "$failed" -ne 0 ]; then
    exit 1
fi

echo ""
echo "check_pypi_registry.sh: koinome is available on PyPI and TestPyPI"
