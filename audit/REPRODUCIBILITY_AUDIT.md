# Reproducibility audit

- Environment versions are pinned for Python 3.11.
- Optimizer seeds, population, generations, and checkpoints are defined.
- Public JMA raw HTML pages are retained separately from parsed CSV data.
- Request conditions, response headers, sizes, checksums, and terms URLs are retained in acquisition metadata.
- Historical child-worker scratch captures that were not recoverable are explicitly marked and are not treated as analysis inputs or archived evidence.
- Figures, tables, and manuscript values are generated from machine-readable outputs.
- Unit tests cover mass balance, thresholds, weather resampling, density, same-step peaks, and energy-proxy resolution behavior.
