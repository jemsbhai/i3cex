"""Validate the frozen I3C-EX extensibility experiment manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "experiments" / "extensibility" / "manifest-v1.json"
DEFAULT_HASH = REPOSITORY_ROOT / "experiments" / "extensibility" / "manifest-v1.sha256"
MASK_32 = 0xFFFFFFFF
AXIS_BLOCKER_COUNT = 5
CORE_CELL_COUNT = 192
FULL_COVERAGE_PERCENT = 100
NUISANCE_FACTOR_COUNT = 7
MINIMUM_BOUNDARY_POINTS = 4
SCENARIO_COUNT = 12
FIRST_CANDIDATE_COUNT = SCENARIO_COUNT // 2
HASH_SIDECAR_FIELD_COUNT = 2

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


def _xorshift32(state: int) -> int:
    """Advance the manifest's specified 32-bit pseudorandom generator."""
    state = (state ^ ((state << 13) & MASK_32)) & MASK_32
    state = (state ^ (state >> 17)) & MASK_32
    return (state ^ ((state << 5) & MASK_32)) & MASK_32


def derive_implementation_order(seed: int, scenario_ids: list[str]) -> list[tuple[str, str]]:
    """Derive the constrained scenario/candidate order from the master seed."""
    ordered = list(scenario_ids)
    state = seed & MASK_32
    for index in range(len(ordered) - 1, 0, -1):
        state = _xorshift32(state)
        swap_index = state % (index + 1)
        ordered[index], ordered[swap_index] = ordered[swap_index], ordered[index]

    state = _xorshift32(state)
    first = "preamble" if state & 1 == 0 else "tlv"
    second = "tlv" if first == "preamble" else "preamble"
    return [
        (scenario_id, first if position % 2 == 0 else second)
        for position, scenario_id in enumerate(ordered)
    ]


def _record(condition: bool, message: str, errors: list[str]) -> None:
    """Record a validation error when a condition is false."""
    if not condition:
        errors.append(message)


def _ids(items: Any) -> list[str]:
    """Extract string IDs from a list of objects, returning an empty list on bad shape."""
    if not isinstance(items, list):
        return []
    return [item.get("id", "") for item in items if isinstance(item, dict)]


def _validate_top_level(manifest: Manifest, errors: list[str]) -> None:
    """Validate immutable top-level identity and safety gates."""
    _record(manifest.get("schema_version") == "1.0.0", "schema_version must be 1.0.0", errors)
    _record(
        manifest.get("manifest_id") == "i3cex-extensibility-v1",
        "unexpected manifest_id",
        errors,
    )
    _record(
        manifest.get("status") == "frozen_preimplementation",
        "manifest status must be frozen_preimplementation",
        errors,
    )
    baseline = manifest.get("baseline_commit")
    _record(
        isinstance(baseline, str) and re.fullmatch(r"[0-9a-f]{40}", baseline) is not None,
        "baseline_commit must be a full lowercase Git SHA",
        errors,
    )
    _record(
        manifest.get("labeled_measurements_enabled") is False,
        "labeled measurements must remain disabled until all axis methods are accepted",
        errors,
    )
    blockers = manifest.get("blocking_requirements")
    _record(
        isinstance(blockers, list) and len(blockers) == AXIS_BLOCKER_COUNT,
        "five axis blockers required",
        errors,
    )


def _validate_methodology(manifest: Manifest, errors: list[str]) -> None:
    """Validate that the four governing ADRs are pinned as accepted."""
    adrs = manifest.get("methodology_adrs")
    expected = ["ADR-0011", "ADR-0012", "ADR-0013", "ADR-0014"]
    _record(_ids(adrs) == expected, "methodology ADR set or order is incorrect", errors)
    if not isinstance(adrs, list):
        return
    statuses = [item.get("status") for item in adrs if isinstance(item, dict)]
    _record(statuses == ["accepted"] * 4, "all methodology ADRs must be accepted", errors)
    for item in adrs:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        exists = isinstance(path, str) and (REPOSITORY_ROOT / path).is_file()
        _record(exists, f"methodology ADR path does not exist: {path}", errors)


def _validate_dimensions(manifest: Manifest, errors: list[str]) -> None:
    """Validate the dimensions that produce the exhaustive core matrix."""
    candidates = manifest.get("candidates")
    pairings = _ids(manifest.get("version_pairings"))
    directions = _ids(manifest.get("directions"))
    _record(candidates == ["preamble", "tlv"], "candidate set must be preamble and tlv", errors)
    _record(
        pairings == ["B_TO_B", "B_TO_E", "E_TO_B", "E_TO_E"],
        "version pairing set is incorrect",
        errors,
    )
    _record(
        directions == ["controller_to_target", "target_to_controller"],
        "direction set is incorrect",
        errors,
    )
    scenarios = manifest.get("scenarios")
    count = len(scenarios) if isinstance(scenarios, list) else 0
    calculated = (
        len(candidates) * len(pairings) * len(directions) * count
        if isinstance(candidates, list)
        else 0
    )
    _record(
        calculated == CORE_CELL_COUNT,
        f"calculated core matrix is {calculated}, expected {CORE_CELL_COUNT}",
        errors,
    )
    _record(
        manifest.get("expected_core_cells") == calculated,
        "expected_core_cells mismatch",
        errors,
    )


