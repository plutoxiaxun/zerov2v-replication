# Results and Supporting Data

This table links the main reported results to the released files and states
what can and cannot be inferred from each measurement.

| Result | Public data | Interpretation |
|---|---|---|
| The 66-run protocol matrix contains 63 successful runs and three declared fault injections that failed as expected. | `strict_matrix.csv` | These runs check the evaluated migration path, target topology, and boot gate. They do not measure application availability. |
| Thirty-three successful two-disk direct, low-downtime, sparsity, or fault runs recorded a group checkpoint and a common disk epoch. | `strict_matrix.csv` | The records support the reported multi-disk publication boundary. They are not a test of guest-filesystem or application-transaction consistency. |
| Across seven repeated or matched path cohorts, direct output is faster in four and not faster in three. In the five cohorts with directly checkable timing and source-read boundaries, it is faster in two and not faster in three. | `master_analysis.csv`, `controlled_trials.csv`, `current_workset.csv`, `analysis_summary.json` | The exact two-sided sign-test value is 1.0 in both summaries. The data therefore do not support a general speed advantage for either path. |
| The historical VM-B and VM-C comparisons show 16.8% and 21.3% shorter direct durations. | `controlled_trials.csv` | These are sensitivity results. VM-B is an extremely sparse thick-lazy case with staging-tail overlap, and VM-C lacks a triplicate TCG cell. |
| Explicit VDDK extents are 3.9% and 20.2% slower than the qemu-img sparse path in the two evaluated workloads. | `master_analysis.csv`, `controlled_trials.csv` | Each cell has three repetitions. The result is retained as a negative finding and is not generalized beyond these workloads. |
| The strict matrix includes 36 performance-group rows, of which 29 meet the predefined performance criteria. | `strict_matrix.csv` | Seven rows are excluded because of repair paths, invalid read volume, full-scan convergence, or known vSAN contention. Their functional results remain in the table. |
| Thirty successful runs contain 768 sampled 64-KiB block comparisons and retained console observations. | `strict_matrix.csv` | The checks establish equality at the sampled positions and support the reported boot gate; they are not whole-disk hashes or application-level probes. |
| The final 12-run cohort contains ten successes and two declared F3 failures at `direct_conversion.after`. | `final_core_validation.csv`, `analysis_summary.json` | This cohort checks the final tested revision. It is reported separately from the 66-run matrix and is excluded from performance calculations. |
| In the current-workset comparison, source reads remain within the declared drift limit while staged runs vary more in duration. | `current_workset.csv`, `analysis_summary.json` | The retained records do not establish that earlier log deletion caused the timing difference. |

## Cohort boundaries

1. The historical operational archive is used for descriptive results.
2. The 66-run matrix evaluates protocol and recovery behavior.
3. Supplemental performance runs do not replace earlier successful runs.
4. The current workset is analyzed separately from the earlier source state.
5. The final 12-run cohort is used only for correctness checks and does not
   change the historical denominators.
