# Specifications

This directory contains versioned I3C-EX specification documents.

## Naming and versioning

Documents use `I3CEX-MAJOR.MINOR.PATCH-STAGE.md`, where the optional stage is
`draft` or `rcN`. Version meaning and graduation rules are defined in
[GOVERNANCE.md](../GOVERNANCE.md).

Drafts may change. Once published as a release candidate or stable release, a
specification is immutable; semantic changes require a new version.

## Current documents

| File | Status |
|---|---|
| [I3CEX-0.2.0-draft.md](./I3CEX-0.2.0-draft.md) | Current draft; aligns the protocol boundary to I3C Basic v1.2 |
| [I3CEX-0.1.0-draft.md](./I3CEX-0.1.0-draft.md) | Historical pre-registration draft; superseded as the active draft |

The Python implementation at the repository root tracks the current draft.

## External standards boundary

These documents are original project materials. They do not reproduce or
replace MIPI specifications. Obtain I3C Basic from MIPI Alliance and review its
applicable terms independently. The project's normative alignment policy is
[I3C_BASIC_V1_2_ALIGNMENT.md](../docs/standards/I3C_BASIC_V1_2_ALIGNMENT.md).
