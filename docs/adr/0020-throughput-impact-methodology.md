# ADR-0020: Throughput-impact methodology

- **Status**: Accepted
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: RFC 1242, RFC 2544, RFC 9004, ADR-0011, ADR-0016, and
  ADR-0019
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

Throughput impact is axis 6 of the framing bakeoff. Raw I3C signalling rate is
not application throughput: framing consumes content budget, fragmentation can
add transfers, and endpoint compute or backpressure can prevent saturation.
The useful quantity is delivered application content per elapsed interval under
a declared, loss-free workload.

The method must keep exact analytical limits separate from empirical saturation
results and must not claim one selected controller represents every I3C Basic
implementation.

## Decision Drivers

- Application goodput rather than candidate or base framing bytes.
- Both transfer directions, boundary sizes, capability levels, and session
  lengths.
- Exact wire-efficiency ceilings plus endpoint saturation measurements.
- A fixed zero-loss offered-load search and backlog criterion.
- Explicit compute, wire, fragmentation, and setup decomposition.
- No pooling across workloads that have different crossover behavior.

## Considered Options

- Option A: Derive throughput only from nominal bus rate and minimum overhead.
- Option B: Send as fast as one host implementation permits and report an
  average rate.
- Option C: Report exact goodput ceilings and use a preregistered loss-free
  offered-load search on named hardware/model profiles.

## Decision Outcome

Chosen option: **Option C — analytical ceilings plus empirical zero-loss
saturation**, because it distinguishes format efficiency from a particular
endpoint's ability to keep the bus supplied and drained.

### Consequences

**Good:**

- Results show whether wire bytes, compute, or fragmentation limits goodput.
- Cold single-message and long steady-state sessions remain distinguishable.
- The method can be replicated on later I3C controllers without rewriting the
  core metric.

**Bad:**

- Empirical results are profile-specific and require calibrated offered load.
- A zero-loss search with one million measured transactions per trial is
  expensive.
- Different payload sizes may yield different winners.

## Normative measurement contract

### 1. Definitions

For one measured interval:

```text
application_goodput =
    successfully_delivered_application_bytes / elapsed_seconds

transaction_throughput =
    successfully_delivered_logical_messages / elapsed_seconds

bus_utilization =
    occupied_base_transfer_time / elapsed_seconds
```

Only application value bytes that pass the receiver's semantic correctness
check count as delivered. Candidate framing, common I3C-EX bytes, base I3C
fields, padding, duplicates, retries, and rejected messages do not count.

The maximum sustainable offered load is the fastest offered logical-message
rate for which the complete trial has zero loss, zero duplication, zero parse
errors, zero ordering errors where order is required, and no positive net
backlog growth.

### 2. Workload grid

The manifest MUST cross:

- controller-to-target and target-to-controller directions;
- capability levels EX-1 through EX-6;
- the application-size, record-count, transfer-budget, fragmentation, and
  session-length grids in ADR-0016;
- setup-cold and steady-state phases; and
- every accepted framing operation that performs recurring work.

The semantic-equivalence gate from ADR-0016 and differential correctness gate
from ADR-0011 apply. Unsupported or infeasible cells remain in the result set
with a reason and are never converted to zero goodput.

### 3. Analytical ceiling

For every valid cell and named base SDR timing profile, compute exact recurring
wire occupancy from emitted bytes and the profile's base-protocol timing model.
The wire-only goodput ceiling is:

```text
wire_goodput_ceiling = application_bytes / occupied_wire_time
```

Report logical transfers, fragments, content efficiency, and setup-amortized
goodput for session lengths `1, 10, 100, 1000, 1000000`. A zero-byte
application message has zero application goodput even if transaction throughput
is nonzero.

The analytical ceiling assumes endpoint computation can overlap or keep pace as
declared by the profile. It MUST be labeled a ceiling, not a measured sustained
rate.

### 4. Empirical profiles and calibration

Each empirical profile MUST record controller and target hardware or verified
model, firmware commits, clocks, transfer direction, I3C mode, content limits,
queue depths, DMA/interrupt/polling mode, compiler artifacts, supply method,
temperature, and instrumentation uncertainty. The profile must use standard
I3C Basic transfers and the context/negotiation boundary in ADR-0015.

