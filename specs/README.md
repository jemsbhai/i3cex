# Specifications

This directory contains all specification documents for the I3C-EX and
I4C projects.

## Document Naming Convention

Specifications are named:

```
<PROJECT>-<MAJOR>.<MINOR>.<PATCH>[-<STAGE>].md
```

Where:
- `<PROJECT>` is `I3CEX` or `I4C`
- `<MAJOR>.<MINOR>.<PATCH>` follows [Semantic Versioning 2.0.0](https://semver.org)
- `<STAGE>` is optional: `draft` for active development, `rc1`/`rc2`/... for
  release candidates. Omitted for stable releases.

## Versioning Rules

See [`../GOVERNANCE.md`](../GOVERNANCE.md) for full versioning rules.

Summary:
- **MAJOR**: Breaking protocol changes (incompatible frame formats, wire changes)
- **MINOR**: Backward-compatible additions (new optional sublayers, new CCCs)
- **PATCH**: Clarifications, errata, non-normative fixes
- `-draft`: Under active development; breaking changes expected without notice
- `-rcN`: Release candidate; stable unless critical issues found

## Immutability

Once a specification is published without the `-draft` suffix (i.e., as a
release candidate or stable release), the file is immutable. Errata and
clarifications produce new PATCH-level files. The only edits permitted to
non-draft specs are typo fixes that change no semantics.

Draft specifications can be edited freely until they graduate to `-rcN`.

## Current Documents

| Project | File | Status |
|---------|------|--------|
| I3C-EX | [`I3CEX-0.1.0-draft.md`](./I3CEX-0.1.0-draft.md) | Draft, unstable |
| I4C | [`I4C-0.0.1-placeholder.md`](./I4C-0.0.1-placeholder.md) | Placeholder |

## Specification Structure

All specifications follow the same section structure (MIPI-inspired but
simplified):

1. **Status and Versioning** — document version, status, replaces/superseded by
2. **Scope** — what this document covers and does not cover
3. **Terminology** — normative terms (MUST, SHOULD, MAY per RFC 2119)
4. **Background** — motivation, prior art, relationship to I3C
5. **Protocol Overview** — high-level architecture
6. **Normative Specification** — the actual wire-level/behavioural rules
7. **Optional Features** — clearly separated from mandatory features
8. **Conformance** — what an implementation must do to claim conformance
9. **Security Considerations**
10. **References**
11. **Appendix: Non-normative examples**

## Pre-registration

Specifications are written **before** implementation per our
pre-registration policy (see GOVERNANCE.md). This creates an immutable
record of the research hypothesis.

The implementation in `i3cex/` and `i4c/` is expected to track the spec,
not the other way around. Changes discovered through implementation that
require spec changes are recorded as ADRs first, then folded back into
the next draft.
