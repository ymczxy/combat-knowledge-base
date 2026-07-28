#!/usr/bin/env sh
set -eu
PYTHONPATH=src python -m ckb.cli validate
PYTHONPATH=src python -m ckb.cli stats
PYTHONPATH=src python -m ckb.cli build --output exports
