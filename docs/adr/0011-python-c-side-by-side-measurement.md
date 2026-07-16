# ADR-0011: Python and C side-by-side measurement for runtime axes

- **Status**: Accepted
- **Date**: 2026-07-16
- **Deciders**: Project maintainer
- **Consulted**: Kalibera and Jones; Georges, Buytaert, and Eeckhout; Arm,
  STMicroelectronics, Python, and GCC documentation
- **Informed**: Future collaborators, artifact evaluators, and paper reviewers

## Context and Problem Statement

The Python implementation is the executable semantic reference, but Python
timings alone do not represent constrained I3C endpoints. Conversely, a C-only
benchmark can hide semantic divergence or implementation-specific shortcuts.
The bakeoff therefore needs a cross-language rule that preserves a common
protocol definition while producing publication-relevant embedded results.

This ADR governs runtime-bearing axes: parse complexity where it includes
executable cost, worst-case latency, throughput, and any extensibility scenario
that adds parser work. It does not compare Python speed directly with C speed.

## Decision Drivers

- A single vector corpus and operation boundary for both framing candidates.
- Publication-relevant measurements on a constrained Cortex-M0 endpoint.
- A readable Python oracle for differential validation.
- Protection against compiler, warm-up, ordering, and timing-harness artifacts.
- Raw-data reproducibility and no post-hoc outlier removal or optional stopping.
- Separation of framing cost from I3C wire time and base-controller behavior.

## Considered Options

- Option A: Measure only the Python reference implementation.
- Option B: Measure only an embedded C implementation.
- Option C: Validate Python and C side by side, but use within-language paired
  comparisons and treat embedded C as the primary runtime endpoint.

## Decision Outcome

Chosen option: **Option C — one semantic corpus, independent Python and C
implementations, within-language paired comparisons, and embedded C as the
primary runtime endpoint**, because this combines auditability with an endpoint
representative of constrained devices without conflating language performance.

### Consequences

**Good:**

- Every measured C result is tied to a Python-validated semantic case.
- Preamble-versus-TLV ratios are meaningful within each language and platform.
- The paper can distinguish wire cost, parser cost, and host-language overhead.
- Cross-language disagreement becomes a reported result rather than something
  averaged away.

**Bad:**

- Two independent implementations and a differential harness are required.
- Embedded runs require physical hardware and a pinned cross-toolchain.
- Runtime methodology is more expensive than a single host microbenchmark.

## Normative measurement contract

### 1. Independent implementations

The Python and C encoders/decoders MUST be independent production
implementations. They MAY share machine-readable test vectors and generated
constant tables, but MUST NOT call one another or share generated executable
parser code.

The C implementation MUST target freestanding ISO C11 and MUST avoid dynamic
allocation in the timed framing path. Any platform abstraction used for timing
MUST live outside the framing implementation.

### 2. Common semantic corpus

Before a case is timed, both implementations MUST:

1. encode the same structured input to bit-identical bytes;
2. decode those bytes to the same structured output;
3. return the same outcome class for every invalid or unsupported input; and
4. pass deterministic randomized differential tests using a recorded seed.

A case that fails this gate is a correctness failure and MUST NOT produce a
performance datum. It remains in the results manifest as failed.

### 3. Operation boundaries

The following operations are measured separately:

- encode one complete framing block into a caller-provided output buffer;
- decode and validate one complete framing block from a caller-provided buffer;
- skip one well-formed unknown optional element, where the candidate supports
  that operation; and
- reject one malformed or unsupported block.

Allocation, vector loading, logging, serialization of results, I3C transfer
time, and test assertion work MUST remain outside the timed region. Setup that
is inherently required by the framing algorithm MUST remain inside it and be
identified in the manifest.

### 4. Primary embedded platform

The primary runtime platform is an ST NUCLEO-F072RB carrying an STM32F072RB
Cortex-M0, operated at a recorded fixed core clock no higher than 48 MHz. Board
revision, MCU marking, clock tree, flash wait-state configuration, supply
method, and ambient temperature MUST be recorded.

This board measures framing computation only; it is not evidence of I3C
controller or target conformance.

Cycle measurement uses the Cortex-M SysTick timer configured from the processor
clock as a free-running 24-bit counter. Interrupts MUST be disabled only for the
timed region. The harness MUST:

- measure and publish timer-read plus loop overhead;
- use a volatile result sink to prevent dead-code elimination;
- keep each batch below half of one SysTick wrap;
- make a timed batch at least 100 times longer than measured timer overhead;
- subtract only the matched empty-harness median, never a fitted correction;
- detect counter wrap and discard the entire invalid block with a recorded
  harness-error reason; and
- verify clock configuration before and after every independent run.

The batch loop count is selected in an unlabeled pilot, then frozen in the
experiment manifest before labeled measurements begin.

### 5. C build configurations

