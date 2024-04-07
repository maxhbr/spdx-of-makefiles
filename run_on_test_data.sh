#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"
set -x
poetry run python -m package \
  --src test_data/hello-2.12 \
  --src_strip_prefix /src/ \
  --bear_json test_data/bear.json \
  --artifact test_data/hello-2.12/hello \
  _test_out
