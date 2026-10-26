# Disclosure for the condensed revision

Version 1.1.0 adds the observations and calculations supporting
the 20-page revision. Its reserved DOI is
[10.5281/zenodo.23667792](https://doi.org/10.5281/zenodo.23667792);
upload and publication are pending. The
previous public version is 1.0.2; its archive DOI is not a DOI for these new files.
See [RELEASE_STATUS.json](RELEASE_STATUS.json).

## Included material

| Evidence | Public input | Reproduction |
|---|---|---|
| Ten-pair supplementary direct/staged paths and ten-block A/B/C recovery cost | `data/revision/observations.json`, `earlySupplementary` | Arm means/SD, paired differences, Student intervals, exact sign-flip probabilities, cleanup-tail sensitivity |
| Five paired competing-tool runs | `supplementary.M1` | Controller completion and first boot remain separate endpoints |
| Fifteen concurrency batches, including the incomplete batch | `supplementary.S6a`, `S6aStages` | Complete-batch durations, paired throughput ratios and 31 member phase summaries |
| Twelve SQL service attempts | `supplementary.D1r`, `data/revision/outcomes.json` | Attempted/completed counts and complete-pair response-gap reduction; original acceptance is distinct from later corroboration |
| Twelve verification-cost observations | `supplementary.V1r` | Full/sample timing, digest cost and unique logical coverage |
| Original frozen model and retained adverse observations | `supplementary.P1`, `P1Choices`, outcome counts | Predictions, MAPE, five paired choices, always-direct comparator and retained original failures |
| Frozen prediction construction | `data/revision/frozen-model.json` | Three calibration pairs, fixed held-out inputs, original formulas and predictions; no private workload identities |
| Six diagnostic rows and one independent confirmation pair | `diagnosis`, `confirmation` | No refitting or replacement; full cohorts and whole-pair sensitivity, stage/read decomposition |
| Six additional fault-boundary observations | `data/revision/outcomes.json`, `F1r` | Campaign-level counts from retained closeout; no invented per-run times |
| Historical cohort accounting | `data/master_analysis.csv` | Membership and intersection matrix for 210 unique historical public records |
| Current L2 import/publication phase | `currentWorksetPhases` in `revision/observations.json` | Seven measured phase durations joined by public record ID, not wall-minus-first-stage estimates |
| Current figures and tables | `data/figure_table_trace.json` | Current numbering for all 20 tables, six main figures and two supplemental diagrams |

Run `python3 -B scripts/analyze_revision.py` for the supplementary statistics,
and `python3 -B scripts/test_revision.py` for regression checks. Original
cohorts remain reproducible with `scripts/analyze_public_data.py`.

For the four quantitative figures, install matplotlib and run:

```bash
python3 -B scripts/plot_public_figures.py --output-dir ../reproduced-figures
```

The script renders Figures 3–6 from public values. Figures 3, 4 and 6 follow
the revised plotting code; Figure 5 is a numerical reconstruction with the
same means, units and min/max error-bar definition. Font/layout or PDF byte
identity across software versions is not promised. Structural diagrams and
the manuscript itself are not redistributed as statistical data.

Figure 5's right panel is source requests as a percentage of provisioned
capacity, calculated as `100 * source_read_gib / allocated_capacity_gib`,
not absolute GiB or unique-byte coverage. Historical sparse-copy read volumes
are exported to three decimals in GiB. Table 9's percentages were rounded
separately from the original counters, so recomputing from these rounded GiB
values can differ by 0.001 percentage point in the last displayed digit.
This does not affect Figure 5's one-decimal percentages or the path comparison.

Table 6 is backed by `conversion_environment_summary.csv`, an environment-level
aggregate of 42 TCG and 48 KVM parsed runs. It is not reconstructed by selecting
nonempty conversion timings in `master_analysis.csv`; those are a different
recording scope. The released aggregate supports checking the printed table,
but not independent observation-level recalculation of its historical summary.

## Measurement definitions

All durations are seconds unless a field says otherwise; `Bytes` means bytes,
GiB is 2^30 bytes and MiB is 2^20 bytes. Null means unmeasured, unavailable or
inapplicable, never zero. Repetition and pair keys are local to a cohort.
The early S1 cohort is not the original sparse-policy P1 cohort. The held-out
prediction cohort also uses the label P1; do not merge those populations.

`earlySupplementary` contains 62 rows: 20 S1, 30 R1 and 12 S4 mechanism/content
records. R1 arms A/B/C denote reference, journal, and journal-plus-checkpoint;
`wallSeconds` includes cleanup and `beforeCleanupSeconds` excludes it.
The S4 rows are supporting mechanism observations, not extra performance
replications. Allocation metrics from local files and target storage are not
interchangeable write-amplification measures.
S4-W1, S4-W2 and S4-W3 are release-local workload aliases; no source naming
convention or network-address suffix is retained. R1 arm configuration labels
and timings are public; the receipts verifying which generation, journal and
checkpoint mechanisms were actually active remain controlled evidence.

`currentWorksetPhases` joins the seven original current-workset rows by
`record_id`. `targetTransferPublicationSeconds` is the recorded staged target
transfer/import or direct publication interval. It excludes other overhead
and is not the residual obtained by subtracting the first stage from wall
time. The adjacent control remains outside the direct triplicate.

M1 uses `tool=m` for MTV and `z` for ZeroV2V, with pair-local IDs. Both use the
same guest workload, but MTV's local-LVM-backed OpenShift target differs from
ZeroV2V's ZStack/Ceph target. MTV 2.12.9, OpenShift Virtualization 4.22.9 and
LVM Storage Operator 4.22.0 describe the tested competitor stack. The measured
effect is a complete-toolchain comparison, not a protocol-only speedup.

S6a is batch-grain: `seconds` is complete batch wall duration and `overlap`
records maximum concurrent forward-copy jobs. Throughput is declared guest
payload per batch time, not physical network bandwidth. `S6aStages` contains
state-transition phase durations for the 31 tasks in complete batches, not
all 35 attempts. The incomplete batch has no complete duration. Its two
additional accepted tasks and two failures are retained in the outcome
counts; those counters do not invent task durations.

D1r measures the interval from last source SQL response to first target
response. `success` refers to migration completion, not all levels of native
acceptance. `replaySeconds` is unmeasured; it must not be read as a database
replay benchmark. Windows reduction uses the two complete matched blocks,
whereas its cold-arm descriptive mean includes three runs.

V1r `verifierWallSeconds` excludes device setup and guest conversion.
`uniqueVerifiedBytes` counts each logical position once although source and
target are both read. Sample policy is sixteen 64-KiB blocks per disk.
`uniqueCoverageFraction` and `digestWallFraction` are fractions, not percent.

P1 `seconds`, diagnosis `seconds` and confirmation `seconds` use active-log
start to D pre-cleanup commit or Q cold completion. `ape` and
`absolutePercentageError` are fractions; `apePercent` is percent. Frozen
predictions are not refitted. The 12 P1 timing rows comprise ten formal
unassisted completions and two auxiliary acceptances; two original formal
failures have no invented completion times and remain in outcome counts.

`frozen-model.json` also permits reconstruction of the original predictions,
not just their errors. Rates are bytes/s, sizes bytes, and fixed/control costs
seconds. The six rate/conversion/control inputs are arithmetic means of three
calibration pairs from one lineage. Held-out Dr is a powered-off allocation
estimate, not a measured read counter; Ds and Dt use the mean calibration
ratios to Dr. Cross-OS transfer of these rates/costs remains an assumption.
No held-out timing is used in this reconstruction.

Diagnosis pairs ran in QD, DQ, QD order. `phaseSeconds` includes cleanup where
present and need not sum to the pre-cleanup endpoint. `sourceReadBytes`
measures source requests, not physical disk reads. Per-disk operations and
staging counters are retained using disk indices only. Disk index 1 is the
500-GiB disk in this fixed three-disk workload. Confirmation is one later DQ
pair, not a replacement for the earlier cohorts. It allowed MON_DISK_LOW only;
capacity checks, quiet window and 60-s dispatch budget remained unchanged.
Possible background backup overlap is operator-reported and not measured
per run; no causal field has been fabricated.

`outcomes.json` is explicitly aggregate evidence. It distinguishes original
acceptance, later corroboration, formal failures and fault-boundary recovery.
Three group-creation failures remain fail-closed; three final-CBT cases have
same-task recovery. It is not a per-run fault trace or evidence that newer
dispatch-window code was live-fault tested. These counts do not enlarge the
original 66-row matrix.
The original strict matrix exposes statuses and checkpoint/sample counts,
but successful fault rows do not include a full per-boundary trigger history.
The attribution of twelve process-exit recoveries to F1/F2/F4/F5 and the F5
attempt history therefore require controlled receipts. Likewise, incomplete
concurrency members, SQL original-acceptance versus later-corroboration, and
original model failures are reconciled in aggregate here rather than through
a public attempt-level ledger. These limits do not turn failed attempts into
completed timing observations.

## Correction and provenance

The exclusion description of historical M0031 is corrected in both the
master table and strict subset. Its source-read value remains 426616291328
bytes and its exclusion remains in force. No measured value, membership or
eligibility changed. The earlier Git/Zenodo release is not rewritten.

The network-contention descriptions for M0060, M0134 and M0173 omit the
background backup product name, using "backup workload" instead. This textual
generalization changes no measurement, cohort membership, eligibility or
recorded explanation of network contention. The retained source descriptions
and previous public archive are unchanged.

`data/revision/provenance.json` contains source hashes without private source
paths. `MANIFEST.sha256` covers the current release package. Hashes support integrity,
not independent validation of raw platform events. See
[DATA_DICTIONARY.md](DATA_DICTIONARY.md) for original fields.

## Material kept controlled

Do not add raw application databases or their keys, full runtime archives,
credentials, endpoint configuration, real VM/NIC/disk identifiers, console
captures or private operational controllers. They are unnecessary for
recalculating the published statistics and may expose infrastructure or data.
Raw fault and acceptance evidence remains subject to
[DATA_ACCESS.md](DATA_ACCESS.md). The migration-controller implementation is
not part of this data-and-analysis package; standalone simulation or local
unit tests must not be advertised as experimental migration reproduction.

## Before public release

Export only the paths listed in `MANIFEST.sha256`, plus the manifest itself.
Do not zip a development checkout wholesale: local `.git` metadata, caches,
editor files and unlisted backups are not release artifacts. Verify the
extracted archive again before upload. Named author contact details and ORCID
identifiers in citation/access metadata are intentional scholarly attribution,
not part of the deidentified experimental records.

Run the manifest, release audit, both analysis scripts and regression tests
from a clean standalone copy. Use public tag `v1.1.0` and create a new Zenodo
version rather than overwriting the 1.0.2 archive. The supplied 1.1.0 DOI is now
in the citation metadata and manuscript. Confirm that its public record contains
the intended version and files before marking publication verified or filling in
the release date. These local metadata updates do not upload or replace any
GitHub or Zenodo content.
