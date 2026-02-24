#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

build_module() {
  local module="$1"
  echo "==> Building frontend/${module}"
  pushd "${ROOT_DIR}/frontend/${module}" >/dev/null
  npm install
  npm run build
  popd >/dev/null
}

build_module home
build_module cloud
build_module hypotheses
build_module interviews

echo "Builds generated in static/home, static/cloud, static/hypotheses, static/interviews"
