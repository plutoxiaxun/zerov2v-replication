# Experiment Reproduction Runbook

The public CSV and JSON files permit recalculation of the row-based
statistics without access to the test infrastructure. Historical conversion
distributions and additional fault/acceptance counts are released as
aggregates; independently reconstructing those aggregates requires the
controlled source records described in `DATA_ACCESS.md`. Re-executing the
migration protocol requires a VMware source, a Ceph-backed KVM target cloud,
VDDK, `nbdkit`, `virt-v2v`, and site-specific credentials.

## Frozen implementation

The final core-fault cohort was executed from Git commit
`3681503dd376425eec126ea66249bc2cbcbe377f`. Later fixes must use a new commit
and be reported as a distinct revision. The cohort contains 12 new rows and
does not replace or extend the historical 66-row strict matrix:

1. `FC-F1-PARTIAL-R1` through `FC-F5-CUTOVER-R1`, including the separately
   declared `FC-F3-ROLLBACK-RETRY-R1`;
2. the corresponding six `R2` rows in the same order.

The two `FC-F3-ROLLBACK` rows are expected failures only when the recorded
fault point is `direct_conversion.after`. Every other row must succeed. The
runner is serial and stops on an unexpected failure.

## Public statistical reproduction

Run these commands from the root of the released repository:

```bash
python3 -B scripts/verify_manifest.py
python3 -B scripts/audit_public_release.py --release-ready
python3 -B scripts/analyze_public_data.py
python3 -B scripts/analyze_revision.py
python3 -B scripts/test_revision.py
```

The analysis output must reproduce the controlled-trial effects, current
workset comparison, boundary case, and strict-matrix counts stated in the
manuscript. The release maintainer regenerates the manifest whenever the
released contents change. The public audit also checks
cohort counts, subset integrity, fault-point evidence, status and topology
rules, and common identifier or credential patterns.

## Infrastructure re-execution

The private deployment used an isolated experiment API and a dedicated batch
state database. A reproducing site should provide its own deidentified
workload catalog and follow these rules:

- use new run and target-resource names for every re-execution;
- record the application commit in every job;
- keep large local artifacts on a dedicated data filesystem;
- require healthy Ceph before submission;
- retain source checkpoints, target RBDs, group checkpoints, journals, and
  console evidence after failures;
- stop the batch on an unexpected failure without cancelling the active
  application migration;
- keep fail-closed conversion rows separate from their declared retries.

The public runbook omits credentials, endpoint configuration, internal
addresses, VM names, RBD names, snapshot identifiers, and production logs.
They are not needed for statistical reproduction. Requests for retained
evidence follow the controlled-access process in `DATA_ACCESS.md`.

## Final-core release evidence

The released `final_core_validation` table contains the cohort's deidentified
per-row status, fault trigger, build commit, checkpoint-presence flag,
topology, and verification counts. `analysis_summary.json` records the
batch-level hashes for the retained summary, plan, and state database. These
rows remain separate from the historical strict-matrix counts. Incomplete or
repaired rows retain their original status and exclusion reason.
