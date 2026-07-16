# ADR-0013: Extensibility coverage strategy

- **Status**: Accepted
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: NIST combinatorial-testing guidance
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

ADR-0012 freezes what kinds of extension must be evaluated. It does not define
how version pairings, transfer directions, payload boundaries, element order,
and composition factors are covered. Exhausting every byte string is
impossible, while an ad-hoc sample would leave unknown and potentially biased
gaps.

The coverage strategy must exhaust the small factors central to the research
question and use measured combinatorial coverage only for secondary nuisance
factors.

## Decision Drivers

- Complete coverage of both candidates, all scenarios, and old/new skew.
- Explicit controller-to-target and target-to-controller payload budgets.
- Mandatory boundary-value coverage for every encoded limit.
- A reproducible way to reduce the nuisance-factor cross-product.
- No deletion or replacement of unsupported or failed cells.
- A machine-verifiable coverage report committed before results analysis.

## Considered Options

- Option A: A few hand-authored representative examples per scenario.
- Option B: Full Cartesian product of every factor and payload value.
- Option C: Exhaust the core matrix and boundaries; require pairwise coverage
  over declared nuisance factors.

## Decision Outcome

Chosen option: **Option C — exhaustive core and boundary coverage plus measured
pairwise nuisance-factor coverage**, because it fully covers the factors that
define the framing comparison while bounding the remaining test count.

### Consequences

**Good:**

- Every central comparison cell has a result or an explicit failure status.
- Pairwise coverage is quantified rather than asserted informally.
- Boundary bugs cannot be hidden by a covering-array reduction.

**Bad:**

- Pairwise nuisance coverage cannot guarantee detection of every higher-order
  interaction.
- The minimum logical matrix contains 192 cells before fixture expansion.

## Frozen experiment baseline

No scenario implementation begins until all of the following are committed on
`main` or the designated experiment base branch:

1. accepted ADR-0011 through ADR-0014;
2. a machine-readable manifest containing the full factor model;
3. semantic fixtures and expected outcome classes for all twelve scenarios;
4. the exact common baseline commit; and
5. the master random seed and generated implementation order.

The manifest SHA-256 is printed in every raw result. Any semantic or factor
change after the first labeled run requires a new manifest version and a full
rerun; old and new results MUST NOT be pooled.

## Exhaustive core matrix

Every ADR-0012 scenario is executed for the complete Cartesian product of:

- **scenario**: X01 through X12;
- **candidate**: preamble and TLV;
- **version pairing**:
  - B→B: baseline sender to baseline receiver;
  - B→E: baseline sender to extended receiver;
  - E→B: extended sender to baseline receiver;
  - E→E: extended sender to extended receiver; and
- **Private SDR content direction**:
  - controller-to-target, constrained by the SETMWL-derived content budget;
  - target-to-controller, constrained by the SETMRL-derived content budget.

This produces `12 × 2 × 4 × 2 = 192` mandatory logical cells. A cell is never
omitted because a candidate cannot express it. It receives `UNSUPPORTED`,
`INFEASIBLE_BASE_BUDGET`, `IMPLEMENTATION_FAILED`, or another ADR-0014 outcome
and remains in the denominator.

The B→B cell is a no-extension control. B→E demonstrates backward
compatibility, E→B demonstrates forward-compatibility behavior, and E→E
demonstrates the new function. A candidate passes a scenario only if all four
pairings match the pre-registered oracle.

## Exhaustive boundary sets

Every numeric field or negotiated limit touched by a scenario uses:

- minimum valid value;
- one ordinary interior value;
- `boundary - 1`;
- `boundary`;
- `boundary + 1`; and
- maximum representable or negotiated valid value, when distinct.

For the current framing candidates this includes at least capability level 6/7,
TLV Length 127/128, Type 0xFD/0xFE/0xFF, block length 4096/4097, the effective
directional content budget, and any newly introduced extended-length or
namespace boundary.

Malformed values are not inferred from boundary tests. Their broader mutation
campaign belongs to the legacy-safety axis, although clean rejection required
by a canonical extensibility scenario remains in this matrix.

