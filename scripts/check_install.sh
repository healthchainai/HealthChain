#!/usr/bin/env bash
# Install healthchain with pip into clean environments, as users do, and import it.
# Usage: scripts/check_install.sh <wheel path, or "healthchain" for the PyPI release>
# Keep the version list in step with requires-python in pyproject.toml.
set -euo pipefail

SPEC="$1"
TMP="${RUNNER_TEMP:-$(mktemp -d)}"

for PY in 3.10 3.11 3.12 3.13; do
  echo "::group::Python $PY"
  # No extras: core imports and CLI. interop, cdaadapter and
  # sandbox.generators deliberately raise without their extras.
  uv venv --seed --python "$PY" "$TMP/bare-$PY"
  "$TMP/bare-$PY/bin/python" -m pip install -q "$SPEC"
  "$TMP/bare-$PY/bin/python" -I -c "import healthchain, healthchain.fhir, healthchain.gateway, healthchain.io, healthchain.pipeline"
  "$TMP/bare-$PY/bin/healthchain" --help > /dev/null
  # Light extras: every module imports.
  uv venv --seed --python "$PY" "$TMP/extras-$PY"
  "$TMP/extras-$PY/bin/python" -m pip install -q "$SPEC[mcp,langchain,cda,sandbox]"
  "$TMP/extras-$PY/bin/python" -I -c "import importlib, pkgutil, healthchain; [importlib.import_module(m.name) for m in pkgutil.walk_packages(healthchain.__path__, 'healthchain.')]"
  echo "::endgroup::"
done
