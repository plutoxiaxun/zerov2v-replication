# Notes on Analysis and Interpretation

The following path-count summary refers to the original release cohorts,
not all later supplementary observations. Version 1.1.0 adds
separate cohorts described in [REVISION_DISCLOSURE.md](REVISION_DISCLOSURE.md).
Neither the original observations nor the slow database and concurrency runs
are replaced. Version 1.1.1 (DOI 10.5281/zenodo.23689584) updates
documentation and release-metadata checks from version 1.1.0
(DOI 10.5281/zenodo.23667792). The observation data, numerical analysis
scripts, and plotting code are unchanged.

## Path-comparison results

The repeated comparisons do not show a uniform speed advantage for direct
output. The released observations include the following results:

- Across all seven repeated or matched path cohorts, direct output is faster
  in four and not faster in three; the exploratory exact two-sided sign-test
  value is 1.0.
- Among the five cohorts whose timing and source-read boundaries could be
  checked directly, direct output is faster in two and not faster in three;
  the same exploratory value is 1.0.
- L1 is effectively neutral: direct output is 0.7% slower for the aligned
  source-read/conversion stage.
- The current L2 workset has a 38.7% slower direct first stage. Its shorter
  complete wall time is retained as an operational observation caused by a
  slow staged target-import phase, not as a general direct-write effect.
- W2 favors staging at the measured first stage.
- The 600-GiB full-read boundary pair records 6840 s for direct output and
  1657 s for staged qcow2 output (114.0 versus 27.6 min).
- Three no-recovery traces affected by a concurrent shared-network backup are
  retained in `sensitivity_rows.csv` and are not treated as uncontended-path
  measurements.
- Three post-shutdown recovery traces, including the 5204-s maximum, remain in
  `analysis_summary.json` as stability evidence but are excluded from the
  ordinary-path downtime summary.

Taken together, these results support a conditional performance finding rather
than a general speedup claim.

## Cohort boundaries

1. The 104-row historical primary archive is descriptive operational evidence.
2. The 66-row strict matrix evaluates protocol and recovery boundaries.
3. The current-workset cohort uses a changed source state and is not merged
   with the earlier 426.8-GB state.
4. The 12-row final-core cohort checks its archived tested revision and
   is excluded from the strict-matrix denominator and all performance results.
5. Historical VM-B and VM-C path triplicates are sensitivity evidence because
   source-read counters or allocation metrics are incomplete or inconsistent.

Seven strict-matrix performance rows are ineligible by an explicit exclusion
or by the experiment design. Where their protocol checks passed, they remain
useful as functional or sensitivity evidence. Later successful runs do not
replace these records.

The public master table gives every observation one `analysis_class`. All
rows marked `performance_eligible=False`, including fault-recovery,
sparsity-validation, and final-core correctness rows, carry a stable
`performance_exclusion_code` and a readable reason. Exclusion from a
performance estimate does not remove the row from protocol or sensitivity
analysis.

## What can be checked

The archive supports recomputation of the controlled, downtime, sparse-copy,
current-workset, and protocol results. The historical adaptation table is a descriptive
aggregate rather than per-log observations; the same-workload
TCG/KVM trials remain fully available per run. Raw infrastructure
databases, journals, screenshots, credentials, and identifiers are kept under
controlled access. Batch-level hashes identify the final-core summary, plan,
and state database retained by the authors. The access process is described in
`DATA_ACCESS.md`.

The migration-controller implementation is not part of this repository. The
commit identifies the tested revision in the private development repository.
This package supports numerical reproduction; it does not by itself provide
the software and infrastructure needed to rerun a migration.
