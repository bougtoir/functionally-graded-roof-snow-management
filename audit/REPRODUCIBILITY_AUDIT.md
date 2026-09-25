# Reproducibility audit

## Verdict

- Quantitative reproduction: **PASS (CHECKPOINT-BASED)**.
- Literature-evidence persistence: **PASS**. The five public-source snapshots used by the final reference audit are tracked under `data/raw/published_sources/` with URL, size, checksum, and usage metadata; they are not quantitative analysis inputs.

## Current evidence

- All canonical 0.5-h checkpoint manifests passed configuration, source, weather, seed, and checksum compatibility checks. Figures, Tables, manuscript files, and the submission package were regenerated and validated from those outputs; no detached full optimizer rerun is claimed.
- All 9 0.5-h checkpoint manifests passed: True.
