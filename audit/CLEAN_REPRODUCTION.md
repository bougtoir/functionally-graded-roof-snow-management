# Clean reproduction record

## Final run

- Date: 2026-09-24 UTC
- Commit: `2f4c2db4d66c0bd122ee78873a697b25a3ecdaa4`
- Clean checkout: a detached Git worktree created from the commit above
- Interpreter: Python 3.11.15
- pip: 24.3.1
- Environment: a new `.venv311` containing only packages installed from
  `requirements.txt`

Commands and exit codes:

```text
/home/ubuntu/.pyenv/versions/3.11.15/bin/python -m venv .venv311
exit 0

./.venv311/bin/python -m pip install --upgrade pip==24.3.1
exit 0

./.venv311/bin/python -m pip install -r requirements.txt
exit 0

/usr/bin/time -v make all PYTHON=./.venv311/bin/python
exit 0
elapsed 1:15:24
maximum resident set size 1,543,292 kB

make lint PYTHON=./.venv311/bin/python
exit 0

make test PYTHON=./.venv311/bin/python
exit 0
27 passed
```

The complete pipeline executed the data, baseline, convergence, uniform,
optimization, JMA, sensitivity, robustness, tables, figures, manuscript, and
validation stages. The final validation JSON contained zero errors and four
intentional warnings:

1. author metadata contains user-approved `REQUIRED` placeholders;
2. the manuscript contains user-approved `REQUIRED` placeholders;
3. 136 historical child-worker or blocked source records are not locally
   retained in the public checkout and are not quantitative analysis inputs;
4. the CRST checklist has unresolved manual items.

The validation checks reported a 201-word abstract, continuous line numbering,
six native Word equations, no non-ASCII characters, 21 references, compliant
highlight lengths, nine 1000-dpi TIFF figures, and 61 files in the submission
ZIP.

## Dependency versions

The directly pinned environment was:

```text
matplotlib==3.9.2
numpy==2.1.3
pandas==2.2.3
Pillow==11.0.0
pymoo==0.6.1.3
python-docx==1.1.2
PyYAML==6.0.2
requests==2.32.3
scipy==1.14.1
tifffile==2024.9.20
pytest==8.3.3
ruff==0.7.2
```

The resolved transitive packages were:

```text
about-time==4.2.1
alive-progress==3.3.0
autograd==1.9.1
certifi==2026.7.22
charset-normalizer==3.5.1
cma==3.2.2
contourpy==1.3.3
cycler==0.12.1
Deprecated==1.3.1
dill==0.4.1
fonttools==4.66.0
graphemeu==0.7.2
idna==3.20
iniconfig==2.3.0
kiwisolver==1.5.1
lxml==6.1.3
packaging==26.3
pluggy==1.6.0
pyparsing==3.3.3
python-dateutil==2.9.0.post0
pytz==2026.4
six==1.17.0
typing_extensions==4.16.0
tzdata==2026.4
urllib3==2.8.0
wrapt==2.4.1
```

## Reproduction checks

All nine optimizer history files contained exactly 2,160 population rows:
48 individuals for each of 45 generations. The clean run did not append stale
generations. Git reported no changes to the generated result CSV files,
including the seed-specific histories and Pareto sets, confirming byte-for-byte
agreement with the committed quantitative outputs.

The history-file SHA-256 values from the final clean run were:

```text
geometry seed 1701  49ae6261f51bb8e9e35d9a64dd6a75f89320781d712ea1f63854bf8df6bba4d2
geometry seed 2903  2f090487ac0ed21d0716a71bcdc591ee3a06fd24e824f05c354928a2aacbe7f7
geometry seed 4517  d3111e73ab1b6adf26000a95d231e83621fa8a1291d9483a8e6f8340da2fc176
surface seed 1701   d9c580389ce61b11cd4e94eab1e0a7f1127a6e9dae736e46c7e76f9f3683ca3e
surface seed 2903   0def34d182ab17f95da21f231d5d18d67f18e2f27242948b8c50cc903b485874
surface seed 4517   e365a065e1888059302ef966208229d552ba073ddd8d1b1886aa20028b3e590c
joint seed 1701     7deea4e6ca8e3ea3463a3d35c3e9058a75cdbddbd19dec740641e7b2afe415f8
joint seed 2903     ebe63a153207d13deac8d4ed6766c332fd735f10d5fe0d99a1bdceba586e2fec
joint seed 4517     46b5ea36427d0d2f41a17f2a88a5a5a2c8aa5e2937d8b9cacdbfd2a0fcb3456e
```

Regenerated SVG, EPS, PDF, DOCX, ZIP, manifest, and state files can differ in
embedded creation timestamps, generated XML identifiers, ZIP metadata, or
local-source status. These differences do not alter the quantitative CSV
outputs. The clean validation report correctly evaluates the public checkout,
where excluded third-party files under `data/raw/external/` are absent.

## Source-data behavior

The acquisition ledger contains 233 records. In the public clean checkout,
97 records had checksum-verified local snapshots, 135 historical or excluded
records were marked `not_recovered`, and the CRST Guide for Authors retrieval
remained `no_path` after HTTP 403. The 136 unavailable records are disclosed
but are not quantitative inputs. The official JMA scenario forcing and
redistributable bibliographic metadata used by the study are retained with
checksums. Excluded institutional files remain identified by URL, recorded
size, checksum, usage conditions, and expected path.

## Problems found during clean reproduction

1. The system `python3` was Python 3.10.12, outside the declared
   `>=3.11,<3.13` range, and `python3.11` was not initially available on
   `PATH`. The final run used the installed Python 3.11.15 interpreter at
   `/home/ubuntu/.pyenv/versions/3.11.15/bin/python`.
2. The first requirements-only checkout failed with
   `ModuleNotFoundError: No module named 'graded_roof'`. The Makefile now
   exports the repository `src/` tree through `PYTHONPATH`, so an editable
   installation is not required.
3. The first corrected run exposed stale optimizer-history appends when no
   checkpoint existed. New optimization runs now remove stale history and
   front files before writing.
4. A later interrupted run resumed from serialized pymoo algorithms but
   produced a different population because NumPy's global random state was not
   serialized. Checkpoints now atomically store and restore both the algorithm
   and NumPy random state. A regression test covers this behavior.
5. The final run from commit `2f4c2db` completed without interruption and
   reproduced the committed quantitative outputs.

## Non-fatal warnings

- Matplotlib's PostScript backend reported that transparency is rendered
  opaque in EPS output.
- The test run emitted 14 upstream Matplotlib/pyparsing deprecation warnings.
- pip reported that a newer pip release existed; the declared pip 24.3.1 was
  intentionally retained.

These warnings did not change exit codes or validation status.
