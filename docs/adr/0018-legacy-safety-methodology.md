# ADR-0018: Legacy-safety methodology

- **Status**: Proposed
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: RFC 6709, LLVM libFuzzer and sanitizer documentation,
  ADR-0012 through ADR-0014, and the I3C Basic v1.2 public specification
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

Legacy safety is axis 4 of the framing bakeoff. "Legacy" can mean a plain I3C
endpoint that never negotiated I3C-EX, an earlier I3C-EX implementation, or a
current decoder facing malformed input. Those cases have different safe
behavior and must not be collapsed into one malformed-frame test.

I3C-EX is explicitly context-scoped and opt-in. A plain or unnegotiated I3C
endpoint must not be exposed to I3C-EX semantics merely because ordinary
Private SDR content happens to resemble a candidate frame.

## Decision Drivers

- Preserve the standards boundary and explicit-negotiation rule in ADR-0015.
- Exercise old/new version skew and hostile inputs, not only happy paths.
- Fixed work budgets and seeds rather than time-based or optional stopping.
- Independent Python and C implementations with differential oracles.
- Sanitizer-backed host testing and replay on the primary embedded target.
- Zero tolerance for unsafe outcomes, with no compensation by average scores.

## Considered Options

- Option A: Unit-test a small hand-written malformed-input list.
- Option B: Run an open-ended fuzzer and report elapsed hours without a fixed
  input budget.
- Option C: Combine exhaustive boundary mutations, model-based version-skew
  tests, fixed-run coverage-guided fuzzing, and embedded replay.

## Decision Outcome

Chosen option: **Option C — layered deterministic and coverage-guided safety
testing**, because no single technique covers negotiation state, semantic
compatibility, memory safety, resource bounds, and parser resynchronization.

### Consequences

**Good:**

- Safety claims cover unnegotiated peers, version skew, and malformed frames.
- Fixed run counts make candidate effort comparable and reproducible.
- Crashes and sanitizer findings cannot be averaged away.

**Bad:**

- The fuzz corpus, state model, and sanitizer builds add substantial artifact
  work.
- Absence of a finding is evidence over a bounded campaign, not a proof of
  safety for every possible implementation.
- Embedded replay requires minimizing and transporting host-discovered cases.

## Normative measurement contract

### 1. Peer classes

Every candidate MUST be evaluated against three distinct peer classes:

1. **Plain or unnegotiated I3C peer.** I3C-EX semantics are disabled. No
   candidate decoder is invoked and ordinary Private SDR bytes remain ordinary
   application content, even if they collide with an experimental marker.
2. **Version-skewed I3C-EX peer.** An old receiver, new receiver, old sender,
   and new sender are crossed as defined by ADR-0012 through ADR-0014.
3. **Malformed or misbehaving I3C-EX peer.** Negotiation succeeded for the
   exact endpoint and context, but the transferred content violates framing or
   negotiated resource constraints.

The artifact MUST not call class 1 an I3C-EX decoder result. Its oracle is
non-interference: no I3C-EX state transition, allocation, or interpretation.

### 2. State-machine scenarios

The machine-readable model MUST exercise at least:

- reset, Dynamic Address Assignment, context change, and re-negotiation;
- traffic before negotiation, after successful negotiation, after failure,
  and after state invalidation;
- correct and incorrect controller/target, direction, and context tuple;
- endpoint restart, stale capability cache, and version downgrade; and
- interleaving ordinary Private SDR and I3C-EX transfers.

Every transition has a predeclared state and oracle. I3C-EX remains disabled
unless all gating predicates in ADR-0015 hold.

### 3. Deterministic malformed-input matrix

Starting from every valid boundary vector, exhaustively apply all applicable
single mutations:

- flip each framing control bit;
- truncate at every framing-byte position;
- extend with one and with the maximum permitted trailing byte sequence;
- change each length to boundary minus one, boundary, and boundary plus one;
- set every reserved field or value class;
- insert unknown optional and unknown critical elements;
- duplicate, omit, and reorder records where order has semantics;
- exceed record, block, SETMWL-derived, and SETMRL-derived caps by one and by
  the maximum representable amount; and
- corrupt version, capability, context, direction, and endpoint association.

Applicable pairwise and longer mutation combinations follow ADR-0013. The
manifest MUST state which combinations are exhaustive and which use generated
coverage.

