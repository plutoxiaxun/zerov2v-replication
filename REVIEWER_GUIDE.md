# Reviewer Guide

This page gives a short route through the evidence used in the manuscript.
The public release supports review of the reported calculations and protocol
counts. It is not a deployable copy of the migration controller.

## Ten-minute check

Run the following commands from the repository root:

```bash
python3 -B scripts/verify_manifest.py
python3 -B scripts/audit_public_release.py --release-ready
python3 -B scripts/analyze_public_data.py
python3 -B scripts/analyze_revision.py
python3 -B scripts/test_revision.py
```

The first command verifies every released file against `MANIFEST.sha256`.
The second checks row counts, subset membership, fault points, topology and
sampling rules, deidentification patterns, local links, and unexpected files.
The two analysis commands recalculate the original and revision statistics
from public tables and print JSON to standard output. The tests exercise
paired indexing, key numerical claims and retained adverse outcomes.

`data/figure_table_trace.json` maps each data-bearing manuscript table and
figure to its source file, row selection, calculation, claim, and limitation.
The trace uses the current 20-page manuscript numbering. Original field
definitions are in [DATA_DICTIONARY.md](DATA_DICTIONARY.md); added fields,
cohorts, endpoints and disclosure boundaries are in
[REVISION_DISCLOSURE.md](REVISION_DISCLOSURE.md).

## Evidence available by result

| Manuscript result | Public evidence | Review level |
|---|---|---|
| Controlled direct/staged comparisons and sparse-copy trials | `master_analysis.csv`, `controlled_trials.csv` | Per-run values; means, ranges, standard deviations, read volumes, and effects can be recalculated |
| Controlled low-downtime TCG/KVM comparison | `controlled_trials.csv` | Per-run values and phase decomposition for all four workloads |
| Historical TCG/KVM duration distribution | `conversion_environment_summary.csv` | Descriptive aggregate only; the journal-linked per-log observations remain controlled |
| Ordinary-path and sensitivity downtime strata | `master_analysis.csv`, `sensitivity_rows.csv`, `analysis_summary.json` | Per-run cutover values and explicit recovery/contention flags |
| Current L2 workset | `current_workset.csv` | Per-run stage time, wall time, source reads, revision, and checkpoint-presence evidence |
| 600-GiB full-read counterexample | `boundary_cases.csv` | Both path observations are public and remain outside pooled effects |
| 66-run protocol matrix | `strict_matrix.csv` | Per-run status, fault point, eligibility, topology, block-sample count, console count, and commit boundary |
| Final 12-run fault-validation cohort | `final_core_validation.csv`, `analysis_summary.json` | Per-run status and evidence counts, tested commit, checkpoint presence, and hashes of the retained source records |
| Supplementary performance, recovery cost, competing tool, concurrency, SQL service, verification and frozen model | `revision/observations.json` | Individual timing observations; failed completion values stay null or in separate outcome counts |
| Database diagnosis and independent confirmation | `revision/observations.json` | Paired timings, frozen predictions, per-disk request counters and phase decomposition; all slow observations retained |
| Additional fault boundaries and acceptance accounting | `revision/outcomes.json` | Explicitly aggregate archived outcomes; raw fault/acceptance records remain controlled |

The historical TCG/KVM distribution is not used as a causal comparison. The
same-workload controlled trials provide the public per-run evidence for the
conversion-worker deployment result.

## Interpretation boundaries

- Timing fields with different definitions are not pooled.
- `analysis_class` records the analytical use of every row, and every
  `performance_eligible=False` row carries an explicit exclusion code and
  explanation.
- Post-shutdown recovery runs remain available as recovery evidence but do
  not enter the ordinary-path downtime summary.
- The three shared-network contention observations remain in the sensitivity
  table and are not treated as uncontended measurements.
- The current-workset rows are not merged with the earlier source state.
- `Running` is a target-cloud control-plane state. Console samples support the
  reported boot gate; neither field is an application-readiness test.
- Sampled block comparisons are not whole-disk hashes.
- The final-core cohort checks its archived tested revision and does not alter the
  historical matrix denominator or any performance estimate.
- Later local code-correction tests are not relabeled as new live migration
  or fault-injection outcomes.

The numerical consequences of these boundaries are summarized in
[PUBLICATION_NOTES.md](PUBLICATION_NOTES.md) and the claim-level decisions are
listed in `data/claim_evidence_ledger.md`.

## Evidence not released without review

Raw databases, complete journals, infrastructure identifiers, and console
captures can reveal workload or site information. They are retained under the
process in [DATA_ACCESS.md](DATA_ACCESS.md). Batch-level SHA-256 values in
`analysis_summary.json` identify the final-core summary, plan, and state
database retained by the authors.

The migration-controller source is maintained separately and is not
distributed in this release. The manuscript, pseudocode, protocol invariants,
and public data support review of the reported design and results. An
independent infrastructure re-execution would additionally require the
implementation and a compatible VMware/VDDK/Ceph/KVM test environment.
