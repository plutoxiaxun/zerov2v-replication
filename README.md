# ZeroV2V Replication Package

This repository accompanies the ZeroV2V IEEE Access manuscript. It contains
the deidentified data and analysis scripts used to calculate the results
reported in the paper, **ZeroV2V: A Recoverable VMware-to-KVM/Ceph Migration
Protocol with Final-RBD Checkpointing**. This is the **1.1.0 release package**,
prepared locally and not yet uploaded to GitHub or Zenodo. The previous public
version is **1.0.2** and remains archived separately.
See [REVISION_DISCLOSURE.md](REVISION_DISCLOSURE.md)
for the added data, measurement definitions and publication checklist.
Reviewers can start with [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md).

## Contents and scope

The original per-run tables cover the controlled comparisons, the current-workset
comparison, and the 66-run protocol matrix. Selection and exclusion fields
distinguish performance observations from recovery and sensitivity cases. An
additional 12-run fault-validation cohort is published in
`final_core_validation.csv`; it is kept separate from the 66-run matrix and
from all performance calculations.

Each row has one `analysis_class`. Every row with
`performance_eligible=False` also has a machine-readable
`performance_exclusion_code` and a human-readable explanation. These fields
make adverse, sensitivity, recovery, and correctness-only observations
explicit without removing them from the release.

The per-run files support recalculation of the controlled comparisons,
downtime strata, current-workset results, boundary cases, and protocol evidence
counts. The heterogeneous historical TCG/KVM distribution in Table 6 is an
aggregate-only result; it is descriptive and is not used as a causal
comparison. Measurements that showed no benefit or favored staging are
included alongside favorable results. The archive does not include
infrastructure credentials, IP addresses, real VM names, cloud resource UUIDs,
RBD image names, VMware snapshot identifiers, or complete service journals.

The revision adds paired path and recovery-cost runs, competing-tool results,
concurrency, SQL service gaps, verification costs, frozen-model observations,
database diagnosis and independent confirmation in `data/revision/`.
Original failures and later corroboration are distinguished in
`data/revision/outcomes.json`; those campaign counts are not fabricated
per-run timing records. The historical M0031 exclusion description is
corrected without changing its measured bytes or eligibility.

This is a data-and-analysis replication package. It provides the evidence and
standard-library scripts needed to reproduce the reported calculations, but it
does not distribute the ZeroV2V migration-controller implementation. The
protocol, state transitions, recovery boundaries, and pseudocode needed to
review the design are provided in the manuscript.

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for file grain and field
semantics, and [PUBLICATION_NOTES.md](PUBLICATION_NOTES.md) for cohort
boundaries and interpretation of adverse or confounded observations.
The machine-readable `data/figure_table_trace.json` maps every data-bearing
manuscript figure or table to its public inputs, transformation, supported
claim, and limitation.

## Reproduce the public analysis

From the released repository:

```bash
python3 -B scripts/verify_manifest.py
python3 -B scripts/audit_public_release.py --release-ready
python3 -B scripts/analyze_public_data.py
python3 -B scripts/analyze_revision.py
python3 -B scripts/test_revision.py
```

The numerical scripts use only the Python standard library and require Python
3.10 or newer. Optional `scripts/plot_public_figures.py` requires matplotlib
and renders the four quantitative figures to a user-selected output directory.
`MANIFEST.sha256` covers every release artifact. The manifest verifier
rejects unlisted files; the release audit checks file types and common
identifier and credential patterns.

`--release-ready` checks package hygiene and metadata consistency; it does not
mean that a public upload has occurred. Version 1.1.0 has no new
DOI until a new archive is actually published.

See [DATA_ACCESS.md](DATA_ACCESS.md) for the controlled-access procedure.
[EXPERIMENT_RUNBOOK.md](EXPERIMENT_RUNBOOK.md) separates public
statistical reproduction from infrastructure re-execution and records the
final fault-validation cohort.

## Licenses

Package-specific code in `scripts/` is released under Apache-2.0. The
deidentified data and documentation are released under CC BY 4.0. Full terms
and file-level scope are listed in [LICENSES.md](LICENSES.md).
