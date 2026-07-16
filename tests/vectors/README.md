# Test vectors

This directory will contain versioned, normative I3C-EX test vectors. The
corpus is not yet complete; no implementation can claim conformance to a
released I3C-EX standard at this pre-alpha stage.

Vectors will be stored under a directory matching the specification version:

```text
vectors/
├── README.md
└── v0.2.0-draft/
    ├── framing/
    └── envelope/
```

Each vector will identify its specification version and section, inputs, and
bit-exact expected output. Vectors are hand-authored from specification
examples or independently reviewed derivations; they are not generated from
the reference implementation.

Draft vector sets may change with their draft. Once a corresponding
specification is frozen, its vector set is immutable and corrections require a
new version. I3C-EX vectors validate only I3C-EX content semantics and do not
test or establish I3C Basic conformance.
