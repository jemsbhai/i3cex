# Extensibility experiment manifest

This directory freezes the framing-neutral inputs for the I3C-EX extensibility
bakeoff defined by ADR-0012 through ADR-0014.

`manifest-v1.json` records:

- the accepted methodology and exact baseline commit;
- both framing candidates, four version pairings, and both Private SDR content
  directions, producing 192 mandatory logical cells;
- the twelve canonical semantic scenarios and their old/new compatibility
  oracles;
- boundary and nuisance-factor models;
- prohibited safety outcomes; and
- deterministic implementation order and random seed.

`manifest-v1.schema.json` documents the machine-readable shape.
`manifest-v1.sha256` authenticates the exact manifest bytes.

Validate the freeze with:

```bash
python scripts/validate_extensibility_manifest.py
```

The manifest deliberately sets `labeled_measurements_enabled` to `false` and
remains an immutable record of the state before the remaining per-axis methods
were accepted. The all-axis
[bakeoff manifest v2](../bakeoff/README.md) references its exact SHA-256 rather
than modifying it. Pilot data is exploratory and cannot be pooled with the
future registered result set.
