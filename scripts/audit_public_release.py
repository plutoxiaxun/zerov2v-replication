#!/usr/bin/env python3
"""Fail closed on public-data integrity and common deidentification hazards."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
DATA = PACKAGE / "data"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def audit_tables(failures: list[str]) -> None:
    expected_counts = {
        "controlled_trials.csv": 39,
        "controlled_summary.csv": 13,
        "conversion_environment_summary.csv": 2,
        "master_analysis.csv": 210,
        "strict_matrix.csv": 66,
        "current_workset.csv": 7,
        "boundary_cases.csv": 2,
        "final_core_validation.csv": 12,
        "sensitivity_rows.csv": 3,
    }
    tables = {name: read_csv(name) for name in expected_counts}
    for name, expected in expected_counts.items():
        require(len(tables[name]) == expected, f"{name}: expected {expected} rows", failures)
        if tables[name] and "record_id" in tables[name][0]:
            ids = [row["record_id"] for row in tables[name]]
            require(len(ids) == len(set(ids)), f"{name}: duplicate record_id", failures)

    controlled_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tables["controlled_trials.csv"]:
        controlled_groups[row["group"]].append(row)
    controlled_summary = tables["controlled_summary.csv"]
    require(
        {row["group"] for row in controlled_summary} == set(controlled_groups),
        "controlled_summary.csv: group membership differs from controlled trials",
        failures,
    )
    summary_fields = {
        "duration_mean_s": ("duration_s", statistics.mean),
        "duration_sd_s": ("duration_s", statistics.stdev),
        "duration_min_s": ("duration_s", min),
        "duration_max_s": ("duration_s", max),
        "downtime_mean_s": ("downtime_s", statistics.mean),
        "downtime_sd_s": ("downtime_s", statistics.stdev),
        "downtime_min_s": ("downtime_s", min),
        "downtime_max_s": ("downtime_s", max),
        "repair_mean_s": ("repair_s", statistics.mean),
        "repair_sd_s": ("repair_s", statistics.stdev),
        "final_cbt_mean_mib": ("final_cbt_mib", statistics.mean),
        "shutdown_mean_s": ("shutdown_s", statistics.mean),
        "final_sync_mean_s": ("final_sync_s", statistics.mean),
        "registration_mean_s": ("registration_s", statistics.mean),
        "residual_mean_s": ("residual_s", statistics.mean),
    }
    for summary_row in controlled_summary:
        rows = controlled_groups.get(summary_row["group"], [])
        require(
            int(summary_row["n"]) == len(rows),
            f"controlled_summary.csv: {summary_row['group']} count changed",
            failures,
        )
        for output_field, (input_field, operation) in summary_fields.items():
            values = [float(row[input_field]) for row in rows if row[input_field]]
            observed = summary_row[output_field]
            if not values:
                require(
                    observed == "",
                    f"controlled_summary.csv: {summary_row['group']} {output_field} should be blank",
                    failures,
                )
                continue
            expected = float(operation(values))
            require(
                observed != "" and abs(float(observed) - expected) <= 0.051,
                f"controlled_summary.csv: {summary_row['group']} {output_field} drifted",
                failures,
            )

    master_rows = tables["master_analysis.csv"]
    allowed_analysis_classes = {
        "operational_descriptive",
        "controlled_performance",
        "performance_sensitivity",
        "current_workset_performance",
        "sparsity_validation",
        "fault_recovery_validation",
        "correctness_confirmation",
    }
    require(
        all(row["analysis_class"] in allowed_analysis_classes for row in master_rows),
        "master_analysis.csv: missing or unknown analysis_class",
        failures,
    )
    require(
        all(
            row["performance_exclusion_code"] and row["performance_exclusion"]
            for row in master_rows
            if row["performance_eligible"] == "False"
        ),
        "master_analysis.csv: False performance eligibility lacks an explicit exclusion code or explanation",
        failures,
    )
    require(
        all(
            not row["performance_exclusion_code"]
            for row in master_rows
            if row["performance_eligible"] != "False"
        ),
        "master_analysis.csv: exclusion code assigned outside False performance eligibility",
        failures,
    )
    master_controlled = {
        (row["controlled_group"], row["controlled_trial_index"]): row
        for row in master_rows
        if row["controlled_trial"] == "1"
    }
    require(
        len(master_controlled) == len(tables["controlled_trials.csv"]),
        "master_analysis.csv: controlled row keys are incomplete or duplicated",
        failures,
    )
    for row in tables["controlled_trials.csv"]:
        key = (row["group"], row["trial"])
        master_row = master_controlled.get(key)
        require(master_row is not None, f"controlled_trials.csv: {key} is absent from master", failures)
        if master_row is None:
            continue
        field_pairs = (
            ("mode", "mode"),
            ("conversion_mode", "conversion_engine"),
            ("duration_s", "active_seconds"),
            ("final_cbt_mib", "final_cbt_mib"),
            ("shutdown_s", "shutdown_latency_seconds"),
            ("final_sync_s", "final_sync_seconds"),
            ("repair_s", "inplace_conversion_seconds"),
            ("registration_s", "registration_seconds"),
        )
        for controlled_field, master_field in field_pairs:
            observed = row[controlled_field]
            expected = master_row[master_field]
            try:
                equal = (observed == expected) or abs(float(observed) - float(expected)) <= 1e-9
            except ValueError:
                equal = observed == expected
            require(
                equal,
                f"controlled_trials.csv: {key} {controlled_field} differs from master",
                failures,
            )
        downtime_field = (
            "offline_cutover_seconds"
            if row["mode"] == "lowDowntimeRbd"
            else "reported_offline_seconds"
        )
        require(
            abs(float(row["downtime_s"]) - float(master_row[downtime_field])) <= 1e-9,
            f"controlled_trials.csv: {key} downtime differs from master",
            failures,
        )

    master = {row["record_id"]: row for row in master_rows}
    for name, flag in (
        ("strict_matrix.csv", "strict_matrix"),
        ("current_workset.csv", "current_workset"),
        ("final_core_validation.csv", "final_core"),
        ("sensitivity_rows.csv", "historical_sensitivity"),
    ):
        expected = {key for key, row in master.items() if row[flag] == "1"}
        observed = {row["record_id"] for row in tables[name]}
        require(observed == expected, f"{name}: subset membership mismatch", failures)
        require(
            all(row == master[row["record_id"]] for row in tables[name]),
            f"{name}: row differs from master_analysis.csv",
            failures,
        )

    strict = tables["strict_matrix.csv"]
    require(
        Counter(row["status"] for row in strict)
        == Counter({"succeeded": 63, "expected_failed": 3}),
        "strict_matrix.csv: status counts changed",
        failures,
    )
    require(
        all(
            row["fault_point"] == "direct_conversion.after"
            for row in strict
            if row["status"] == "expected_failed"
        ),
        "strict_matrix.csv: expected failure lacks the declared fault point",
        failures,
    )
    require(
        all(
            row["target_vm_state"] == "Running"
            for row in strict
            if row["status"] == "succeeded"
        ),
        "strict_matrix.csv: successful row is not Running",
        failures,
    )
    require(
        sum(int(float(row["target_disk_count"] or 0)) for row in strict if row["status"] == "succeeded")
        == 102,
        "strict_matrix.csv: successful target-disk count changed",
        failures,
    )
    require(
        sum(int(float(row["copy_sample_count"] or 0)) for row in strict) == 768,
        "strict_matrix.csv: sampled-block count changed",
        failures,
    )

    final_core = tables["final_core_validation.csv"]
    require(
        Counter(row["status"] for row in final_core)
        == Counter({"succeeded": 10, "expected_failed": 2}),
        "final_core_validation.csv: status counts changed",
        failures,
    )
    require(
        all(
            row["fault_point"] == "direct_conversion.after"
            for row in final_core
            if row["status"] == "expected_failed"
        ),
        "final_core_validation.csv: expected failure lacks the declared fault point",
        failures,
    )
    require(
        all(
            row["target_disk_count"] == "2"
            and row["target_vm_state"] == "Running"
            and row["console_sample_count"] == "3"
            for row in final_core
            if row["status"] == "succeeded"
        ),
        "final_core_validation.csv: successful topology or console evidence changed",
        failures,
    )
    require(
        {row["code_commit"] for row in final_core}
        == {"3681503dd376425eec126ea66249bc2cbcbe377f"},
        "final_core_validation.csv: application commit changed",
        failures,
    )
    require(
        all(row["source_checkpoint_recorded"] == "True" for row in final_core),
        "final_core_validation.csv: source checkpoint evidence is incomplete",
        failures,
    )
    require(
        all(
            row["performance_eligible"] == "False"
            and row["performance_exclusion"]
            == "final-core correctness-only cohort; excluded from performance aggregates"
            for row in final_core
        ),
        "final_core_validation.csv: correctness-only performance exclusion changed",
        failures,
    )

    boundary = {row["path"]: row for row in tables["boundary_cases.csv"]}
    require(
        set(boundary) == {"direct_full_read", "staged_qcow2"},
        "boundary_cases.csv: path membership changed",
        failures,
    )
    if set(boundary) == {"direct_full_read", "staged_qcow2"}:
        require(
            boundary["direct_full_read"]["active_seconds"] == "6840.0"
            and boundary["staged_qcow2"]["active_seconds"] == "1657.0",
            "boundary_cases.csv: frozen timing changed",
            failures,
        )
        require(
            all(
                row["record_id"] in master
                and row["active_seconds"] == master[row["record_id"]]["active_seconds"]
                and row["provisioned_gib"]
                == master[row["record_id"]]["allocated_capacity_gib"]
                for row in boundary.values()
            ),
            "boundary_cases.csv: rows differ from master_analysis.csv",
            failures,
        )

    historical = [
        row
        for row in tables["master_analysis.csv"]
        if row["historical_primary"] == "1"
    ]
    direct = [row for row in historical if row["mode"] != "coldQcow2"]
    require(
        len({row["observed_vm_id"] for row in historical if row["observed_vm_id"]})
        == 46,
        "master_analysis.csv: historical VM pseudonym count changed",
        failures,
    )
    require(
        Counter(row["guest_os_family"] for row in direct)
        == Counter({"CentOS/RHEL": 15, "UOS": 3, "Windows": 32, "openEuler": 42}),
        "master_analysis.csv: direct-path guest OS counts changed",
        failures,
    )
    require(
        Counter(
            row["allocation_evidence_tier"]
            for row in direct
            if row["allocation_evidence_tier"]
        )
        == Counter(
            {
                "historical_csv": 51,
                "historical_manual": 1,
                "paired_run": 1,
                "task_recorded": 39,
            }
        ),
        "master_analysis.csv: allocation evidence tiers changed",
        failures,
    )

    environments = {
        row["conversion_mode"]: row
        for row in tables["conversion_environment_summary.csv"]
    }
    require(
        environments
        == {
            "TCG": {
                "conversion_mode": "TCG",
                "csv_count": "44",
                "parsed_count": "42",
                "min_s": "226.0",
                "max_s": "745.8",
                "avg_s": "361.1",
                "median_s": "334.7",
            },
            "KVM": {
                "conversion_mode": "KVM",
                "csv_count": "48",
                "parsed_count": "48",
                "min_s": "38.2",
                "max_s": "148.0",
                "avg_s": "61.8",
                "median_s": "47.5",
            },
        },
        "conversion_environment_summary.csv: frozen values changed",
        failures,
    )


def audit_analysis_summary(failures: list[str]) -> None:
    path = DATA / "analysis_summary.json"
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"analysis_summary.json is not valid JSON: {exc}")
        return

    expected_row_counts = {
        "controlled_trials.csv": 39,
        "conversion_environment_summary.csv": 2,
        "master_analysis.csv": 210,
        "strict_matrix.csv": 66,
        "current_workset.csv": 7,
        "final_core_validation.csv": 12,
        "sensitivity_rows.csv": 3,
        "boundary_cases.csv": 2,
    }
    require(
        summary.get("public_row_counts") == expected_row_counts,
        "analysis_summary.json: public row counts changed",
        failures,
    )

    master = read_csv("master_analysis.csv")
    source = summary.get("source_summary", {})
    require(source.get("rows") == len(master), "analysis_summary.json: row count drifted", failures)
    require(
        source.get("unique_job_ids") == len(master),
        "analysis_summary.json: source job count drifted",
        failures,
    )
    role_fields = (
        "historical_primary",
        "historical_sensitivity",
        "controlled_trial",
        "strict_matrix",
        "current_workset",
        "sparse_policy_trial",
        "final_core",
    )
    observed_roles = {
        field: sum(row[field] == "1" for row in master) for field in role_fields
    }
    require(
        source.get("population_counts") == observed_roles,
        "analysis_summary.json: population counts differ from master_analysis.csv",
        failures,
    )

    primary = [
        row
        for row in master
        if row["historical_primary"] == "1"
        and row["mode"] == "lowDowntimeRbd"
        and row["offline_cutover_seconds"]
    ]
    sensitivity = [
        row
        for row in master
        if row["historical_sensitivity"] == "1"
        and row["mode"] == "lowDowntimeRbd"
        and row["offline_cutover_seconds"]
    ]
    strata = {
        "low_downtime_primary": primary,
        "low_downtime_primary_without_post_shutdown_recovery": [
            row for row in primary if row["outage_recovery_affected"] == "0"
        ],
        "low_downtime_primary_post_shutdown_recovery": [
            row for row in primary if row["outage_recovery_affected"] == "1"
        ],
        "low_downtime_all_without_post_shutdown_recovery": [
            row
            for row in primary + sensitivity
            if row["outage_recovery_affected"] == "0"
        ],
        "low_downtime_all_completed": primary + sensitivity,
    }
    for name, rows in strata.items():
        values = [float(row["offline_cutover_seconds"]) for row in rows]
        observed = source.get(name, {})
        expected = {
            "n": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "sample_sd": statistics.stdev(values),
        }
        require(
            observed.keys() == expected.keys()
            and all(abs(float(observed[key]) - float(value)) <= 1e-9 for key, value in expected.items()),
            f"analysis_summary.json: {name} differs from public rows",
            failures,
        )

    release = summary.get("release_evidence", {})
    require(
        release.get("final_core_code_commit")
        == ["3681503dd376425eec126ea66249bc2cbcbe377f"],
        "analysis_summary.json: final-core commit changed",
        failures,
    )
    require(
        release.get("final_core_evidence_file_count") == 42
        and release.get("final_core_evidence_files_verified") == 42,
        "analysis_summary.json: final-core evidence-file counts changed",
        failures,
    )


def audit_figure_table_trace(failures: list[str]) -> None:
    path = DATA / "figure_table_trace.json"
    require(path.exists(), "figure_table_trace.json is missing", failures)
    if not path.exists():
        return
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"figure_table_trace.json is not valid JSON: {exc}")
        return
    entries = document.get("entries", [])
    require(len(entries) == 29, "figure_table_trace.json: expected 29 entries", failures)
    required = {
        "artifact_id",
        "source_data",
        "selection",
        "transformation",
        "caption_claim",
        "supported_manuscript_claims",
        "limitations",
    }
    expected_artifacts = ({f"Table {i}" for i in range(1,21)}
                          | {f"Figure {i}" for i in range(1,7)}
                          | {"Supplement Figure S1", "Supplement Figure S2", "Recovery boundary paragraphs"})
    observed_artifacts = set()
    for index, entry in enumerate(entries, 1):
        missing = sorted(required - set(entry))
        require(
            not missing,
            f"figure_table_trace.json entry {index}: missing {', '.join(missing)}",
            failures,
        )
        observed_artifacts.add(entry.get("artifact_id", ""))
        for source_name in entry.get("source_data", []):
            require(
                (DATA / source_name).is_file(),
                f"figure_table_trace.json entry {index}: missing source {source_name}",
                failures,
            )
        for script in entry.get("scripts", []):
            require((PACKAGE / script).is_file(), f"Missing trace script {script}", failures)
        require(
            bool(entry.get("supported_manuscript_claims")),
            f"figure_table_trace.json entry {index}: no supported claim",
            failures,
        )
        require(
            bool(entry.get("limitations")),
            f"figure_table_trace.json entry {index}: no limitation",
            failures,
        )
    require(
        observed_artifacts == expected_artifacts,
        "figure_table_trace.json: artifact set changed",
        failures,
    )


def audit_text(failures: list[str]) -> None:
    patterns = {
        "private IPv4 address": re.compile(
            r"(?<![\d.])(?:10|127|169\.254|172\.(?:1[6-9]|2\d|3[01])|192\.168)(?:\.\d{1,3}){2,3}(?![\d.])"
        ),
        "UUID": re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
        "32-character internal identifier": re.compile(r"\b[0-9a-f]{32}\b", re.IGNORECASE),
        "source snapshot identifier": re.compile(r"\bsnapshot-\d+\b", re.IGNORECASE),
        "credential assignment": re.compile(
            r"(?i)(password|passwd|secret|token|api[_-]?key|credential)\s*[:=]"
        ),
        "internal absolute path": re.compile(
            r"(?<!\w)/(?:var|opt|home|Users|data|tmp|etc)/[^\s`\]\"']+"
        ),
    }
    for path in sorted(PACKAGE.rglob("*")):
        relative = path.relative_to(PACKAGE)
        if (
            not path.is_file()
            or path.name == "MANIFEST.sha256"
            or ".git" in relative.parts
        ):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in patterns.items():
            if pattern.search(content):
                failures.append(f"{path.relative_to(PACKAGE)}: contains {label}")


def audit_packaging_hygiene(failures: list[str]) -> None:
    for path in sorted(PACKAGE.rglob("*")):
        relative = path.relative_to(PACKAGE)
        if relative.parts[0] == '.git':
            continue
        require(not path.is_symlink(), f"{relative}: symlink must not be released", failures)
        if path.is_symlink() or not path.is_file():
            continue
        require(path.name == 'MANIFEST.sha256' or path.suffix in {'.py','.md','.txt','.json','.csv','.cff'},
                f"{relative}: unexpected binary/archive or file type", failures)
        require(
            not any(part.startswith(".") for part in relative.parts)
            and "__pycache__" not in relative.parts
            and path.suffix not in {".pyc", ".pyo"},
            f"{relative}: hidden or generated local file must not be released",
            failures,
        )


def audit_document_links(failures: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in sorted(PACKAGE.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(content):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_target = target.split("#", 1)[0]
            if not local_target:
                continue
            require(
                (path.parent / local_target).resolve().is_file(),
                f"{path.relative_to(PACKAGE)}: broken local link {target}",
                failures,
            )


def audit_release_metadata(failures: list[str]) -> None:
    citation = PACKAGE / "CITATION.cff"
    require(citation.exists(), "CITATION.cff is missing", failures)
    if citation.exists():
        content = citation.read_text(encoding="utf-8")
        require("TODO" not in content, "CITATION.cff contains TODO", failures)
        require("zenodo.TODO" not in content, "CITATION.cff DOI is incomplete", failures)
        status = json.loads((PACKAGE / 'RELEASE_STATUS.json').read_text())
        version = re.search(r'^version:\s*(\S+)\s*$', content, re.M)
        require(version is not None and version[1] == status.get('version'),
                'Citation and release-status versions must match', failures)
        require(re.fullmatch(r'\d+\.\d+\.\d+', status.get('version', '')) is not None,
                'Release version must not contain a prerelease suffix', failures)
        if status['status'] == 'release_artifact':
            dois = re.findall(r'^doi:\s*(\S+)\s*$', content, re.M)
            require(dois == [status.get('newVersionDOI')] and
                    re.fullmatch(r'10\.\d{4,9}/\S+', status.get('newVersionDOI') or '') is not None,
                    'Citation DOI must match the supplied new-version DOI', failures)
            require(not re.search(r'^date-released:', content, re.M),
                    'Artifact citation must not add an undeclared release date', failures)
            require('publicUploadPerformed' not in status and 'doiVerification' not in status,
                    'Artifact metadata must not contain mutable publication-state fields', failures)
        elif status['status'] == 'reserved_doi_pending_publication':
            dois = re.findall(r'^doi:\s*(\S+)\s*$', content, re.M)
            require(dois == [status.get('newVersionDOI')] and
                    re.fullmatch(r'10\.\d{4,9}/\S+', status.get('newVersionDOI') or '') is not None,
                    'Citation DOI must match the supplied new-version DOI', failures)
            require(status['publicUploadPerformed'] is False and
                    status.get('doiVerification', {}).get('publicAvailabilityVerified') is False,
                    'Unverified DOI must not claim verified publication', failures)
            require(not re.search(r'^date-released:', content, re.M),
                    'Unverified publication must not invent a release date', failures)
        elif not status['publicUploadPerformed']:
            require(not re.search(r'^doi:|^date-released:', content, re.M),
                    'Unpublished release must not borrow an old archive DOI/date', failures)
            require(status['newVersionDOI'] is None and status['status'] == 'local_release_not_uploaded',
                    'Unpublished release metadata conflicts', failures)
    require(
        not (PACKAGE / "CITATION.cff.template").exists(),
        "CITATION.cff.template must not be shipped in the final release",
        failures,
    )
    require(
        (PACKAGE / "LICENSE-APACHE-2.0.txt").exists(),
        "Apache-2.0 license text is missing",
        failures,
    )
    require(
        (PACKAGE / "LICENSE-CC-BY-4.0.txt").exists(),
        "CC BY 4.0 license text is missing",
        failures,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release-ready",
        action="store_true",
        help="also require final citation metadata and complete license texts",
    )
    args = parser.parse_args()
    failures: list[str] = []
    audit_tables(failures)
    audit_analysis_summary(failures)
    audit_figure_table_trace(failures)
    from analyze_revision import analyze
    try:
        analyze()
    except (AssertionError, KeyError, ValueError, OSError) as exc:
        failures.append(f"revision data: {type(exc).__name__}: {exc}")
    audit_text(failures)
    audit_packaging_hygiene(failures)
    audit_document_links(failures)
    if args.release_ready:
        audit_release_metadata(failures)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print("PASS: public release data, cohort integrity, and deidentification checks")


if __name__ == "__main__":
    main()
