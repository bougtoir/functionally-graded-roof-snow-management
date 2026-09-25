# Final hostile review

Status: PASS for scientific and computational content; packaging corrections required
before the final handoff

## Desk-rejection risks

| Risk | Final assessment |
|---|---|
| Journal scope | Addressed. The manuscript is explicitly a cold-regions roof-snow design-space study and avoids structural-validation claims. |
| Unsupported practical claims | Addressed. Safety, code compliance, injury reduction, and universal performance are explicitly excluded. |
| Comparator fairness | Addressed. The exhaustive uniform grid is the primary comparator; heterogeneous results are described as heuristic multi-seed sets. |
| Nonconverged production timestep | Disclosed prominently in the abstract, results, limitations, and conclusions. |
| Unconstructable continuous profiles | Disclosed; the mapped profile is described as a post hoc translation rather than a constrained optimum. |
| JMA interpretation | Addressed. Ground observations are supplementary forcing and not roof-scale validation. |
| Citation format | Corrected to the current CRST author-year style and alphabetical bibliography, with journal references ordered as author, year, title, journal, volume, pages/article number, DOI. |
| AI declaration | Present using the journal-required heading; final author-review confirmation intentionally remains a manual completion item. |

## High-risk numerical claims

- The exhaustive uniform set has two unique objective regimes.
- The heuristic joint set preserves the uniform endpoints and adds six observed
  intermediate objective pairs.
- The zero-origin, 1.05-reference normalized hypervolumes are 0.402 for uniform and
  0.611 for joint, while additive epsilon versus uniform is zero.
- Six candidates tie the minimum scalar robustness score.
- Mapping changes modeled retained mass by 0.36% and release mass by 11.03%.
- All three selected production designs fail the frozen composite timestep criterion at
  1 h.

Every item is regenerated from machine-readable results and passes the fabrication
audit.

## Reproducibility and provenance

- A clean detached-worktree run regenerated all 58 quantitative CSV files byte for
  byte.
- Ruff and all 32 tests pass; manuscript validation reports zero errors.
- Three redistribution-restricted literature documents remain unavailable from the
  public checkout. This is disclosed and does not affect quantitative reproduction.
- The official CRST Guide for Authors is retained as a verified browser-rendered
  snapshot; the earlier blocked shell response remains separately labeled.

## Corrections made during this review

1. Corrected bibliography field order to match the current CRST example.
2. Removed language that could imply global completeness of the heuristic heterogeneous
   trade-off set.
3. Corrected the supplement reproduction command sequence so lint and tests are not
   falsely attributed to `make all`.
4. Qualified the public-data claim to distinguish quantitative and redistributable
   snapshots from restricted third-party literature documents.
5. Updated the checklist to record the verified current Guide for Authors snapshot.
6. Corrected the single-author cover letter from “our manuscript” to “my manuscript.”

## Residual manual items

- Author affiliation and postal address.
- Funding and competing-interest declarations.
- CRediT role confirmation.
- Originality, exclusive-submission, and author-approval confirmation.
- Final wording of the generative-AI declaration after author review.
- Persistent repository or data-deposit details if changed before submission.

## Phase 16 packaging requirements

The prior ZIP lacks the editable tables DOCX, editable figures PPTX, reference audit,
fresh reproducibility audit, and final audit. The final packaging phase must add these
files, regenerate all documents after the corrections above, and inspect the ZIP
manifest before delivery.
