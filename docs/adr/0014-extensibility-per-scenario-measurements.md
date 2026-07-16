# ADR-0014: Extensibility per-scenario measurements and decision rule

- **Status**: Proposed
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: RFC 6709; ADR-0011 through ADR-0013
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

ADR-0012 defines the extensibility scenarios and ADR-0013 defines which cells
must be executed. The bakeoff still needs a fixed measurement set and decision
rule. “Effort” cannot mean developer hours: there is one primary implementer,
the second candidate benefits from learning, and elapsed time is dominated by
tooling and debugging choices.

The methodology must capture whether an extension works safely, what framing
intervention it requires, how much namespace and wire space it consumes, and
how much implementation structure changes. It must not collapse unlike costs
into an arbitrary weighted score.

## Decision Drivers

- Compatibility outcomes must be semantic, not merely crash/no-crash.
- Safety failures must dominate convenience or byte savings.
- Unsupported and base-budget-infeasible cases remain explicit.
- Measurements should be mechanically reproducible from isolated diffs.
- Runtime data must follow ADR-0011 and remain distinguishable from
  extensibility evidence.
- The extensibility axis may legitimately end in a trade-off rather than a
  forced winner.

## Considered Options

- Option A: Use developer hours and subjective difficulty ratings.
- Option B: Produce one weighted extensibility score.
- Option C: Record a fixed outcome-and-cost vector and compare candidates by
  safety gates and Pareto dominance.

## Decision Outcome

Chosen option: **Option C — fixed per-cell outcome classes, fixed per-scenario
cost vectors, a non-negotiable safety gate, and Pareto comparison**, because it
preserves the evidence without hiding value judgments in arbitrary weights.

### Consequences

**Good:**

- Unsafe compatibility cannot be compensated by fewer bytes or less code.
- Reviewers can recompute every table and apply alternative preferences.
- An inconclusive or trade-off result is representable without forcing a score.

**Bad:**

- The paper must present a multidimensional result rather than one headline
  number.
- Code-churn and complexity counts remain imperfect secondary proxies for
  engineering burden.

## Cell-level outcome vocabulary

Every mandatory ADR-0013 logical cell receives exactly one terminal outcome.

| Code | Meaning | Safe? |
|---|---|---|
| `FULL` | Receiver produces the complete pre-registered semantics | Yes |
| `BASELINE_ONLY` | Receiver safely preserves only baseline-known semantics | Yes, optional extensions only |
| `SAFE_IGNORE` | Unknown optional content is skipped with framing synchronization preserved | Yes |
| `SAFE_REJECT` | Receiver rejects before exposing partial or corrupted semantics | Yes |
| `NEGOTIATED_FALLBACK` | Sender does not emit the extension and both peers use the registered baseline path | Yes |
| `UNSUPPORTED` | Candidate has no encoding that meets the scenario contract | No pass, but not unsafe |
| `INFEASIBLE_BASE_BUDGET` | Fixture cannot fit the declared SETMRL/SETMWL-derived content budget | Not attributable to framing support |
| `IMPLEMENTATION_FAILED` | The isolated extension implementation did not reach its semantic oracle | No |
| `UNSAFE_ACCEPT` | Receiver accepts unknown critical content or returns incorrect semantics | No; safety failure |
| `DESYNCHRONIZED` | Receiver loses the next element boundary or consumes the wrong length | No; safety failure |
| `UNBOUNDED_RESOURCE` | Input causes unbounded loop, allocation, recursion, or state growth | No; safety failure |
| `MEMORY_SAFETY_FAILURE` | Out-of-bounds access, overflow, sanitizer failure, or crash | No; safety failure |

Raw diagnostic details accompany the code. Outcome codes MUST NOT be inferred
from process exit status alone.

## Compatibility oracle

For every scenario:

- **B→B** MUST produce `FULL` baseline semantics and bit-identical baseline
  bytes; otherwise the experiment baseline is invalid.
- **B→E** MUST produce `FULL` baseline semantics; an extended receiver may not
  require new-only data from an old sender.
- **E→E** MUST produce `FULL` extended semantics unless the declared base budget
  produces `INFEASIBLE_BASE_BUDGET`.
- **E→B**, for an optional extension, MUST produce `BASELINE_ONLY`,
  `SAFE_IGNORE`, or `NEGOTIATED_FALLBACK` as declared before implementation.
- **E→B**, for a critical extension, MUST produce `SAFE_REJECT` or
  `NEGOTIATED_FALLBACK`; `SAFE_IGNORE` is a safety failure.
- **E→B**, for a negotiated extension, MUST NOT transmit the extension after a
  peer declines support.

Changing an expected E→B outcome after observing candidate behavior requires a
new manifest and full rerun.

## Scenario pass rule

A `(candidate, scenario)` pair passes only when:

1. every B→B and B→E cell is `FULL`;
2. every E→E cell is `FULL` or pre-registered
   `INFEASIBLE_BASE_BUDGET`;
3. every E→B cell matches its exact pre-registered safe outcome;
4. no cell has an unsafe outcome; and
5. all required directions, boundaries, and nuisance-factor fixtures meet
   ADR-0013 coverage.

`UNSUPPORTED` and `IMPLEMENTATION_FAILED` are scenario failures and remain in
the twelve-scenario denominator. `INFEASIBLE_BASE_BUDGET` is reported
separately and does not penalize a candidate when both candidate encodings
exceed the same framing-neutral budget. If only one exceeds it because of its
own added overhead, that candidate fails the affected fixture.

