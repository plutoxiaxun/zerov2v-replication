#!/usr/bin/env python3
"""Recalculate manuscript-facing statistics from the public CSV files."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [float(row[field]) for row in rows if row.get(field) not in (None, "")]


def mean(rows: list[dict[str, str]], field: str) -> float:
    return statistics.mean(values(rows, field))


def controlled_metrics() -> dict[str, object]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv("controlled_trials.csv"):
        groups[row["group"]].append(row)

    b_stage = mean(groups["VM-B / QCOW2 staging"], "duration_s")
    b_kvm = mean(groups["VM-B / Cold direct KVM"], "duration_s")
    c_stage = mean(groups["VM-C / QCOW2 staging"], "duration_s")
    c_kvm = mean(groups["VM-C / Cold direct KVM"], "duration_s")
    b_tcg_repair = mean(groups["VM-B / Cold direct TCG"], "repair_s")
    b_kvm_repair = mean(groups["VM-B / Cold direct KVM"], "repair_s")
    low = {}
    for vm in "EFGH":
        tcg = mean(groups[f"VM-{vm} / Low-downtime TCG"], "downtime_s")
        kvm = mean(groups[f"VM-{vm} / Low-downtime KVM"], "downtime_s")
        low[vm] = 100 * (1 - kvm / tcg)
    return {
        "row_count": sum(len(rows) for rows in groups.values()),
        "triplicate_group_count": len(groups),
        "historical_path_observation_role": "sensitivity_only",
        "historical_path_limitations": [
            "VM-B is an extremely sparse 500-GiB thick-lazy boundary case",
            "VM-B staging jobs have 51--52 s of target-import tail overlap",
            "VM-C has no triplicate TCG cell",
        ],
        "vm_b_direct_kvm_active_reduction_pct": 100 * (1 - b_kvm / b_stage),
        "vm_c_direct_kvm_active_reduction_pct": 100 * (1 - c_kvm / c_stage),
        "vm_b_conversion_speedup_tcg_over_kvm": b_tcg_repair / b_kvm_repair,
        "low_downtime_reduction_pct": low,
    }


def operational_archive_metrics() -> dict[str, object]:
    rows = [
        row
        for row in read_csv("master_analysis.csv")
        if row["historical_primary"] == "1"
    ]
    direct = [row for row in rows if row["mode"] != "coldQcow2"]
    return {
        "primary_rows": len(rows),
        "observed_vm_ids": len(
            {row["observed_vm_id"] for row in rows if row["observed_vm_id"]}
        ),
        "direct_rows": len(direct),
        "direct_provisioned_tib": sum(values(direct, "allocated_capacity_gib")) / 1024,
        "direct_guest_os_counts": dict(
            sorted(Counter(row["guest_os_family"] for row in direct).items())
        ),
        "allocation_evidence_tier_counts": dict(
            sorted(
                Counter(
                    row["allocation_evidence_tier"]
                    for row in direct
                    if row["allocation_evidence_tier"]
                ).items()
            )
        ),
        "direct_ceph_allocation_tib": sum(values(direct, "ceph_actual_capacity_gib"))
        / 1024,
    }


def conversion_environment_metrics() -> dict[str, object]:
    rows = read_csv("conversion_environment_summary.csv")
    return {
        row["conversion_mode"]: {
            "csv_count": int(row["csv_count"]),
            "parsed_count": int(row["parsed_count"]),
            "min_s": float(row["min_s"]),
            "max_s": float(row["max_s"]),
            "mean_s": float(row["avg_s"]),
            "median_s": float(row["median_s"]),
        }
        for row in rows
    }


def current_workset_metrics() -> dict[str, object]:
    rows = read_csv("current_workset.csv")
    staging = [row for row in rows if row["mode"] == "coldQcow2"]
    direct = [row for row in rows if row["conversion_engine"] == "direct"]
    if not direct:
        direct = [row for row in rows if row["mode"] == "onlineSnapshotDirectRbd" and row["conversion_engine"] != "direct_control"]
    staging_stage = statistics.median(values(staging, "measured_stage_seconds"))
    direct_stage = statistics.median(values(direct, "measured_stage_seconds"))
    staging_wall = statistics.median(values(staging, "wall_seconds"))
    direct_wall = statistics.median(values(direct, "wall_seconds"))
    return {
        "row_count": len(rows),
        "staging_source_read_gib": values(staging, "source_read_gib"),
        "direct_source_read_gib": values(direct, "source_read_gib"),
        "direct_stage_increase_pct": 100 * (direct_stage / staging_stage - 1),
        "direct_complete_wall_reduction_pct": 100 * (1 - direct_wall / staging_wall),
    }


def controlled_path_metrics() -> dict[str, object]:
    rows = read_csv("master_analysis.csv")
    p1 = [row for row in rows if row["sparse_policy_trial"] == "1" and row["workload_id"] == "VM-P1"]
    p1_staging = [row for row in p1 if row["mode"] == "coldQcow2"]
    p1_direct = [
        row
        for row in p1
        if row["mode"] == "onlineSnapshotDirectRbd"
        and row["conversion_engine"] == "full_scan"
    ]
    l1 = [
        row
        for row in rows
        if row["strict_matrix"] == "1"
        and row["workload_id"] == "L1"
        and row["performance_eligible"] == "True"
    ]
    l1_staging = [row for row in l1 if row["mode"] == "coldQcow2"]
    l1_direct = [
        row
        for row in l1
        if row["mode"] == "onlineSnapshotDirectRbd"
        and row["conversion_engine"] == "virt_v2v_output"
    ]
    if not all(len(group) == 3 for group in (p1_staging, p1_direct, l1_staging, l1_direct)):
        raise RuntimeError("controlled path cohorts must contain three rows per path")
    p1_staging_center = statistics.mean(values(p1_staging, "active_seconds"))
    p1_direct_center = statistics.mean(values(p1_direct, "active_seconds"))
    l1_staging_center = statistics.mean(values(l1_staging, "measured_stage_seconds"))
    l1_direct_center = statistics.mean(values(l1_direct, "measured_stage_seconds"))
    return {
        "P1": {
            "metric": "complete_active_duration_mean",
            "provisioned_gib": 50,
            "staging_source_read_percent": None,
            "direct_source_read_percent": 100 * statistics.mean(values(p1_direct, "source_read_gib")) / 50,
            "direct_reduction_percent": 100 * (1 - p1_direct_center / p1_staging_center),
        },
        "L1": {
            "metric": "source_read_conversion_duration_mean",
            "provisioned_gib": 50,
            "staging_source_read_percent": 100 * statistics.mean(values(l1_staging, "source_read_gib")) / 50,
            "direct_source_read_percent": 100 * statistics.mean(values(l1_direct, "source_read_gib")) / 50,
            "direct_reduction_percent": 100 * (1 - l1_direct_center / l1_staging_center),
        },
    }


def exact_two_sided_sign_p(positive: int, total: int) -> float:
    probabilities = [math.comb(total, value) / (2**total) for value in range(total + 1)]
    observed = probabilities[positive]
    return sum(value for value in probabilities if value <= observed + 1e-15)


def path_direction_audit() -> dict[str, object]:
    master = read_csv("master_analysis.csv")
    controlled = read_csv("controlled_trials.csv")
    effects: list[dict[str, object]] = []

    def append_effect(
        cohort: str,
        staging: list[dict[str, str]],
        direct: list[dict[str, str]],
        metric: str,
        evidence_class: str,
    ) -> None:
        staging_center = mean(staging, metric)
        direct_center = mean(direct, metric)
        reduction = 100 * (1 - direct_center / staging_center)
        effects.append(
            {
                "cohort": cohort,
                "metric": metric,
                "evidence_class": evidence_class,
                "staging_n": len(staging),
                "direct_n": len(direct),
                "staging_mean_seconds": staging_center,
                "direct_mean_seconds": direct_center,
                "direct_reduction_percent": reduction,
                "direction": "direct_faster" if reduction > 0 else "direct_not_faster",
            }
        )

    for workload in ("VM-P1", "VM-P2"):
        rows = [row for row in master if row["sparse_policy_trial"] == "1" and row["workload_id"] == workload]
        append_effect(
            workload,
            [row for row in rows if row["mode"] == "coldQcow2"],
            [row for row in rows if row["conversion_engine"] == "full_scan"],
            "active_seconds",
            "directly_checkable",
        )
    for workload in ("L1", "W2"):
        rows = [
            row
            for row in master
            if row["strict_matrix"] == "1"
            and row["workload_id"] == workload
            and row["performance_eligible"] == "True"
        ]
        append_effect(
            workload,
            [row for row in rows if row["mode"] == "coldQcow2"],
            [row for row in rows if row["conversion_engine"] == "virt_v2v_output"],
            "measured_stage_seconds",
            "directly_checkable",
        )
    rows = [row for row in master if row["current_workset"] == "1"]
    append_effect(
        "L2-current-stage",
        [row for row in rows if row["mode"] == "coldQcow2"],
        [row for row in rows if row["conversion_engine"] == "direct"],
        "measured_stage_seconds",
        "directly_checkable",
    )
    for workload in ("VM-B", "VM-C"):
        append_effect(
            workload,
            [row for row in controlled if row["group"] == f"{workload} / QCOW2 staging"],
            [row for row in controlled if row["group"] == f"{workload} / Cold direct KVM"],
            "duration_s",
            "historical_sensitivity",
        )

    def summarize(selected: list[dict[str, object]]) -> dict[str, object]:
        direct_faster = sum(item["direction"] == "direct_faster" for item in selected)
        return {
            "cohorts": len(selected),
            "direct_faster": direct_faster,
            "direct_not_faster": len(selected) - direct_faster,
            "exact_two_sided_sign_p": exact_two_sided_sign_p(direct_faster, len(selected)),
        }

    directly_checkable = [
        item for item in effects if item["evidence_class"] == "directly_checkable"
    ]
    return {
        "effects": effects,
        "all_repeated_or_matched": summarize(effects),
        "directly_checkable": summarize(directly_checkable),
        "interpretation": "Effect magnitudes are not pooled because active-path and source-read/conversion metrics differ.",
    }


def boundary_case_metrics() -> dict[str, object]:
    rows = read_csv("boundary_cases.csv")
    keyed = {row["path"]: row for row in rows}
    direct = float(keyed["direct_full_read"]["active_seconds"])
    staging = float(keyed["staged_qcow2"]["active_seconds"])
    return {
        "case_id": "B600",
        "provisioned_gib": 600,
        "direct_full_read_minutes": direct / 60,
        "staged_qcow2_minutes": staging / 60,
        "direct_increase_percent": 100 * (direct / staging - 1),
        "evidence_role": "boundary_counterexample",
    }


def matrix_metrics() -> dict[str, object]:
    rows = read_csv("strict_matrix.csv")
    states = Counter(row["status"] for row in rows)
    return {
        "row_count": len(rows),
        "status_counts": dict(sorted(states.items())),
        "target_disk_count": sum(int(float(row["target_disk_count"] or 0)) for row in rows if row["status"] == "succeeded"),
        "copy_sample_count": sum(int(float(row["copy_sample_count"] or 0)) for row in rows),
        "group_checkpoint_rows": sum(row["commit_mode"] == "group_checkpoint" for row in rows),
        "expected_failure_fault_points": dict(
            sorted(
                Counter(
                    row["fault_point"]
                    for row in rows
                    if row["status"] == "expected_failed"
                ).items()
            )
        ),
    }


def final_core_metrics() -> dict[str, object]:
    rows = read_csv("final_core_validation.csv")
    states = Counter(row["status"] for row in rows)
    succeeded = [row for row in rows if row["status"] == "succeeded"]
    expected_failed = [row for row in rows if row["status"] == "expected_failed"]
    return {
        "row_count": len(rows),
        "status_counts": dict(sorted(states.items())),
        "code_commits": sorted({row["code_commit"] for row in rows if row["code_commit"]}),
        "source_checkpoints_recorded": sum(
            row["source_checkpoint_recorded"] == "True" for row in rows
        ),
        "expected_fault_points": dict(
            sorted(Counter(row["fault_point"] for row in expected_failed).items())
        ),
        "successful_two_disk_targets": sum(row["target_disk_count"] == "2" for row in succeeded),
        "successful_running_targets": sum(row["target_vm_state"] == "Running" for row in succeeded),
        "successful_console_samples": sum(
            int(float(row["console_sample_count"] or 0)) for row in succeeded
        ),
    }


def main() -> None:
    result = {
        "operational_archive": operational_archive_metrics(),
        "controlled": controlled_metrics(),
        "conversion_environment": conversion_environment_metrics(),
        "controlled_paths": controlled_path_metrics(),
        "path_direction_audit": path_direction_audit(),
        "boundary_case": boundary_case_metrics(),
        "current_workset": current_workset_metrics(),
        "strict_matrix": matrix_metrics(),
        "final_core": final_core_metrics(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