An unlabeled calibration pilot selects offered-load resolution, queue depth,
batching, and trial timeout. These values are frozen before candidate labels are
revealed. Calibration data cannot enter the final comparison.

### 5. Offered-load search

For each candidate and workload cell:

1. reset and establish the declared context and negotiation state;
2. perform exactly 10,000 untimed warm-up logical messages;
3. run a bracketed binary search over offered message rate using the frozen
   resolution and identical initial brackets;
4. measure exactly 1,000,000 logical messages at each trial rate; and
5. repeat the final passing rate and first failing rate in 30 independent reset
   blocks, paired and counterbalanced between candidates.

The generator uses scheduled offered timestamps rather than a closed loop that
waits for each response. Every trial records offered, accepted, delivered,
dropped, duplicated, reordered, rejected, and outstanding messages plus queue
high-water marks. A trial passes only if the required zero-error criteria hold
and end backlog is no greater than start backlog after the frozen drain window.

No time-based stopping, coverage plateau, outlier deletion, or candidate-
specific search resolution is permitted. A harness overload or instrumentation
drop invalidates the trial with a recorded reason; it does not become a
candidate failure.

### 6. Compute and wire decomposition

Record sender encode and receiver decode cycles using ADR-0011 operation
boundaries, candidate-induced wire occupancy from ADR-0016, and latency bounds
or maxima with the labels in ADR-0019. Where compute and transfer overlap,
measure and state the overlap policy rather than summing costs mechanically.

Required secondary metrics are cycles per delivered application byte, wire
bytes per delivered byte, fragments per message, queue high-water mark, and
the gap between analytical ceiling and measured goodput. Python throughput is a
semantic replication line and is not pooled with embedded results.

### 7. Base-protocol boundary

Every bus-rate and timing assumption MUST come from a named public I3C Basic
profile or a verified model and be recorded with direction and transfer form.
I3C-EX does not alter signalling, arbitration, addressing, or base framing.
The experiment MUST not invent a public Context Byte, extension CCC, MDB, or
I3C-EX-specific bus mode.

Base retransmission and arbitration behavior may be reported in a secondary
sensitivity study, but the primary candidate comparison uses the same
controlled base profile and reports zero injected base errors.

### 8. Analysis and decision rule

For each workload and profile, publish:

- exact wire-only goodput ceiling;
- maximum sustainable offered rate and measured application goodput;
- transaction throughput and bus utilization;
- minimum, median, maximum, interquartile range, and 99th percentile across
  independent block results;
- paired candidate ratio with a 99% hierarchical bootstrap confidence interval;
  and
- compute/wire/fragmentation/setup decomposition.

Do not pool directions, payload sizes, capability levels, session lengths, or
profiles. A candidate dominates only if it is no worse in every applicable,
safety-gated cell and strictly better in at least one. Otherwise report the
trade-off and crossover surfaces. No weighted application mix or composite
throughput score may select the framing after results are observed.

### 9. Reproducibility

Archive the manifest, emitted frames, load-generator schedule, raw event log,
queue observations, calibration record, clock checks, firmware/binary hashes,
timing-profile source, analysis scripts, and every invalidated run. A replay
tool MUST recompute delivered application bytes and all pass/fail decisions
from the raw log.

## Scope exclusions

- HDR modes until separately specified and preregistered.
- Multi-controller arbitration and unrelated application computation.
- Energy efficiency and thermal throttling beyond rejecting an invalid run.
- A claim that one hardware profile characterizes all I3C Basic devices.

## References

- [RFC 1242, Benchmarking Terminology for Network Interconnection Devices](https://www.rfc-editor.org/rfc/rfc1242.html).
- [RFC 2544, Benchmarking Methodology for Network Interconnect Devices](https://www.rfc-editor.org/rfc/rfc2544.html).
- [RFC 9004, Updates for the Back-to-Back Frame Benchmark in RFC 2544](https://www.rfc-editor.org/rfc/rfc9004.html).
- `./0011-python-c-side-by-side-measurement.md`.
- `./0016-wire-overhead-methodology.md`.
- `./0019-bounded-worst-case-latency-methodology.md`.
- `./0015-i3c-basic-v1.2-standards-alignment.md`.
- `../../specs/I3CEX-0.2.0-draft.md` section 5.3.
