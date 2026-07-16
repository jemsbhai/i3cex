from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

import pytest
from scripts.validate_extensibility_manifest import (
    DEFAULT_HASH,
    DEFAULT_MANIFEST,
    derive_implementation_order,
    load_manifest,
    validate_hash,
    validate_manifest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def manifest() -> dict[str, Any]:
    return load_manifest()


@pytest.mark.unit
def test_frozen_manifest_is_valid(manifest: dict[str, Any]) -> None:
    assert validate_manifest(manifest) == []


@pytest.mark.unit
def test_manifest_sha256_sidecar_matches() -> None:
    assert validate_hash(DEFAULT_MANIFEST, DEFAULT_HASH)


@pytest.mark.unit
def test_manifest_uses_canonical_lf_line_endings() -> None:
    manifest_bytes = DEFAULT_MANIFEST.read_bytes()

    assert b"\r\n" not in manifest_bytes
    assert manifest_bytes.endswith(b"\n")


@pytest.mark.unit
def test_core_matrix_contains_192_logical_cells(manifest: dict[str, Any]) -> None:
    calculated = (
        len(manifest["scenarios"])
        * len(manifest["candidates"])
        * len(manifest["version_pairings"])
        * len(manifest["directions"])
    )

    assert calculated == manifest["expected_core_cells"] == 192


@pytest.mark.unit
def test_implementation_order_is_derived_from_seed(manifest: dict[str, Any]) -> None:
    scenario_ids = [scenario["id"] for scenario in manifest["scenarios"]]
    expected = derive_implementation_order(manifest["master_seed"], scenario_ids)
    observed = [
        (entry["scenario"], entry["first_candidate"]) for entry in manifest["implementation_order"]
    ]

    assert observed == expected


@pytest.mark.unit
def test_validator_rejects_wrong_core_cell_count(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["expected_core_cells"] = 191

    assert "expected_core_cells mismatch" in validate_manifest(mutated)


@pytest.mark.unit
def test_validator_rejects_unsafe_optional_oracle(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["scenarios"][2]["e_to_b_expected"] = "UNSAFE_ACCEPT"

    errors = validate_manifest(mutated)

    assert "X03: E_TO_B outcome is invalid for requirement level" in errors


@pytest.mark.unit
def test_validator_rejects_order_not_derived_from_seed(manifest: dict[str, Any]) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["implementation_order"][0], mutated["implementation_order"][1] = (
        mutated["implementation_order"][1],
        mutated["implementation_order"][0],
    )

    assert "implementation order does not match seed algorithm" in validate_manifest(mutated)


@pytest.mark.unit
def test_coverage_configuration_enforces_strictly_above_90_percent() -> None:
    configuration = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    options = configuration["tool"]["pytest"]["ini_options"]["addopts"]
    threshold_option = next(option for option in options if option.startswith("--cov-fail-under="))
    threshold = float(threshold_option.partition("=")[2])
    precision = configuration["tool"]["coverage"]["report"]["precision"]

    assert threshold > 90.0
    assert precision >= 2
