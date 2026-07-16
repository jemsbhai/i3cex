# ADR-0017: Parse-complexity methodology

- **Status**: Accepted
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: McCabe, NIST structured testing guidance, GNU toolchain
  documentation, Lizard, and ADR-0011
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

Parse complexity is axis 2 of the framing bakeoff. Cyclomatic complexity is a
useful structural measure, but a single number can be gamed by splitting
functions or replacing branches with generated tables. Constrained endpoints
also care about code, static data, stack, scratch memory, parser state, and
failure paths.

The comparison therefore needs a reproducible measurement boundary and a
multi-dimensional result. Runtime belongs primarily to the latency and
throughput axes; this ADR measures the static structure and resource footprint
of equivalent decoders.

## Decision Drivers

- Equivalent semantics, validation policy, and public API for both candidates.
- Independent Python and freestanding-C implementations under ADR-0011.
- Tool-pinned, machine-readable structural measurements.
- Resistance to function splitting, generated-table, and hidden-state gaming.
- Embedded resource accounting without an opaque composite score.
- Separate visibility for valid, unknown-optional, and malformed paths.

## Considered Options

- Option A: Compare only the maximum cyclomatic complexity of one function.
- Option B: Use source lines or binary size as a single proxy.
- Option C: Report a preregistered structural and resource vector, retaining
  every component and applying a Pareto rule.

## Decision Outcome

Chosen option: **Option C — a static complexity and resource vector**, because
no single metric adequately represents decoder review burden or constrained
implementation cost.

### Consequences

**Good:**

- The result exposes local complexity, total decision structure, state, and
  embedded footprint independently.
- Refactoring cannot improve one reported number while concealing all other
  costs.
- The C primary result is directly relevant to the Cortex-M0 target.

**Bad:**

- The implementations need a carefully enforced common boundary.
- Generated artifacts and compiler/linker outputs must be archived.
- Results may show trade-offs instead of a single ranked candidate.

## Normative measurement contract

### 1. Compared implementation boundary

Measure only production encoder/decoder code and immutable tables necessary to:

- encode one complete candidate block;
- decode and validate one complete block;
- skip a well-formed unknown optional element when supported; and
- classify malformed or unsupported input.

Tests, benchmarks, logging, platform timers, serialization, and base-I3C driver
code are excluded. Shared utilities are included in each candidate's footprint
unless the final linked image proves they are byte-identical and genuinely
shared. Candidate-specific generated code and tables are included and also
reported separately.

### 2. Semantic and API equivalence gate

Before measurement, both candidates MUST pass the common vector corpus and the
differential correctness gate in ADR-0011. Their decoder APIs MUST expose the
same caller-owned input/output model, allocation policy, validation strictness,
error vocabulary, and recovery contract. Candidate-specific convenience APIs
are outside the comparison.

A failure is a correctness or safety result, not a low complexity score. An
implementation that omits required behavior is ineligible for dominance.

### 3. Cyclomatic complexity

The primary structural metric is McCabe cyclomatic complexity measured with one
pinned release and content hash of Lizard for both Python and C. The manifest
MUST freeze all tool arguments, source inclusion patterns, excluded generated
paths, and the tool's treatment of compound Boolean conditions and `switch`
cases.

For each language and candidate, report:

- per-function cyclomatic complexity;
- sum, median, 90th percentile, and maximum complexity;
- count of functions above complexity 10;
- function count, logical non-comment source lines, and token count; and
- the name and source location of every function attaining the maximum.

The unmodified McCabe-style result is primary. Modified cyclomatic complexity
or cognitive-complexity results may be secondary but cannot replace it.

### 4. Explicit parser structure

Independently of source layout, enumerate and archive:

- parser states and legal transitions;
- maximum nesting depth accepted;
- persistent and per-call state fields;
- distinct outcome classes and validation/error exits;
- maximum loop nesting; and
- lookup-table entries and generated productions.

State and transition counts derive from a machine-readable model or a static
instrumentation table checked against the implementation. Moving branches into
data therefore remains visible. If a candidate is deliberately stateless or
non-nesting, the corresponding values are zero rather than omitted.

### 5. Embedded resource vector

Build the freestanding C implementations under both frozen ADR-0011 compiler
configurations. From fully linked candidate-isolated images, report:

- `.text`, `.rodata`, initialized `.data`, and `.bss` bytes by section;
- total loadable and runtime memory footprints;
- maximum bounded static stack use per measured entry point from GCC
  `-fstack-usage` output plus a documented call-graph aggregation;
- caller-provided scratch and output-buffer requirements; and
- every function whose stack use is dynamic or unbounded.

GNU `size` System V section output and the linker map are the primary binary
sources. Stripped ELF files, map files, compiler `*.su` files, disassembly, and
full build commands MUST be archived. A dynamic or unbounded stack path is not
converted into a guessed number.

### 6. Measurement controls

Candidate builds MUST use the same compiler binary, flags, linker script,
public API shim, feature set, error strings policy, and link-time dependencies.
Dead-code elimination is permitted only when the common harness references all
required operations. Results are reported separately for `-O2` and `-Os` and
never pooled.

Python metrics use the same pinned analyzer but remain a replication line.
Python object size and interpreter memory are not compared with C footprint and
do not select the framing.

### 7. Analysis and decision rule

The primary result is the vector:

```text
(total cyclomatic complexity,
 maximum function complexity,
 functions above 10,
 parser states,
 parser transitions,
 production logical SLOC,
 linked code bytes,
 immutable data bytes,
 maximum bounded stack bytes,
 scratch bytes)
```

Raw components and distributions MUST be published. A candidate dominates only
if it is no worse in every applicable component and strictly better in at least
one, after passing correctness and safety gates. Missing, dynamic, or unbounded
resource values cannot be treated as zero. No weighted complexity index, rank
sum, or post-hoc subset may choose a winner.

### 8. Reproducibility

The final experiment manifest MUST pin tool versions and hashes, source-tree
commit, build container or environment, compiler and binutils binaries, flags,
inclusion rules, and analysis scripts. CI MUST regenerate the machine-readable
reports and fail if the source set or analyzer configuration drifts.

## Scope exclusions

- Human-subject maintainability or comprehension studies.
- General application logic above the framing API.
- Base I3C controller/target driver complexity.
- Runtime cycles, energy, and wire occupancy, which other axes measure.

## References

- Thomas J. McCabe, [A Complexity Measure](https://ieeexplore.ieee.org/document/1702388/), IEEE TSE, 1976.
- NIST, [Structured Testing: A Testing Methodology Using the Cyclomatic Complexity Metric](https://www.mccabe.com/pdf/mccabe-nist235r.pdf).
- [Lizard project documentation](https://github.com/terryyin/lizard).
- GNU Binutils, [`size` documentation](https://sourceware.org/binutils/docs/binutils/size.html).
- GCC, [Static Stack Usage Analysis](https://gcc.gnu.org/onlinedocs/gcc-13.1.0/gnat_ugn/Static-Stack-Usage-Analysis.html).
- `./0011-python-c-side-by-side-measurement.md`.
- `../../specs/I3CEX-0.2.0-draft.md` section 5.3.