The primary C result uses a pinned `arm-none-eabi-gcc` release with:

```text
-std=c11 -mcpu=cortex-m0 -mthumb -O2 -fno-lto
```

The secondary size-oriented result replaces `-O2` with `-Os`. Both builds use
the same warning-as-error policy and linker script. `-O0`, `-O3`, profile-guided
optimization, and link-time optimization are excluded from primary claims.

The exact compiler binary hash, full version output, complete flags, linker map,
ELF file, and disassembly MUST be archived. Candidate order in the image MUST be
counterbalanced across independent runs so layout does not consistently favor
one candidate.

### 6. Python configuration

CPython 3.12 is the primary Python line because it is the middle supported
version. The exact patch release, executable hash, platform, CPU, power policy,
and dependency lock MUST be recorded. Python 3.11 and 3.13 are replication
lines, not pooled with 3.12.

Python measurements use `time.perf_counter_ns()` through a dedicated harness.
Each independent block runs in a fresh process. The harness performs untimed
warm-up, calibrates a batch to the same 100-times-timer-overhead rule, and
records the clock implementation and resolution. Garbage collection state is
left at its interpreter default and recorded; GC is forced before, never
during, each measured block.

### 7. Repetitions, pairing, and ordering

For every candidate, operation, workload, platform, and build configuration:

- execute 30 independent blocks;
- perform 100 untimed warm-up batches per block;
- collect 1,000 timed batches per block;
- pair preamble and TLV cases within the same block; and
- randomize candidate and workload order from a recorded master seed.

Each embedded block begins with a hardware reset and a fresh harness
initialization. Each Python block begins in a fresh interpreter process.

The fixed counts prevent optional stopping. A run may be invalidated only for a
predeclared harness failure: clock verification failure, counter wrap, vector
gate failure, process crash, or corrupted result record. Timing values are
never removed merely because they are extreme.

### 8. Analysis and reporting

Absolute measurements are reported, but the primary contrast is the paired
ratio `TLV / preamble` within the same language, platform, operation, and
workload. Python-to-C speed ratios MUST NOT be used to choose a framing.

For each primary contrast, report:

- all raw block and batch observations;
- per-block median, minimum, maximum, and interquartile range;
- the paired ratio of medians;
- a 99% hierarchical bootstrap confidence interval over independent blocks;
- code size and static RAM from the linker map for each C build; and
- every invalidated block and its predeclared reason.

No universal practical-significance threshold is imposed here; each per-axis
ADR MUST pre-register its own equivalence margin before measurements. When
Python and embedded C imply different candidate ordering, the discrepancy MUST
be reported as an implementation-by-framing interaction. Embedded C remains the
primary runtime endpoint, but disagreement prohibits a language-independent
performance claim.

### 9. Reproducibility artifact

The artifact MUST contain source commits, vector and manifest hashes, compiler
and interpreter metadata, raw observations, analysis scripts, linker maps,
ELFs, disassemblies, board setup, and one command for regenerating every table
and figure from raw data. Generated figures are outputs, never the sole record.

## Pros and Cons of the Options

### Option A: Python only

- Good: Fastest to build and easiest for reviewers to inspect.
- Bad: Host interpreter behavior is not representative of constrained targets.
- Bad: Parser allocation and dispatch costs can dominate the framing effect.

### Option B: C only

- Good: Directly relevant to constrained firmware.
- Bad: Harder to audit semantic correctness and easier to optimize candidates
  asymmetrically.
- Bad: A single implementation can turn an implementation bug into a protocol
  conclusion.

### Option C: Python oracle plus independently measured C

- Good: Separates semantic validity from platform runtime evidence.
- Good: Differential testing catches cross-language drift before timing.
- Bad: Highest implementation and artifact-maintenance cost.

## References

- [ADR-0010](./0010-bakeoff-evaluation-methodology.md) — bakeoff
  meta-methodology.
- [Rigorous Benchmarking in Reasonable Time](https://kar.kent.ac.uk/33611/) —
  experimental levels, uncertainty, and repetition.
- [Statistically Rigorous Java Performance Evaluation](https://biblio.ugent.be/publication/417084)
  — independent executions and uncertainty reporting.
- [Python `perf_counter_ns`](https://docs.python.org/3.12/library/time.html#time.perf_counter_ns)
  — monotonic high-resolution process timing interface.
- [GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)
  — meanings of `-O2`, `-Os`, and LTO controls.
- [ST NUCLEO-F072RB](https://www.st.com/en/evaluation-tools/nucleo-f072rb.html)
  and [STM32F072RB](https://www.st.com/en/microcontrollers-microprocessors/stm32f072rb.html)
  — active Cortex-M0 reference platform.
- [CMSIS SysTick documentation](https://arm-software.github.io/CMSIS_6/main/Core/group__SysTick__gr.html)
  — use of SysTick for time measurement.
