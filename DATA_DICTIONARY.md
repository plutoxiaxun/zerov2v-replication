# Public Data Dictionary

## File grain

| File | Grain | Purpose |
|---|---|---|
| `master_analysis.csv` | One deidentified migration observation | Union table used to derive public subsets and descriptive statistics |
| `strict_matrix.csv` | One predefined protocol-matrix row | Protocol completion, recovery, topology, sampling, and console evidence |
| `controlled_trials.csv` | One controlled repetition | Historical path and TCG/KVM comparisons |
| `controlled_summary.csv` | One controlled group | Convenience summary; it has no `record_id` because it is aggregated |
| `conversion_environment_summary.csv` | One execution environment | Deidentified aggregate behind the descriptive TCG/KVM guest-adaptation table |
| `current_workset.csv` | One current-workset repetition or adjacent control | Staged/direct comparison after the source workset changed |
| `boundary_cases.csv` | One path in a named boundary pair | Reproduces the 600-GiB full-read counterexample |
| `sensitivity_rows.csv` | One retained confounded observation | Shows the effect of known shared-network contention |
| `final_core_validation.csv` | One final fault-validation run | Correctness confirmation only; excluded from all performance aggregates |
| `analysis_summary.json` | One release summary | Cohort counts, downtime strata, and hashes of retained source records |
| `figure_table_trace.json` | One trace entry per data-bearing artifact | Public input, transformation, supported claim, and limitation for manuscript figures and tables |

`record_id` values are release-local pseudonyms. They are stable within the
frozen release but are not source job identifiers. Workload labels such as
`W1`, `L2`, and `VM-P1` are deidentified cohort labels.

For historical rows, `observed_vm_id` is a release-local pseudonym for the
observed VM name. It preserves repeated-name counts without disclosing the
original name. The field groups repeated observations by name; it does not
imply that similarly named clones are independent workloads.
`guest_os_family` is the broad, manually reviewed operating-system family used
for coverage counts.

## Selection fields

- `analysis_roles` and the seven Boolean role columns identify every cohort to
  which a row belongs. Roles may overlap; their counts therefore must not be
  summed to estimate the number of unique rows.
- `analysis_class` assigns one non-overlapping analytical use to every row:
  operational description, controlled performance, performance sensitivity,
  current-workset performance, sparsity validation, fault-recovery validation,
  or final correctness confirmation.
- `performance_eligible` is a row-level eligibility flag within the row's
  original experiment design. All `final_core=1` rows are exported as
  `False` with an explicit correctness-only exclusion, even when the executed
  path was structurally performance-capable.
- `performance_exclusion_code` gives every `False` row a stable,
  machine-readable reason. `performance_exclusion` supplies the corresponding
  human-readable explanation. Fault-recovery and sparsity-validation rows were
  designed to test correctness rather than estimate migration performance;
  the seven excluded rows from the `PERFORMANCE` group retain their specific
  repair, convergence, or contention reason.
- Empty fields mean "not measured" or "not applicable". They are not zero.

## Provenance fields

- `attempt` is the application-side attempt number retained by the source
  record. It is provenance, not an independent experimental repetition.
- `code_commit` records the tested application revision when it was captured.
  Empty values belong mainly to earlier operational records for which the
  revision was not preserved in the normalized source table.
- `source_checkpoint_recorded` states whether the source record retained a
  checkpoint reference. Infrastructure-specific checkpoint names are not
  published.

## Timing fields

- `active_seconds`: complete active duration under the source record's mode.
- `measured_stage_seconds`: explicitly delimited source-read/conversion stage.
- `wall_seconds`: task creation to terminal success, including later target
  transfer or publication where present.
- `reported_offline_seconds`: historical reported offline interval.
- `offline_cutover_seconds`: power-off request to target VM resource creation.
  It excludes target boot and application recovery.
- `shutdown_latency_seconds`, `final_sync_seconds`,
  `inplace_conversion_seconds`, and `registration_seconds` are phase timings
  only where the required markers exist.

Timing fields with different definitions are kept separate. The public
analysis compares like-defined fields within each cohort.

## Volume and output fields

- `source_read_bytes` and `source_read_gib` are observed source-read counters.
- `output_bytes` and `output_gib` use the method named by `output_metric`.
- A staged artifact's `stat().st_size` and Ceph `rbd du` allocated bytes are
  different measures and must not be compared as write amplification.
- `allocated_capacity_gib` is provisioned capacity, whereas
  `ceph_actual_capacity_gib` is observed Ceph allocation where available.
- `allocation_evidence_tier` records whether that allocation came from a task
  record, the retained historical CSV, a manual verification, or a paired-run
  substitution. The mixed tiers may be summed for descriptive coverage but not
  treated as one uniform performance measurement.

## Protocol evidence fields

- `expected_result`, `fault_point`, and `fault_behavior` describe declared
  fault rows. Historical and final-core F3 expected failures use
  `direct_conversion.after`.
- `target_disk_count` and `target_vm_state` are target control-plane evidence.
  `Running` records the control-plane state; network and application readiness
  were not measured by this field.
- `copy_sample_count` counts configured sampled-block checks; it is not a
  whole-disk hash.
- `console_sample_count` counts retained console observations; it supports the
  reported boot gate but is not an application-level probe.
- `commit_mode`, `commit_state`, and `commit_epoch` describe the generation's
  storage publication boundary where applicable.

## Summary terminology

`duplicate_source_records` in `analysis_summary.json` counts normalized rows
that had more than one candidate source-log record during reconciliation. It
does not mean that the public table contains duplicate rows. The reconciler
reported zero boundary conflicts, and every public `record_id` is unique.
`low_downtime_boundary_basis_counts` and `duplicate_source_records` are retained
reconciliation diagnostics. Their source-log identifiers are not published,
so these two aggregates cannot be reconstructed from the deidentified rows.
