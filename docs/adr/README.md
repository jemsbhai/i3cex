# Architecture Decision Records

This directory records significant architectural decisions made during
the development of the `i3cex` package.

## What is an ADR?

An Architecture Decision Record is a short document capturing a single
design decision, its context, the alternatives considered, the chosen
option, and its consequences. ADRs are **immutable** — once accepted,
they are never edited. If a decision is superseded, a new ADR is
written that references and supersedes the old one.

This follows the pattern established by [Michael Nygard's original
2011 blog post](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
and widely adopted across the software industry.

## Numbering

ADRs are numbered sequentially starting at `0001`. Numbers are never
reused.

## Status Values

An ADR is in one of these states:

- `Proposed` — under discussion.
- `Accepted` — the decision has been made.
- `Superseded by ADR-NNNN` — a later ADR replaces this one.
- `Deprecated` — no longer applies but not explicitly superseded.

## Writing a New ADR

Copy [`TEMPLATE.md`](./TEMPLATE.md), assign the next number, and fill
it in. Commit it in the same PR as the change it documents.

## Index

| Number | Title | Status |
|--------|-------|--------|
| [0001](./0001-dual-track-architecture.md) | Dual-track architecture (I3C-EX and I4C) | Accepted |
| [0002](./0002-framing-comparative-prototyping.md) | Comparative prototyping of framing strategies | Accepted |
| [0003](./0003-simulation-hybrid-stack.md) | Hybrid simulation stack | Accepted |
| [0004](./0004-hatch-over-poetry.md) | Hatch over Poetry for packaging | Accepted |
| [0005](./0005-preamble-wire-format.md) | Preamble wire format (Option A) with forward-compatibility to bitmap and table forms | Accepted |
| [0006](./0006-tlv-length-encoding.md) | TLV length encoding — fixed 1-byte with documented extension paths | Accepted |
| [0007](./0007-tlv-nesting-deferred.md) | TLV nesting deferred, Type 0xFE reserved for future container semantics | Accepted |
| [0008](./0008-tlv-max-block-size.md) | TLV maximum block size — negotiated with 4096-byte default | Accepted |
| [0009](./0009-efficiency-principle.md) | Efficiency Principle — every feature must offset its cost | Accepted |
