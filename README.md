# Functionally graded roofs for passive snow management

This repository is a reproducible computational proof-of-concept study of
whether spatial variation in roof geometry and snow-surface interaction changes
the trade-off between maximum retained roof snow mass and maximum single-event
snow shedding compared with optimized spatially uniform roofs.

The target journal is *Cold Regions Science and Technology*. The analysis does
not assume that graded roofs are superior. Snow-retention, conventional
shedding, uniform intermediate, and heterogeneous designs are evaluated under
identical modeled weather conditions.

## Reproduce

The supported environment is Python 3.11.

```bash
conda env create -f environment.yml
conda activate graded-roof-snow
make all
```

For an existing environment:

```bash
python -m pip install -r requirements.txt
make test
make all
```

The Makefile exposes the repository's `src/` tree through `PYTHONPATH`, so an
editable package install is not required for these targets.

`make all` regenerates processed data, analyses, figures, tables, the manuscript,
audits, and the CRST submission package. It fails if a critical validation gate
fails.

Production optimization evaluates 6,300 uniform designs and three independent
NSGA-II seeds for each heterogeneous mode. Heterogeneous runs checkpoint under
`checkpoints/` and resume after interruption.

## Main targets

```text
make data
make baseline
make optimize
make jma
make sensitivity
make robustness
make figures
make tables
make manuscript
make validate
make all
```

The production configuration is `config/production.yaml`. The locked primary
outcomes are maximum roof snow mass over time (`L_max`) and maximum
single-timestep shed mass (`S_max`). The Snow Shedding Concentration Index
(`SSCI`) is secondary and study-specific.

Submission-ready aliases are written under `manuscript/`, separate PNG, TIFF,
SVG, PDF, and EPS figures under `figures/`, machine-readable tables under
`tables/generated/`, and the curated archive at
`submission/CRST_submission_package.zip`. Author affiliation, declarations,
CRediT roles, originality, and approval remain explicit placeholders for local
completion before submission.

## Data and provenance

Original public-data responses used as analysis inputs or authoritative
evidence are stored under `data/raw/` and are never overwritten.
`data/metadata/acquisition_ledger.csv` records source URLs, identifiers,
retrieval times, request parameters, file sizes, checksums, and reuse terms.
Historical child-worker scratch captures that could not be recovered remain
explicitly marked and are not treated as analysis inputs or archived evidence.
Third-party institutional documents kept locally but excluded from repository
redistribution remain recoverable from the source URLs recorded with their
sizes, checksums, and usage terms in the ledger.
Derived UTF-8 and analysis-ready files are stored separately.

Japanese weather observations are scenario inputs, not physical validation of
roof load or safety. JMA ground snowfall and snow-depth observations are not
treated as direct measurements of roof snow mass.

The retained JMA snapshot uses monthly daily tables from the official
Historical Weather Data Search for Kutchan, Aomori, Shinjo, and Takada over
three winters. Original HTML, request parameters, response headers, and
checksums are preserved. Daily aggregation limits event-timing interpretation;
the primary optimization therefore remains based on the frozen synthetic
hourly scenarios. The deviation from the initially planned JMA bulk-hourly
route is documented in `analysis_deviations.md`.

To create a new immutable JMA snapshot without overwriting the retained one:

```bash
python scripts/acquire_jma_daily.py --snapshot-id YYYYMMDDTHHMMSSZ
python scripts/build_acquisition_ledger.py
```

## Scope

The model is intentionally parsimonious. It supports force-balance initiation,
kinetic-friction transport, adhesion, simple snow aging, melting, and optional
rain-on-snow effects. It does not establish structural code compliance,
pedestrian safety, injury reduction, or universal real-world superiority.

## License and citation

Code is released under the MIT License. Third-party data retain their original
terms. See `CITATION.cff` and the acquisition ledger for attribution.