### 4. Oracles and required outcomes

Use the outcome vocabulary in ADR-0014. For each input, record the expected and
observed outcome, bytes consumed, state transition, output writes, recovery
position, and resource high-water marks.

Required invariants are:

- no crash, hang, undefined behavior, out-of-bounds access, integer overflow,
  use-after-free, or unbounded allocation/recursion;
- no decode success for an invalid critical construct;
- safe skip of an unknown optional construct only where its boundary is known;
- no output commit before complete validation unless the API explicitly marks
  a reversible partial result;
- work and memory remain within preregistered bounds; and
- after a rejected complete block, the next independently framed valid block
  decodes according to the declared recovery contract.

False acceptance and false rejection are reported separately. A valid-but-
unsupported feature is not malformed and must retain its registered
`safe-skip`, `safe-ignore`, or `unsupported` oracle.

### 5. Python generative testing

The Python reference uses a pinned Hypothesis release for property and
rule-based state-machine testing. The database is disabled for labeled runs;
the exact example count, generation phases, health-check policy, deadline
policy, seed list, and strategies are frozen. Shrunk counterexamples and the
original failing examples MUST both be archived.

Python testing supplies semantic and state-machine coverage. It does not
replace the C memory-safety campaign.

### 6. C coverage-guided fuzzing

Each C decoder uses a narrow, deterministic libFuzzer target built with a
pinned matching Clang release. Each candidate receives the same valid seed
corpus, framing-neutral semantic dictionary, maximum input length, and
operation harness.

The primary campaign is ten recorded seeds of exactly 1,000,000 executions per
candidate and target, for 10,000,000 executions total per target. Stop-on-time,
"until coverage plateaus," and corpus reuse from one candidate to seed the
other are prohibited. Candidate order and machine assignment are
counterbalanced.

Run separate builds with AddressSanitizer and UndefinedBehaviorSanitizer using
the documented recover/abort settings frozen in the manifest. Project-code
sanitizer suppressions are prohibited. Every crash, timeout, sanitizer report,
and artifact integrity failure is preserved and minimized. The complete final
corpus is replayed as a deterministic regression test.

### 7. Resource-bound checks

The harness MUST impose manifest-defined maximum input bytes, parser steps,
loop iterations, output bytes, stack depth, scratch bytes, and wall-clock guard
time. The wall-clock guard detects a hang but does not replace the structural
step bound. Exceeding any bound is an unsafe outcome.

Allocation failure, short output buffers, and maximum caller-provided buffers
are explicit cases. The freestanding C path MUST not dynamically allocate in
the measured decoder, as required by ADR-0011.

### 8. Embedded replay

All deterministic boundary vectors, every minimized host finding, and a
preregistered coverage sample of the final corpus MUST replay on the
STM32F072RB target under both ADR-0011 compiler configurations. Replay records
outcome, guard-region integrity, stack/scratch high-water marks, and completion
within the structural step bound. Host-only sanitizer success is not described
as target memory-safety proof.

### 9. Analysis and safety gate

Report per peer class and candidate:

- expected/observed outcome confusion matrix;
- false accepts and false rejects;
- crashes, hangs, sanitizer findings, and bound violations;
- unique coverage edges and corpus size as campaign diagnostics;
- recovery failures and cross-frame state contamination; and
- every failing input, including duplicates before deduplication.

Any unsafe outcome fails the candidate's bakeoff safety gate. It cannot be
offset by better wire cost, complexity, latency, throughput, or coverage. A
zero-finding campaign is reported with its exact bounded effort, never as proof
that no bug exists.

## Scope exclusions

- Electrical fault injection and base-protocol parity/CRC behavior.
- Physical attacks, confidentiality, authentication, and device attestation.
- General application code after a successfully decoded framing block.
- Claims about MIPI conformance testing or certification.

## References

- [RFC 6709, Design Considerations for Protocol Extensions](https://www.rfc-editor.org/rfc/rfc6709.html).
- LLVM, [libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html).
- Clang, [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html).
- Clang, [UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html).
- `./0012-extensibility-scenario-taxonomy.md`.
- `./0013-extensibility-coverage-strategy.md`.
- `./0014-extensibility-per-scenario-measurements.md`.
- `./0015-i3c-basic-v1.2-standards-alignment.md`.