## Nuisance-factor model

Within each scenario, applicable nuisance factors are declared before fixture
generation. The initial allowed factor vocabulary is:

| Factor | Levels |
|---|---|
| Extension position | first, middle, last |
| Known element count | 0, 1, 3 |
| Unknown optional element count | 0, 1, 3 |
| Value-content pattern | all-zero, all-one, alternating, deterministic random |
| Directional budget slack | exact fit, one byte spare, at least 25% spare |
| Repetition of same extension | once, twice, maximum permitted |
| Neighbor relation | known/known, known/unknown, unknown/known |

Levels that are semantically impossible for a scenario are represented as
constraints, not silently removed after generation. New nuisance factors
require a manifest revision before labeled runs.

The selected fixtures MUST achieve 100% valid two-way interaction coverage
among applicable nuisance-factor levels. Coverage is computed against the
constrained valid tuple space, not the unconstrained Cartesian product.

Pairwise reduction MUST NOT reduce:

- the 192-cell core matrix;
- any exhaustive boundary set;
- E→B behavior for optional and critical extensions;
- the known-plus-unknown composition in X06; or
- the two-independent-extension interaction in X10.

## Scenario isolation and order control

Each `(candidate, scenario)` extension is implemented from the same baseline
commit in an isolated worktree or branch. It MUST NOT inherit code introduced
for another scenario, except shared harness changes that were already present
in the frozen baseline.

Implementation order is generated from the master seed with these constraints:

- six scenarios begin with preamble and six with TLV;
- no candidate begins more than two consecutive scenarios; and
- scenario IDs are not implemented in numeric order.

The generated order is committed before implementation. This counterbalancing
does not eliminate learning effects, so developer time is excluded as a
primary metric, but it prevents one candidate from always benefiting from
second implementation.

## Coverage verification

A separate coverage verifier consumes only the manifest and completed result
records. It MUST emit:

- present, missing, duplicate, unsupported, and failed core cells;
- boundary coverage per numeric field;
- achieved valid two-way interaction coverage per scenario;
- every constraint used by the covering array;
- fixture counts before and after reduction; and
- the manifest and verifier commit hashes.

Publication tables MUST use the verifier's counts. A run is complete only when:

- all 192 logical cells are present exactly once at the summary level;
- every mandatory boundary point is present;
- nuisance-factor two-way coverage is 100%; and
- every raw record is traceable to one logical cell and fixture.

Failures and unsupported cells satisfy presence, not success. Missing cells
MUST NOT be treated as neutral or excluded from candidate totals.

## Property and differential testing

For every E→E fixture that should succeed:

- encode/decode roundtrip properties run in Python and C;
- both languages emit bit-identical bytes;
- decoding is deterministic under repeated execution; and
- reordering is tested where the scenario declares order independence.

For every B→E and E→B fixture, the observed outcome must match the explicit
compatibility oracle. “Did not crash” is not a sufficient compatibility result.

## Pros and Cons of the Options

### Option A: Representative examples

- Good: Smallest artifact and fastest implementation.
- Bad: Coverage is subjective and easy to bias after seeing candidate behavior.

### Option B: Full Cartesian product

- Good: Strongest finite-factor coverage.
- Bad: Nuisance-factor growth creates redundant tests and impractical artifact
  execution time without making byte-space exhaustion possible.

### Option C: Exhaustive core plus pairwise nuisance coverage

- Good: Complete on research-critical factors and quantitatively bounded on
  secondary factors.
- Bad: Higher-order nuisance interactions remain a stated limitation.

## References

- [ADR-0012](./0012-extensibility-scenario-taxonomy.md) — scenario taxonomy.
- [Measuring and Specifying Combinatorial Coverage of Test Input Configurations](https://www.nist.gov/publications/measuring-and-specifying-combinatorial-coverage-test-input-configurations)
  — NIST guidance on t-way interaction coverage and covering arrays.
- [NIST IR 8466, Combinatorial Testing for Software](https://nvlpubs.nist.gov/nistpubs/ir/2023/NIST.IR.8466.pdf)
  — practical combinatorial-testing methods and coverage measurement.