def _validate_coverage(manifest: Manifest, errors: list[str]) -> None:
    """Validate the registered completeness thresholds and nuisance model."""
    coverage = manifest.get("coverage_requirements")
    _record(isinstance(coverage, dict), "coverage_requirements must be an object", errors)
    if isinstance(coverage, dict):
        for field in (
            "core_cell_coverage_percent",
            "boundary_coverage_percent",
            "valid_two_way_nuisance_coverage_percent",
        ):
            _record(
                coverage.get(field) == FULL_COVERAGE_PERCENT,
                f"{field} must be {FULL_COVERAGE_PERCENT}",
                errors,
            )
        _record(
            coverage.get("summary_records_per_core_cell") == 1,
            "exactly one summary record is required per core cell",
            errors,
        )
    factor_ids = _ids(manifest.get("nuisance_factors"))
    _record(
        len(factor_ids) == NUISANCE_FACTOR_COUNT and len(set(factor_ids)) == NUISANCE_FACTOR_COUNT,
        "seven unique nuisance factors required",
        errors,
    )


def _validate_scenarios(manifest: Manifest, errors: list[str]) -> list[str]:
    """Validate scenario identities, semantic outcomes, boundaries, and budgets."""
    scenarios = manifest.get("scenarios")
    expected_ids = [f"X{number:02d}" for number in range(1, 13)]
    scenario_ids = _ids(scenarios)
    _record(scenario_ids == expected_ids, "scenario IDs must be X01 through X12 in order", errors)
    if not isinstance(scenarios, list):
        return scenario_ids

    allowed_by_level = {
        "optional": {"BASELINE_ONLY", "SAFE_IGNORE", "NEGOTIATED_FALLBACK"},
        "critical": {"SAFE_REJECT", "NEGOTIATED_FALLBACK"},
        "negotiated": {"NEGOTIATED_FALLBACK"},
    }
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            errors.append("scenario entry must be an object")
            continue
        scenario_id = scenario.get("id", "unknown")
        level = scenario.get("requirement_level")
        expected = scenario.get("e_to_b_expected")
        _record(
            isinstance(level, str)
            and level in allowed_by_level
            and expected in allowed_by_level[level],
            f"{scenario_id}: E_TO_B outcome is invalid for requirement level",
            errors,
        )
        boundaries = scenario.get("boundary_values")
        boundary_ok = (
            isinstance(boundaries, list)
            and len(boundaries) >= MINIMUM_BOUNDARY_POINTS
            and len(boundaries) == len(set(boundaries))
            and boundaries == sorted(boundaries)
        )
        _record(boundary_ok, f"{scenario_id}: boundary values must be sorted and unique", errors)
        budgets = scenario.get("directional_content_budget_bytes")
        budget_ok = (
            isinstance(budgets, dict)
            and isinstance(budgets.get("controller_to_target"), int)
            and budgets.get("controller_to_target", 0) > 0
            and isinstance(budgets.get("target_to_controller"), int)
            and budgets.get("target_to_controller", 0) > 0
        )
        _record(budget_ok, f"{scenario_id}: both directional budgets must be positive", errors)
        fixture = scenario.get("semantic_fixture")
        _record(
            isinstance(fixture, dict) and set(fixture) == {"baseline", "extension", "expected"},
            f"{scenario_id}: semantic fixture shape is invalid",
            errors,
        )
    return scenario_ids


def _validate_order(manifest: Manifest, scenario_ids: list[str], errors: list[str]) -> None:
    """Validate the deterministic, counterbalanced implementation order."""
    seed = manifest.get("master_seed")
    _record(isinstance(seed, int) and 0 < seed <= MASK_32, "master_seed must be uint32", errors)
    order = manifest.get("implementation_order")
    _record(
        isinstance(order, list) and len(order) == SCENARIO_COUNT,
        "implementation order must have 12 entries",
        errors,
    )
    if not isinstance(seed, int) or not isinstance(order, list):
        return
    observed = [
        (item.get("scenario"), item.get("first_candidate"))
        for item in order
        if isinstance(item, dict)
    ]
    expected = derive_implementation_order(seed, scenario_ids)
    _record(observed == expected, "implementation order does not match seed algorithm", errors)
    positions = [item.get("position") for item in order if isinstance(item, dict)]
    _record(
        positions == list(range(1, SCENARIO_COUNT + 1)),
        "implementation positions must be 1 through 12",
        errors,
    )
    first_candidates = [candidate for _, candidate in observed]
    _record(
        first_candidates.count("preamble") == FIRST_CANDIDATE_COUNT,
        "preamble must be first six times",
        errors,
    )
    _record(
        first_candidates.count("tlv") == FIRST_CANDIDATE_COUNT,
        "tlv must be first six times",
        errors,
    )


def validate_manifest(manifest: Manifest) -> list[str]:
    """Return all semantic validation errors for a loaded manifest."""
    errors: list[str] = []
    _validate_top_level(manifest, errors)
    _validate_methodology(manifest, errors)
    _validate_dimensions(manifest, errors)
    _validate_coverage(manifest, errors)
    scenario_ids = _validate_scenarios(manifest, errors)
    _validate_order(manifest, scenario_ids, errors)
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
    print(f"valid: {args.manifest} ({manifest['expected_core_cells']} core cells)")
    print(f"sha256: {sha256_file(args.manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
