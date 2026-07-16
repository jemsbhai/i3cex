# ADR-0019: Bounded worst-case latency methodology

- **Status**: Proposed
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: Wilhelm et al., ADR-0011, ADR-0016, and the I3C Basic v1.2
  public specification
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

Worst-case latency impact is axis 5 of the framing bakeoff. The maximum value
observed in a benchmark is not automatically a worst-case execution-time
(WCET) bound. A defensible result must distinguish a safe analytical upper
bound, the maximum over a finite enumerated domain, and the maximum merely
observed in samples.

I3C-EX latency also has distinct sender-compute, wire-occupancy, and receiver-
compute components. Combining them without identifying base-protocol timing
assumptions would make the result platform-specific and could blur the I3C
Basic/I3C-EX boundary.

## Decision Drivers

- Terminology that does not overclaim sampled measurements as WCET proof.
- Exact separation of compute and candidate-induced wire occupancy.
- Cortex-M0 primary results under the cross-language rules in ADR-0011.
- A finite, preregistered boundary domain for valid and invalid paths.
- Static path analysis where a safe bound is supportable.
- No outlier removal, optional stopping, or unreported infeasible cases.

## Considered Options

- Option A: Report the largest microbenchmark timing as "WCET."
- Option B: Report only mean and percentile latency under a traffic trace.
- Option C: Combine bounded-domain measurement with auditable static analysis,
  and label each result according to the evidence it actually provides.

## Decision Outcome

Chosen option: **Option C — separate safe bounds, exhaustive bounded-domain
maxima, and sampled maxima**, because each is useful but they support different
claims. The paper may use "WCET bound" only for a documented safe upper bound.

### Consequences

**Good:**

- Timing claims remain honest when hardware or control-flow analysis cannot
  establish a complete bound.
- Compute and wire effects can be recombined for explicitly named base profiles.
- Pathological reject and unknown-element paths remain visible.

**Bad:**

- Static bound analysis on Cortex-M0 code is more involved than benchmarking.
- Some results may remain bounded-domain maxima rather than WCET bounds.
- End-to-end latency requires transparent base-timing parameters, not one
  universal number.

## Normative measurement contract

### 1. Terms and admissible claims

The artifact MUST use these distinct labels:

- **Safe WCET upper bound**: an analytically justified upper bound for the
  declared program, hardware, and input domain.
- **Bounded-domain maximum**: the maximum from exhaustive execution of a finite,
  fully enumerated domain, without claiming coverage outside that domain.
- **Maximum observed**: the largest value in a non-exhaustive measured sample.

A measured maximum, high percentile, or stress trace MUST NOT be called WCET.
If static analysis cannot provide a safe bound, the artifact must say so and
retain the weaker label.

### 2. Latency decomposition

For each candidate and logical message, report separately:

```text
sender_compute_cycles
candidate_wire_bytes
receiver_compute_cycles
fragment_count
one_time_setup_cost
```

For a declared base timing profile, the derived I3C-EX contribution is:

```text
extension_latency =
    sender_compute_time
  + candidate_induced_wire_occupancy
  + receiver_compute_time
```

Base transaction setup, arbitration, controller scheduling, and application
work are contextual parameters, not candidate decoder time. Setup/negotiation
is reported separately and amortized over ADR-0016 session lengths.

### 3. Input domain

The manifest MUST enumerate both directions and cross the ADR-0016 application
size, record-count, capability-level, transfer-budget, and fragmentation
boundaries. It additionally includes:

- valid encode and decode paths;
- unknown optional skip and unsupported critical paths;
- every deterministic malformed-input class from ADR-0018;
- first, middle, and last placement of the decisive record or error; and
- minimum, boundary-minus-one, boundary, and boundary-plus-one loop counts.

The domain is finite and hash-addressed. Cells outside hardware memory or
SysTick batch limits are explicitly classified and measured with an adjusted
predeclared batch count; they are not removed.

### 4. Primary compute platform and operation boundary

