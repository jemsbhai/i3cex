# ADR-0016: Wire-overhead methodology

- **Status**: Accepted
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: RFC 6709, ADR-0009, ADR-0010, and the I3C Basic v1.2
  public specification
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

Wire overhead is axis 1 of the framing bakeoff. Preamble and TLV framing spend
different numbers of bytes depending on capability level, record count,
payload size, transfer budget, and session length. Comparing one hand-picked
message or reporting only a mean would conceal crossovers and fragmentation.

This axis concerns bytes introduced by I3C-EX framing. It does not redefine or
benchmark I3C Basic signalling, and it must not imply that an unassigned I3C-EX
identifier has a public wire value.

## Decision Drivers

- Exact byte accounting where the formats are deterministic.
- The same semantic content, direction, and base-transfer budget for both
  candidates.
- Separate reporting of base-protocol, I3C-EX common, and candidate-specific
  costs.
- Explicit treatment of fragmentation and one-time negotiation cost.
- No workload-weighted score chosen after results are known.
- Compatibility with SETMWL/SETMRL-derived content budgets.

## Considered Options

- Option A: Compare only minimum framing bytes for one representative message.
- Option B: Sample an application trace and report average overhead.
- Option C: Exhaustively calculate a preregistered finite workload grid and
  report exact per-cell results and Pareto relationships.

## Decision Outcome

Chosen option: **Option C — exact accounting over a preregistered finite
grid**, because the candidate formats are deterministic and therefore do not
need statistical estimation for this axis. A trace may be reported later as a
clearly secondary case study, but it cannot replace the core grid.

### Consequences

**Good:**

- Every reported overhead value can be recomputed without hardware.
- Crossovers, infeasible cells, and fragmentation cliffs remain visible.
- One-time discovery cost cannot be hidden inside or confused with recurring
  framing cost.

**Bad:**

- The result is a family of trade-offs rather than a single convenient number.
- Exact candidate encodings must exist before the manifest can be completed.
- Base-transfer budgets must be represented as profiles rather than assumed
  from a single platform.

## Normative measurement contract

### 1. Accounting boundary

For each logical application message, the artifact MUST report these byte
classes separately:

1. application content bytes;
2. base I3C transfer bytes, shown only as contextual accounting;
3. I3C-EX common recurring bytes shared by both candidates;
4. candidate-specific framing bytes;
5. padding or fragmentation bytes; and
6. one-time discovery or context-establishment bytes.

The primary axis-1 contrast is classes 4 and 5. Base I3C fields MUST NOT be
credited to either candidate. Wire time, parser execution, and retry behavior
belong to ADR-0019 and ADR-0020 rather than this byte-count axis.

### 2. Semantic equivalence gate

A comparison cell is valid only if both candidates encode the same ordered set
of sublayer records and bit-identical application values, and both decode to
the same structured value. Removing semantics to make one candidate smaller is
not permitted. A candidate incapable of representing the cell is recorded as
`unsupported`, not assigned an estimated byte count.

### 3. Core workload grid

The machine-readable experiment manifest MUST cross both directions with:

- capability levels EX-1 through EX-6;
- application-value sizes `0, 1, 4, 8, 16, 32, 64, 127, 128, 255, 256,
  1024, 4096` bytes;
- record counts `1, 2, 4, 6, 16, 64, 127, 128, 255` where semantically valid;
- session lengths `1, 10, 100, 1000, 1000000` logical messages; and
- every applicable canonical extensibility scenario from ADR-0012.

A base-transfer profile supplies the direction-specific content budget derived
from SETMWL or SETMRL. Values beyond that budget are not silently dropped: the
artifact MUST mark whether the candidate fragments the message, rejects it, or
cannot represent it. The final manifest MUST contain boundary values one byte
below, at, and one byte above every candidate or negotiated length boundary.

Profiles and values may be added before labeled measurement, but none may be
removed after the manifest is frozen. No empirical distribution weights the
core cells.

### 4. Exact calculations

For every valid cell and candidate, calculate:

```text
candidate_overhead = candidate_framing + padding + fragmentation
recurring_wire_bytes = application_content + i3cex_common + candidate_overhead
payload_efficiency = application_content / recurring_wire_bytes
remaining_content_budget = base_content_budget - recurring_wire_bytes
amortized_bytes_per_message =
    recurring_wire_bytes + one_time_setup_bytes / session_length
```

Payload efficiency is defined as `1.0` for a zero-byte application message only
if recurring wire bytes are also zero; otherwise it is `0.0`. This convention
MUST be encoded in the analysis script, not chosen while plotting.

The artifact MUST additionally report transfer count, fragment count, and
unused bytes in the final fragment. All integer byte counts are exact and have
no confidence interval. Implementations MUST cross-check the analytical result
against emitted byte strings for every executable cell.

### 5. Setup and amortization

Context selection, capability discovery, and other one-time setup are reported
separately and amortized over the fixed session lengths. The primary recurring
comparison excludes setup. The paper MUST show both recurring and amortized
views and MUST NOT describe a one-message session as steady state.

Symbolic or privately configured experimental identifiers may be counted by
width, but the artifact MUST state that no public I3C-EX Context Byte, CCC, or
MDB allocation is implied.

### 6. Analysis and decision rule

Report each core cell and aggregate only by predeclared strata: direction,
capability level, application-size band, record count, transfer-budget profile,
and session length. Required summaries are median, minimum, maximum, and the
complete empirical distribution of exact cell values; they are descriptive,
not uncertainty estimates.

Candidate A dominates candidate B in a stratum only if A uses no more
candidate-specific bytes in every cell and fewer bytes in at least one cell,
with no correctness, safety, or representability failure. Otherwise the result
is a trade-off, including any crossover point. No weighted mean, rank sum, or
composite axis score may select a winner.

### 7. Reproducibility

The frozen manifest, generator, emitted candidate frames, accounting table, and
analysis output MUST be archived. The generator MUST be deterministic from a
recorded seed even though byte counts themselves are not random. CI MUST verify
that analytical counts equal actual encoded lengths for the complete executable
grid.

## Scope exclusions

- Electrical symbols, parity, bus turnaround, arbitration, and error recovery
  defined by the base protocol.
- HDR modes until separately specified and preregistered.
- Runtime latency, CPU use, and sustained offered load.
- Any claim of MIPI certification, endorsement, or identifier assignment.

## References

- [RFC 6709, Design Considerations for Protocol Extensions](https://www.rfc-editor.org/rfc/rfc6709.html).
- `./0009-efficiency-principle.md` — normative cost/benefit principle.
- `./0010-bakeoff-evaluation-methodology.md` — six-axis framework.
- `./0012-extensibility-scenario-taxonomy.md` — canonical evolution cases.
- `./0015-i3c-basic-v1.2-standards-alignment.md` — base-protocol boundary.
- `../../specs/I3CEX-0.2.0-draft.md` section 5.3.
