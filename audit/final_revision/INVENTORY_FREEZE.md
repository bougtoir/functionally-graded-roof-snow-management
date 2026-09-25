# Final-revision inventory and freeze audit

## Canonical workspace

- Repository: `bougtoir/functionally-graded-roof-snow-management`
- Branch: `devin/1790242860-crst-graded-roof`
- Starting commit: `9f313dcbb52c7f140c709d7e3a35aed23e69659b`
- Canonical review manuscript: `manuscript/manuscript_CRST_inline.docx`
- Frozen primary outcomes: `L_max_kg_per_m` and `S_max_kg_per_m`
- Frozen production configuration: `config/production.yaml`
- Freeze record: `analysis_freeze.yaml`

The final-revision prompt referred to `config/analysis_freeze.yaml`; the
canonical tracked freeze file is at the repository root. No competing copy was
created.

## Persistent inputs and expensive state

- 250 files are retained under `data/raw/`.
- The acquisition ledger contains 233 source records.
- The official JMA snapshot covers four stations, three winters, and the
  November-April daily pages needed for the supplementary scenarios.
- Nine optimizer checkpoints are present: three seeds for each of geometry,
  surface, and joint heterogeneity.
- Each committed optimizer history contains 2,160 population rows.

## Canonical quantitative outputs

The primary numerical sources are the generated CSV files under
`results/generated/` and `tables/generated/`. Manuscript prose reads those
files during document generation. The initial map of manuscript claims to
canonical sources is in `audit/final_revision/number_provenance.csv`.

## Frozen decisions preserved

- The reduced-order physics, primary outcomes, uniform design space, optimizer
  seeds, production resolution, and synthetic weather scenarios remain frozen.
- JMA daily observations remain supplementary scenario forcing rather than
  roof-load validation.
- No structural-load, safety, code-compliance, injury, or universal-superiority
  interpretation is permitted.
- Targeted secondary analyses may audit interpretation and comparability but
  may not replace the frozen primary analysis.

## Audit targets carried forward

1. The front-specific normalized-distance knees are not cross-front evidence of
   superiority.
2. Hypervolume and additive epsilon require an explicit common normalization
   and reference-point explanation.
3. Nominally identical objective pairs can conceal large robustness differences.
4. Complexity penalties selecting a uniform design are a substantive negative
   result.
5. The 12 JMA station-winters require paired trade-off summaries and station
   names, while retaining the non-validation framing.
6. Table 3 losses require explicit units and absolute-versus-percentage labels.

## Phase gate

Status: PASS. The canonical workspace, persistent inputs, freeze record,
checkpoints, result sources, and manuscript have been identified. No
uncommitted changes preceded the final-revision work.
