# ADR-0004: Hatch over Poetry for Python packaging

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: Muntaser Syed
- **Consulted**: Claude (Anthropic)
- **Informed**: Future collaborators, reviewers

## Context and Problem Statement

The `i3cex` package will be published to PyPI and must have a build
backend, environment management tool, and release workflow. The two
mainstream choices in 2026 are Poetry and Hatch. Both are capable;
they differ on philosophy, lockfile behaviour, and alignment with
Python packaging standards.

## Decision Drivers

- Alignment with Python Packaging Authority (PyPA) standards.
- Long-term maintenance trajectory.
- Compatibility with `pyproject.toml` as the single source of truth.
- Ease of CI integration.
- Lockfile ergonomics (we want reproducibility without proprietary
  formats).

## Considered Options

- Option A: Poetry.
- Option B: Hatch.
- Option C: setuptools with pip-tools.

## Decision Outcome

Chosen option: **Option B — Hatch**, because it is PyPA-aligned, uses
only standardised `pyproject.toml` fields, and has better long-term
maintenance trajectory than Poetry.

### Consequences

**Good:**

- `pyproject.toml` is the single source of truth; no proprietary
  lockfile format.
- Environment management via `hatch env` is simple and declarative.
- Build backend (`hatchling`) is PyPA-recommended for new projects.
- Version management via `hatch version` integrates cleanly with the
  `[tool.hatch.version]` path we already configured.
- CI integration is straightforward; GitHub Actions has first-class
  support.

**Bad:**

- Smaller ecosystem than Poetry today; fewer community tutorials.
- Dependency locking in Hatch is less batteries-included than
  Poetry's `poetry.lock`. For strict reproducibility we may need to
  add `pip-compile` or `uv` as a separate locking layer.

## Pros and Cons of the Options

### Option A: Poetry

- Good: Large community; extensive documentation.
- Good: Built-in dependency locking.
- Bad: Proprietary lockfile format (`poetry.lock`) predates PEP 751.
- Bad: Has historically diverged from PyPA standards (e.g., its own
  `[tool.poetry]` section instead of `[project]`).
- Bad: Release cadence has been inconsistent.

### Option B: Hatch

- Good: PyPA-aligned; uses standard `[project]` metadata.
- Good: Maintained by the PyPA itself.
- Good: Build backend (`hatchling`) is the current PyPA recommendation
  for new packages.
- Good: Declarative environment management with matrix testing
  support built in.
- Bad: Smaller ecosystem than Poetry.
- Bad: Locking story is less mature; supplementary tooling may be
  needed.

### Option C: setuptools with pip-tools

- Good: Maximum compatibility; works everywhere Python does.
- Good: Well understood; long track record.
- Bad: No environment management; must pair with `venv` or `tox`.
- Bad: More boilerplate in `pyproject.toml`.
- Bad: Less pleasant developer experience than Hatch or Poetry.

## References

- `../../../GOVERNANCE.md` — packaging decision log entry.
- [Hatch documentation](https://hatch.pypa.io/)
- [PyPA Packaging User Guide](https://packaging.python.org/)
- [PEP 621](https://peps.python.org/pep-0621/) — standard project
  metadata in `pyproject.toml`.
