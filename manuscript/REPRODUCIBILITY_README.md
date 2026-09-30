# Reproducibility

Use Python 3.11 and install the pinned project plus development dependencies with `python -m pip install -e '.[dev]'`. Run `make lint`, `make test`, and `make all` from the repository root. The production pipeline regenerates quantitative inputs derived from retained raw snapshots, optimization outputs, figures, tables, manuscript files, validation reports, and this submission package.

The current 0.5-h checkpoint manifests passed configuration, source, weather, seed, and checksum compatibility checks. The five public-source snapshots used by the final literature audit are retained under `data/raw/published_sources/` with ledgered URLs, sizes, SHA-256 values, and usage conditions. They are not quantitative analysis inputs. The targeted finalization intentionally did not repeat a full clean pipeline rebuild after the one-time Figure and Table regeneration; see `FINAL_HANDOFF.md` and `manuscript_values.csv`.