## Per-scenario measurement vector

For each candidate and scenario, collect the following from the isolated
baseline-to-extension diff and test results.

### A. Semantic and compatibility results — primary

- terminal outcome for every logical cell;
- scenario pass/fail;
- count of unsafe cells by exact class;
- count of version pairings that retain full semantics;
- count using safe ignore, safe reject, or negotiated fallback; and
- count and reason for unsupported or budget-infeasible fixtures.

### B. Framing intervention — primary

- number of existing transmitted bits whose normative meaning changes;
- number of new fixed header bytes;
- number of new conditional/escape bytes;
- number and identity of reserved values consumed;
- number of existing values made invalid;
- whether a new framing revision or negotiation round is required;
- whether baseline frames remain bit-identical; and
- remaining primary namespace after the scenario.

Counts are computed from a machine-readable encoding declaration checked into
the scenario branch. Narrative claims do not replace the declaration.

### C. Wire cost — primary

For minimum, typical, and boundary fixtures:

- total framing bytes;
- bytes added relative to the candidate's baseline encoding;
- content bytes remaining under the direction-specific base budget;
- number of records/fragments required; and
- number of bytes that must be inspected to skip an unknown optional element.

Wire-cost results are exact integer counts, not sampled timing estimates.

### D. Implementation change surface — secondary

Measured separately for Python and C:

- production logical source lines added, deleted, and modified;
- public functions/types added, removed, or signature-changed;
- parser decision-point and cyclomatic-complexity delta;
- maximum parser nesting/state depth;
- C `.text`, `.rodata`, `.data`, and `.bss` delta under `-O2` and `-Os`;
- maximum caller-provided scratch-buffer delta; and
- conformance fixtures and assertions added.

Generated files, comments, blank lines, tests, and harness code are reported in
separate categories and excluded from production-SLOC totals. Tool names,
versions, and configuration are pinned in the manifest.

### E. Runtime cross-axis outputs — secondary here

Encode, decode, skip, and reject measurements follow ADR-0011. Cycles or time
are not folded into an extensibility score; they feed axes 2, 5, and 6 and are
linked to the same scenario ID.

### F. Qualitative disclosures — non-scored

- implementation assumptions;
- reviewer-visible specification rules added or changed;
- known ambiguity that required an oracle clarification before coding;
- reliance on a private or unassigned identifier; and
- any candidate-specific workaround.

Developer time, self-rated difficulty, and commit count are disclosed if
available but MUST NOT rank candidates.

## Safety gate and comparison rule

Comparison proceeds in three stages.

### Stage 1: Safety gate

A candidate with any `UNSAFE_ACCEPT`, `DESYNCHRONIZED`,
`UNBOUNDED_RESOURCE`, or `MEMORY_SAFETY_FAILURE` cell fails the extensibility
safety gate. The paper reports the cell and minimized reproducer. A safety-gate
failure cannot be offset by any other metric.

### Stage 2: Support and compatibility

Among candidates passing Stage 1, compare:

1. number of passed canonical scenarios out of 12;
2. number of E→B cells achieving their exact pre-registered safe outcome; and
3. number of scenarios that require a framing revision rather than an existing
   extension point.

These are reported as separate counts. Scenario weights are all one; no
scenario may be declared more important after results are known.

### Stage 3: Cost-vector Pareto comparison

For candidates tied on safety and scenario support, compare the primary
framing-intervention and wire-cost measures. Candidate A Pareto-dominates B only
if A is no worse on every applicable primary measure and strictly better on at
least one. Metrics whose preferable direction is not intrinsic are presented
without dominance claims.

If neither candidate dominates, the extensibility-axis conclusion is
**trade-off / no unique winner**. Secondary implementation and runtime measures
explain the trade-off but do not break a primary tie.

This ADR does not select the overall framing winner. A later synthesis ADR must
combine all six pre-registered axes and may conclude that evidence is mixed.

## Analysis integrity

- Report all twelve scenarios in numeric order, not in result-favorable order.
- Publish raw cell outcomes and isolated branch commits.
- Never replace a failed scenario with a “comparable” easier scenario.
- Corrections after unblinding require an erratum, a new manifest version, and
  clearly separated rerun results.
- Exploratory analyses are labeled exploratory and cannot alter the registered
  primary conclusion.

## Pros and Cons of the Options

### Option A: Developer time and difficulty ratings

- Good: Directly resembles ordinary engineering effort.
- Bad: Confounded by learning order and subjective judgment; irreproducible.

### Option B: Weighted score

- Good: Produces one simple ranking.
- Bad: Weights hide value judgments and allow safety or support deficits to be
  compensated by minor byte savings.

### Option C: Safety gate and Pareto vector

- Good: Preserves raw trade-offs and makes unsafe behavior non-compensable.
- Bad: May not produce a unique winner for this axis.

## References

- [ADR-0011](./0011-python-c-side-by-side-measurement.md) — runtime
  measurement contract.
- [ADR-0012](./0012-extensibility-scenario-taxonomy.md) — scenario taxonomy.
- [ADR-0013](./0013-extensibility-coverage-strategy.md) — coverage strategy.
- [RFC 6709, Design Considerations for Protocol Extensions](https://www.rfc-editor.org/rfc/rfc6709.html)
  — compatibility, testability, unknown-extension handling, and namespace
  considerations.