The STM32F072RB Cortex-M0 platform, compiler configurations, timer, warm-up,
batching, resets, pairing, ordering, and raw-observation policy in ADR-0011 are
normative. Encode, decode, skip, and reject remain separate operations.

Primary protocol-intrinsic measurements disable interrupts only inside the
timed region. Interrupt and scheduler sensitivity may be a secondary system
experiment, but it MUST NOT be mixed into the framing-compute distribution or
represented as a universal system WCET.

The paper reports cycles first and converts to time only using the verified,
recorded core clock. No timing observation is deleted merely for being extreme.

### 5. Static upper-bound analysis

For the fully linked primary `-O2` C image, archive the ELF, disassembly,
linker map, control-flow graph, loop-bound annotations, call graph, target
instruction-timing model, flash wait-state assumptions, and analysis-tool
version/hash. The analysis MUST account for all reachable paths in the declared
input domain, including error paths and compiler-generated helpers.

Every loop bound must trace to a framing field, negotiated cap, or explicit
harness bound. Indirect calls, recursion, dynamic stack, unresolved control
flow, timing anomalies, and unsupported instructions are reported. A safe WCET
claim is permitted only if every such item is conservatively bounded.

The `-Os` build is a replication line. If a trustworthy analyzer does not
support this Cortex-M0 binary and memory configuration, the project MUST report
that limitation rather than substitute a sampled maximum.

### 6. Bounded-domain measurement

Every executable cell follows ADR-0011: 30 independent reset blocks, 100
untimed warm-up batches, and 1,000 timed batches per block, using a frozen batch
loop selected in an unlabeled pilot. Candidate/workload order is randomized
from the recorded master seed and paired within a block.

Where the complete finite domain for a structural path can be enumerated, run
every member at least once in every independent block and call its largest
measurement a bounded-domain maximum. Otherwise report a maximum observed.
Exhaustive input enumeration does not by itself bound unmodeled hardware
interference.

### 7. Wire occupancy

Candidate-induced wire bytes come from ADR-0016 and are converted to occupancy
only through a manifest-defined base I3C Basic SDR timing profile. The profile
MUST cite the applicable public specification clauses or verified RTL/model,
state direction and transfer form, and include turnaround or base fields only
as common contextual terms.

No public Context Byte, CCC, MDB, bus speed, or timing mode is invented for
I3C-EX. Profiles are reported separately and never pooled.

### 8. Analysis and decision rule

For each operation and workload stratum, publish:

- any safe upper bound and all assumptions;
- bounded-domain maximum or maximum observed, correctly labeled;
- minimum, median, maximum, interquartile range, and 99th percentile of raw
  block medians;
- ADR-0011 paired `TLV / preamble` median ratio with 99% hierarchical
  bootstrap confidence interval; and
- decomposition into compute, wire, fragmentation, and amortized setup.

The hierarchy of evidence is a safe upper bound where available, then the
bounded-domain maximum, then sampled distribution. A candidate dominates only
if it is no worse in every applicable safety-gated workload and strictly better
in at least one. Crossovers and analysis gaps produce a trade-off, not a forced
ranking. No latency value compensates for a safety failure.

## Scope exclusions

- A universal whole-system WCET claim across all controllers, targets, clocks,
  flash configurations, interrupts, operating systems, or application loads.
- Electrical-layer and HDR timing not included in a frozen base profile.
- Network queuing beyond candidate-induced fragmentation and compute.
- Energy consumption.

## References

- Reinhard Wilhelm et al., [The Worst-Case Execution-Time Problem — Overview of Methods and Survey of Tools](https://www.cs.fsu.edu/~whalley/papers/tecs07.pdf), ACM TECS, 2008.
- `./0011-python-c-side-by-side-measurement.md`.
- `./0016-wire-overhead-methodology.md`.
- `./0018-legacy-safety-methodology.md`.
- `./0015-i3c-basic-v1.2-standards-alignment.md`.
- `../../specs/I3CEX-0.2.0-draft.md` section 5.3.
