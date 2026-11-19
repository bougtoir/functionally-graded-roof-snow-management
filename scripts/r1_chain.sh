#!/usr/bin/env bash
# Runs the downstream R1 stages sequentially after the Pareto analysis.
set -euo pipefail
PY=.venv/bin/python
while pgrep -f "scripts/r1_analyze.py" >/dev/null; do sleep 20; done
$PY scripts/r1_robustness.py > results/r1/robustness_run.log 2>&1
$PY scripts/r1_event_sensitivity.py > results/r1/event_sensitivity_run.log 2>&1
$PY scripts/r1_jma.py > results/r1/jma_run.log 2>&1
$PY scripts/r1_figures.py > results/r1/figures_run.log 2>&1
echo done > results/r1/chain_done.txt
