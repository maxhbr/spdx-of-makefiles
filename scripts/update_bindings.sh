#!/usr/bin/env bash

set -euo pipefail
venv=$(mktemp -d)
python -m venv $venv
. $venv/bin/activate
python -m pip install shacl2code
shacl2code -h
shacl2code generate -i https://spdx.github.io/spdx-3-model/model.jsonld python -o "$(dirname "$0")/../package/spdx3_0.py"
