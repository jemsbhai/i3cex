"""Validate the frozen I3C-EX all-axis bakeoff design manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "experiments" / "bakeoff" / "manifest-v2.json"
DEFAULT_HASH = REPOSITORY_ROOT / "experiments" / "bakeoff" / "manifest-v2.sha256"
EXPECTED_BASELINE_COMMIT = "e0a098c3dbc30bfe8f2c59102f6472b174c286c9"
EXPECTED_V1_SHA256 = "157413beeb461a42c531bb1422d48bd345e5cda4ee87ccac185f35459db4f033"
EXPECTED_GRID_CELLS = 84_240
EXPECTED_EXTENSIBILITY_CELLS = 192
EXPECTED_FUZZ_EXECUTIONS_PER_CANDIDATE = 40_000_000
FULL_COVERAGE_PERCENT = 100
HASH_SIDECAR_FIELD_COUNT = 2
MASK_32 = 0xFFFFFFFF
MAXIMUM_CORE_CLOCK_HZ = 48_000_000
PROPERTY_SEED_COUNT = 10
PROPERTY_EXAMPLES_PER_CASE = 10_000
MINIMUM_EXECUTION_PINS = 8
METHODOLOGY_ADRS = [
    "ADR-0011",
    "ADR-0012",
    "ADR-0013",
    "ADR-0014",
    "ADR-0016",
    "ADR-0017",
    "ADR-0018",
    "ADR-0019",
    "ADR-0020",
]
OPERATIONS = ["encode", "decode", "skip_unknown_optional", "reject_invalid"]
CLAIM_LABELS = ["safe_wcet_upper_bound", "bounded_domain_maximum", "maximum_observed"]
GRID_DIMENSIONS = {
    "capability_levels": [1, 2, 3, 4, 5, 6],
    "application_value_bytes": [0, 1, 4, 8, 16, 32, 64, 127, 128, 255, 256, 1024, 4096],
    "record_counts": [1, 2, 4, 6, 16, 64, 127, 128, 255],
    "directional_content_budget_bytes": [64, 128, 256, 512, 4096, 8192],
    "session_lengths": [1, 10, 100, 1000, 1_000_000],
}
SOURCE_METRICS = [
    "cyclomatic_complexity_sum",
    "cyclomatic_complexity_median",
    "cyclomatic_complexity_p90",
    "cyclomatic_complexity_maximum",
    "functions_above_complexity_10",
    "function_count",
    "logical_noncomment_sloc",
    "token_count",
    "parser_states",
    "parser_transitions",
    "maximum_nesting_depth",
    "validation_error_exits",
]
EMBEDDED_METRICS = [
    "text_bytes",
    "rodata_bytes",
    "data_bytes",
    "bss_bytes",
    "maximum_bounded_stack_bytes",
    "scratch_bytes",
]
PRIMARY_C_FLAGS = ["-std=c11", "-mcpu=cortex-m0", "-mthumb", "-O2", "-fno-lto"]
REPLICATION_C_FLAGS = ["-std=c11", "-mcpu=cortex-m0", "-mthumb", "-Os", "-fno-lto"]
FUZZ_TARGETS = ["decode_block", "negotiation_state_sequence"]
SANITIZER_PROFILES = ["address", "undefined"]
ZERO_LOSS_CRITERIA = [
    "zero_loss",
    "zero_duplication",
    "zero_parse_errors",
    "zero_required_ordering_errors",
    "end_backlog_not_greater_than_start_after_frozen_drain_window",
]
AXIS_IDS = {
    "axis_1_wire_overhead",
    "axis_2_parse_complexity",
    "axis_3_extensibility",
    "axis_4_legacy_safety",
    "axis_5_bounded_worst_case_latency",
    "axis_6_throughput",
}

Manifest = dict[str, Any]


def load_manifest(path: Path = DEFAULT_MANIFEST) -> Manifest:
    """Load a JSON manifest and require an object at its root."""
    document: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        msg = "manifest root must be a JSON object"
        raise ValueError(msg)
    return document


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a file's exact bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(condition: bool, message: str, errors: list[str]) -> None:
    """Record a validation error when a condition is false."""
    if not condition:
        errors.append(message)


def _object(value: Any) -> Manifest:
    """Return a mapping value or an empty mapping for invalid input."""
    return value if isinstance(value, dict) else {}


def _ids(items: Any) -> list[str]:
    """Extract string IDs from an array of objects."""
    if not isinstance(items, list):
        return []
    return [item.get("id", "") for item in items if isinstance(item, dict)]


def _validate_top_level(manifest: Manifest, errors: list[str]) -> None:
    """Validate immutable manifest identity and preregistration state."""
    expected = {
        "$schema": "./manifest-v2.schema.json",
        "schema_version": "2.0.0",
        "manifest_id": "i3cex-bakeoff-v2",
        "status": "frozen_preimplementation_design",
        "specification": "I3CEX-0.2.0-draft",
        "baseline_commit": EXPECTED_BASELINE_COMMIT,
        "labeled_measurements_enabled": False,
        "next_required_manifest": "manifest-v3-execution",
    }
    for field, value in expected.items():
        _record(manifest.get(field) == value, f"{field} must be {value!r}", errors)

    baseline = manifest.get("baseline_commit")
    _record(
        isinstance(baseline, str) and re.fullmatch(r"[0-9a-f]{40}", baseline) is not None,
        "baseline_commit must be a full lowercase Git SHA",
        errors,
    )
    seed = manifest.get("master_seed")
    _record(isinstance(seed, int) and 0 < seed <= MASK_32, "master_seed must be uint32", errors)


def _validate_standards(manifest: Manifest, errors: list[str]) -> None:
    """Validate the public standards and identifier boundary."""
    standards = _object(manifest.get("standards_baseline"))
    required = {
        "name": "MIPI I3C Basic",
        "version": "1.2",
        "adopted": "2025-04-17",
        "official_url": "https://www.mipi.org/specifications/i3c-sensor-specification",
        "identifier_policy": "symbolic_or_deliberately_configured_private_only_until_assignment",
        "conformance_claim_policy": "base_i3c_and_i3cex_reported_separately",
    }
    for field, value in required.items():
        _record(standards.get(field) == value, f"standards_baseline.{field} is incorrect", errors)
    boundary = standards.get("transport_boundary")
    _record(
        isinstance(boundary, str) and "Private SDR" in boundary and "SETBUSCON" in boundary,
        "standards transport boundary must retain Private SDR and SETBUSCON gating",
        errors,
    )


def _validate_lineage(manifest: Manifest, errors: list[str]) -> None:
    """Validate the exact immutable extensibility-v1 dependency."""
    lineage = _object(manifest.get("extends_manifest"))
    path = lineage.get("path")
    _record(path == "experiments/extensibility/manifest-v1.json", "v1 path is incorrect", errors)
    _record(lineage.get("sha256") == EXPECTED_V1_SHA256, "v1 recorded SHA-256 is incorrect", errors)
    _record(
        lineage.get("expected_core_cells") == EXPECTED_EXTENSIBILITY_CELLS,
        "v1 core cell count is incorrect",
        errors,
    )
    _record(lineage.get("mutation_policy") == "immutable", "v1 must remain immutable", errors)
    if isinstance(path, str):
        v1_path = REPOSITORY_ROOT / path
        _record(v1_path.is_file(), "referenced v1 manifest does not exist", errors)
        if v1_path.is_file():
            _record(
                sha256_file(v1_path) == EXPECTED_V1_SHA256, "referenced v1 bytes changed", errors
            )


def _validate_methodology(manifest: Manifest, errors: list[str]) -> None:
    """Validate the complete accepted methodology family and source files."""
    adrs = manifest.get("methodology_adrs")
    _record(_ids(adrs) == METHODOLOGY_ADRS, "methodology ADR set or order is incorrect", errors)
    if not isinstance(adrs, list):
        return
    for item in adrs:
        if not isinstance(item, dict):
            errors.append("methodology ADR entry must be an object")
            continue
        adr_id = item.get("id", "unknown")
        _record(item.get("status") == "accepted", f"{adr_id} must be accepted", errors)
        path = item.get("path")
        adr_path = REPOSITORY_ROOT / path if isinstance(path, str) else None
        _record(
            adr_path is not None and adr_path.is_file(), f"{adr_id} path does not exist", errors
        )
        if adr_path is not None and adr_path.is_file():
            text = adr_path.read_text(encoding="utf-8")
            _record("- **Status**: Accepted" in text, f"{adr_id} file is not accepted", errors)


def _validate_dimensions(manifest: Manifest, errors: list[str]) -> None:
    """Validate candidate, direction, operation, and shared workload dimensions."""
    candidates = manifest.get("candidates")
    directions = _ids(manifest.get("directions"))
    operations = manifest.get("operations")
    _record(candidates == ["preamble", "tlv"], "candidate set must be preamble and tlv", errors)
    _record(
        directions == ["controller_to_target", "target_to_controller"],
        "direction set is incorrect",
        errors,
    )
    _record(operations == OPERATIONS, "operation set or order is incorrect", errors)

    grid = _object(manifest.get("shared_workload_grid"))
    for field, expected in GRID_DIMENSIONS.items():
        _record(grid.get(field) == expected, f"shared workload {field} changed", errors)
    if not isinstance(candidates, list) or not isinstance(directions, list):
        return
    calculated = len(candidates) * len(directions)
    for value in GRID_DIMENSIONS.values():
        calculated *= len(value)
    _record(calculated == EXPECTED_GRID_CELLS, "shared workload grid calculation changed", errors)
    _record(
        grid.get("expected_candidate_direction_cells") == calculated,
        "expected_candidate_direction_cells mismatch",
        errors,
    )


def _validate_runtime(manifest: Manifest, errors: list[str]) -> None:
    """Validate primary runtime platform, language split, and repetitions."""
    runtime = _object(manifest.get("cross_language_runtime"))
    c_runtime = _object(runtime.get("c"))
    python_runtime = _object(runtime.get("python"))
    repetitions = _object(runtime.get("repetitions"))
    _record(c_runtime.get("standard") == "freestanding ISO C11", "C standard changed", errors)
    _record(
        c_runtime.get("dynamic_allocation_in_timed_path") is False,
        "timed C allocation forbidden",
        errors,
    )
    _record(
        "Cortex-M0" in str(c_runtime.get("primary_target")), "Cortex-M0 must be primary", errors
    )
    _record(
        c_runtime.get("maximum_core_clock_hz") == MAXIMUM_CORE_CLOCK_HZ,
        "primary clock cap changed",
        errors,
    )
    _record(
        python_runtime.get("primary_version_line") == "3.12", "CPython 3.12 must be primary", errors
    )
    _record(
        python_runtime.get("replication_version_lines") == ["3.11", "3.13"],
        "Python replication lines changed",
        errors,
    )
    _record(c_runtime.get("primary_flags") == PRIMARY_C_FLAGS, "primary C flags changed", errors)
    _record(
        c_runtime.get("replication_flags") == REPLICATION_C_FLAGS,
        "replication C flags changed",
        errors,
    )
    required_repetitions = {
        "independent_blocks": 30,
        "warmup_batches_per_block": 100,
        "timed_batches_per_block": 1000,
        "fresh_process_or_hardware_reset_per_block": True,
        "outlier_removal": False,
        "optional_stopping": False,
    }
    for field, value in required_repetitions.items():
        _record(repetitions.get(field) == value, f"runtime repetitions.{field} changed", errors)


def _validate_wire_and_complexity(axes: Manifest, errors: list[str]) -> None:
    """Validate exact wire accounting and non-composite complexity rules."""
    wire = _object(axes.get("axis_1_wire_overhead"))
    complexity = _object(axes.get("axis_2_parse_complexity"))
    _record(wire.get("adr") == "ADR-0016", "axis 1 ADR is incorrect", errors)
    _record(wire.get("grid_reference") == "shared_workload_grid", "axis 1 grid changed", errors)
    _record(
        wire.get("method") == "exact_analytical_accounting_cross_checked_against_emitted_bytes",
        "axis 1 must use exact accounting",
        errors,
    )
    _record(
        wire.get("uncertainty_interval") == "not_applicable_exact_integer_accounting",
        "axis 1 must not invent uncertainty intervals",
        errors,
    )
    _record(complexity.get("adr") == "ADR-0017", "axis 2 ADR is incorrect", errors)
    _record(complexity.get("primary_language") == "c", "C must be primary for axis 2", errors)
    _record(
        complexity.get("composite_score_allowed") is False, "complexity composite forbidden", errors
    )
    _record(
        complexity.get("source_metrics") == SOURCE_METRICS, "axis 2 source metrics changed", errors
    )
    _record(
        complexity.get("embedded_metrics") == EMBEDDED_METRICS,
        "axis 2 embedded metrics changed",
        errors,
    )


def _validate_extensibility_and_safety(axes: Manifest, errors: list[str]) -> None:
    """Validate the inherited extensibility matrix and fixed safety campaigns."""
    extensibility = _object(axes.get("axis_3_extensibility"))
    safety = _object(axes.get("axis_4_legacy_safety"))
    _record(
        extensibility.get("expected_core_cells") == EXPECTED_EXTENSIBILITY_CELLS,
        "axis 3 core cells changed",
        errors,
    )
    for field in (
        "core_cell_coverage_percent",
        "boundary_coverage_percent",
        "valid_two_way_nuisance_coverage_percent",
    ):
        _record(
            extensibility.get(field) == FULL_COVERAGE_PERCENT, f"axis 3 {field} changed", errors
        )

    property_campaign = _object(safety.get("python_property_campaign"))
    fuzz = _object(safety.get("c_fuzz_campaign"))
    _record(safety.get("unsafe_tolerance") == 0, "axis 4 unsafe tolerance must be zero", errors)
    _record(
        property_campaign.get("database") is None,
        "labeled Hypothesis database must be disabled",
        errors,
    )
    _record(
        property_campaign.get("deadline") is None,
        "labeled Hypothesis deadline must be disabled",
        errors,
    )
    _record(
        property_campaign.get("seed_count") == PROPERTY_SEED_COUNT,
        "Hypothesis seed count changed",
        errors,
    )
    _record(
        property_campaign.get("max_examples_per_seed_candidate_target")
        == PROPERTY_EXAMPLES_PER_CASE,
        "Hypothesis example count changed",
        errors,
    )
    targets = fuzz.get("targets")
    profiles = fuzz.get("sanitizer_profiles")
    _record(targets == FUZZ_TARGETS, "fuzz target set changed", errors)
    _record(profiles == SANITIZER_PROFILES, "sanitizer profile set changed", errors)
    seeds = fuzz.get("seed_count")
    runs = fuzz.get("runs_per_seed_candidate_target_profile")
    calculated = (
        len(targets) * len(profiles) * seeds * runs
        if isinstance(targets, list)
        and isinstance(profiles, list)
        and isinstance(seeds, int)
        and isinstance(runs, int)
        else 0
    )
    _record(
        calculated == EXPECTED_FUZZ_EXECUTIONS_PER_CANDIDATE, "fuzz campaign size changed", errors
    )
    _record(
        fuzz.get("expected_executions_per_candidate") == calculated,
        "fuzz execution total mismatch",
        errors,
    )
    _record(fuzz.get("time_based_stopping") is False, "time-based fuzz stopping forbidden", errors)
    _record(
        fuzz.get("project_code_suppressions_allowed") is False,
        "sanitizer suppressions forbidden",
        errors,
    )


def _validate_latency_and_throughput(axes: Manifest, errors: list[str]) -> None:
    """Validate latency claim labels and loss-free goodput search effort."""
    latency = _object(axes.get("axis_5_bounded_worst_case_latency"))
    throughput = _object(axes.get("axis_6_throughput"))
    _record(latency.get("claim_labels") == CLAIM_LABELS, "latency claim labels changed", errors)
    _record(
        latency.get("sampled_maximum_may_be_called_wcet") is False,
        "sample maximum is not WCET",
        errors,
    )
    _record(
        latency.get("static_analysis_required_for_safe_bound_claim") is True,
        "safe bound requires static analysis",
        errors,
    )
    _record(
        throughput.get("primary_metric")
        == "successfully_delivered_application_bytes_per_elapsed_second",
        "throughput must measure application goodput",
        errors,
    )
    search = _object(throughput.get("empirical_search"))
    expected = {
        "warmup_logical_messages": 10_000,
        "measured_logical_messages_per_trial": 1_000_000,
        "independent_final_pair_blocks": 30,
        "time_based_stopping": False,
        "outlier_removal": False,
    }
    for field, value in expected.items():
        _record(search.get(field) == value, f"throughput search.{field} changed", errors)
    _record(
        search.get("passing_criteria") == ZERO_LOSS_CRITERIA, "zero-loss criteria changed", errors
    )


def _validate_analysis_and_activation(manifest: Manifest, errors: list[str]) -> None:
    """Validate the global decision rule and pre-label execution gate."""
    analysis = _object(manifest.get("analysis_contract"))
    expected_analysis = {
        "confidence_level_percent": 99,
        "interval_method": "hierarchical_bootstrap_over_independent_blocks",
        "safety_gate_noncompensable": True,
        "decision_rule": "pareto_dominance_with_crossovers_and_no_unique_winner_reported",
        "weighted_scores_allowed": False,
        "python_to_c_speed_ratio_selects_candidate": False,
        "negative_results_reported": True,
    }
    for field, value in expected_analysis.items():
        _record(analysis.get(field) == value, f"analysis_contract.{field} changed", errors)

    execution = _object(manifest.get("execution_manifest_requirements"))
    _record(
        execution.get("required_before_labeled_measurements") is True,
        "execution manifest gate required",
        errors,
    )
    pins = execution.get("must_pin")
    _record(
        isinstance(pins, list) and len(pins) >= MINIMUM_EXECUTION_PINS,
        "execution manifest pin list is incomplete",
        errors,
    )
    _record(
        execution.get("candidate_labels_blinded_during_pilot") is True,
        "pilot must remain blinded",
        errors,
    )
    _record(
        execution.get("may_modify_manifest_v2") is False,
        "manifest v2 must remain immutable",
        errors,
    )


def validate_manifest(manifest: Manifest) -> list[str]:
    """Return all semantic validation errors for a loaded manifest."""
    errors: list[str] = []
    _validate_top_level(manifest, errors)
    _validate_standards(manifest, errors)
    _validate_lineage(manifest, errors)
    _validate_methodology(manifest, errors)
    _validate_dimensions(manifest, errors)
    _validate_runtime(manifest, errors)
    axes = _object(manifest.get("axes"))
    _record(set(axes) == AXIS_IDS, "exactly the six registered bakeoff axes are required", errors)
    _validate_wire_and_complexity(axes, errors)
    _validate_extensibility_and_safety(axes, errors)
    _validate_latency_and_throughput(axes, errors)
    _validate_analysis_and_activation(manifest, errors)
    return errors


def validate_hash(manifest_path: Path = DEFAULT_MANIFEST, hash_path: Path = DEFAULT_HASH) -> bool:
    """Return whether the sidecar contains the manifest's exact SHA-256."""
    if not hash_path.is_file():
        return False
    fields = hash_path.read_text(encoding="ascii").strip().split()
    return (
        len(fields) == HASH_SIDECAR_FIELD_COUNT
        and fields[0] == sha256_file(manifest_path)
        and fields[1] == manifest_path.name
    )


def main(argv: list[str] | None = None) -> int:
    """Validate a manifest and its sidecar hash from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--hash-file", type=Path, default=DEFAULT_HASH)
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    errors = validate_manifest(manifest)
    if not validate_hash(args.manifest, args.hash_file):
        errors.append("manifest SHA-256 sidecar is missing or does not match")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    grid = _object(manifest.get("shared_workload_grid"))
    print(f"valid: {args.manifest} ({grid.get('expected_candidate_direction_cells')} grid cells)")
    print(f"sha256: {sha256_file(args.manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
