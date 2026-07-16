# All-axis bakeoff manifest

This directory contains the immutable preimplementation design freeze for the
six-axis preamble-versus-TLV framing bakeoff.

`manifest-v2.json` freezes:

- the latest public MIPI I3C Basic v1.2 baseline and the I3C-EX transport,
  identifier, and conformance boundaries;
- the exact accepted methodology family, baseline commit, candidates,
  directions, operations, and shared 84,240-cell workload grid;
- wire-overhead, parse-complexity, extensibility, legacy-safety, bounded-
  latency, and application-goodput contracts;
- fixed repetitions, a 40-million-execution C fuzz campaign per candidate,
  zero unsafe tolerance, and the Pareto/no-weighted-score decision rule; and
- the exact immutable dependency on the 192-cell extensibility manifest v1.

`manifest-v2.schema.json` documents the machine-readable shape, and
`manifest-v2.sha256` authenticates the exact manifest bytes.

Validate both frozen manifests with:

```bash
python scripts/validate_extensibility_manifest.py
python scripts/validate_bakeoff_manifest.py
```

## Measurement gate

Manifest v2 deliberately leaves `labeled_measurements_enabled` set to `false`.
It freezes experimental design before benchmark implementation. After the
candidate-neutral harness exists, an unlabeled, fixed-scope pilot may determine
only the settings explicitly delegated by the accepted ADRs. A separate
immutable execution manifest must then pin tool binary hashes, physical board
inventory, timing profiles, corpora, pilot-selected settings, and artifact
paths before any labeled observation is collected.

That execution manifest may reference but must never edit manifest v1 or v2.
