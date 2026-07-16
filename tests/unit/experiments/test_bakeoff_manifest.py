from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from scripts.validate_bakeoff_manifest import (
    DEFAULT_HASH,
    DEFAULT_MANIFEST,
    EXPECTED_GRID_CELLS,
    EXPECTED_V1_SHA256,
    load_manifest,
    sha256_file,
    validate_hash,
    validate_manifest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = DEFAULT_MANIFEST.with_name("manifest-v2.schema.json")


@pytest.fixture
def manifest() -> dict[str, Any]:
    return load_manifest()


@pytest.mark.unit
def test_frozen_bakeoff_manifest_is_valid(manifest: dict[str, Any]) -> None:
    assert validate_manifest(manifest) == []


@pytest.mark.unit
def test_bakeoff_manifest_sha256_sidecar_matches() -> None:
    assert validate_hash(DEFAULT_MANIFEST, DEFAULT_HASH)


@pytest.mark.unit
def test_bakeoff_manifest_uses_canonical_lf_line_endings() -> None:
    manifest_bytes = DEFAULT_MANIFEST.read_bytes()

    assert b"\r\n" not in manifest_bytes
    assert manifest_bytes.endswith(b"\n")


@pytest.mark.unit
def test_bakeoff_schema_is_valid_json_and_matches_manifest() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    manifest = load_manifest()

    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(manifest)) == []
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["manifest_id"]["const"] == manifest["manifest_id"]
    assert schema["properties"]["schema_version"]["const"] == manifest["schema_version"]


@pytest.mark.unit
def test_shared_workload_grid_contains_84240_candidate_direction_cells(
    manifest: dict[str, Any],
) -> None:
    grid = manifest["shared_workload_grid"]
    calculated = len(manifest["candidates"]) * len(manifest["directions"])
    for field in (
        "capability_levels",
        "application_value_bytes",
        "record_counts",
        "directional_content_budget_bytes",
        "session_lengths",
    ):
        calculated *= len(grid[field])

    assert calculated == grid["expected_candidate_direction_cells"] == EXPECTED_GRID_CELLS


@pytest.mark.unit
def test_manifest_v2_pins_the_unchanged_extensibility_v1_bytes(
    manifest: dict[str, Any],
) -> None:
    lineage = manifest["extends_manifest"]
    v1_path = REPOSITORY_ROOT / lineage["path"]

    assert lineage["mutation_policy"] == "immutable"
    assert lineage["sha256"] == sha256_file(v1_path) == EXPECTED_V1_SHA256


@pytest.mark.unit
def test_validator_rejects_standards_baseline_drift(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["standards_baseline"]["version"] = "1.3"

    assert "standards_baseline.version is incorrect" in validate_manifest(mutated)


@pytest.mark.unit
def test_validator_rejects_unaccepted_methodology(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["methodology_adrs"][-1]["status"] = "proposed"

    assert "ADR-0020 must be accepted" in validate_manifest(mutated)


@pytest.mark.unit
def test_validator_rejects_grid_cell_count_drift(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["shared_workload_grid"]["session_lengths"].pop()

    assert "shared workload session_lengths changed" in validate_manifest(mutated)


@pytest.mark.unit
def test_validator_rejects_reduced_fuzz_campaign(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["axes"]["axis_4_legacy_safety"]["c_fuzz_campaign"][
        "runs_per_seed_candidate_target_profile"
    ] = 999999

    assert "fuzz campaign size changed" in validate_manifest(mutated)


@pytest.mark.unit
def test_validator_rejects_calling_a_sampled_maximum_wcet(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["axes"]["axis_5_bounded_worst_case_latency"]["sampled_maximum_may_be_called_wcet"] = (
        True
    )

    assert "sample maximum is not WCET" in validate_manifest(mutated)


@pytest.mark.unit
def test_validator_rejects_labeled_measurements_before_execution_freeze(
    manifest: dict[str, Any],
) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["labeled_measurements_enabled"] = True
    mutated["execution_manifest_requirements"]["required_before_labeled_measurements"] = False

    errors = validate_manifest(mutated)

    assert "labeled_measurements_enabled must be False" in errors
    assert "execution manifest gate required" in errors
