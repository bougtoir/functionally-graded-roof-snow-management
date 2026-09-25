# Phase 13 handoff: CRST format and language

Status: complete

## Official guidance verified

- Retained a complete browser-rendered snapshot of the current official CRST Guide for
  Authors after shell retrieval was blocked by Cloudflare.
- Retained official Elsevier artwork and generative-AI guidance with acquisition
  metadata, byte sizes, and SHA-256 checksums.
- Confirmed current CRST requirements for a 250-word abstract, 1-7 keywords, 3-5
  highlights of at most 85 characters, continuous line numbers, separate artwork,
  editable tables, author-year citations, alphabetical references, and research-data
  deposit or an allowed explanation.

## Manuscript corrections

- Replaced numeric citations with CRST author-year citations and alphabetized the
  22-reference list.
- Applied font-based superscript formatting to negative unit exponents while preserving
  embedded Word drawings.
- Confirmed six native Word math objects and no visible LaTeX.
- Updated the generative-AI section title to the official Elsevier wording while
  preserving an explicit author-review completion item rather than making a false claim.
- Confirmed American English, no unsupported DeepL claim, and no strengthening of the
  audited scientific claims.

## Automated audit

`audit/CRST_FORMAT_LANGUAGE_AUDIT.md` passes all automated format and language gates:

- abstract: 182 words;
- keywords: 6;
- highlights: 4, all 59-67 characters;
- native Word math objects: 6;
- font-superscript unit runs: 19;
- separate TIFF figures: 9, all at least 300 dpi;
- continuous line numbering and single-column Word layout;
- author-year citations and alphabetical references.

## Manual completion retained by instruction

Author affiliation/address, funding, competing interests, CRediT roles, declarations-tool
file, final author review of the AI statement, persistent data-repository identifier or
allowed explanation, and final human proofreading remain explicit pre-submission items.
