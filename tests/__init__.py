"""Top-level test package for i3cex.

Test organisation follows the layering established in the project
GOVERNANCE document:

- ``unit/``:         Pure-function tests, no I/O, millisecond-scale.
- ``property/``:     Hypothesis-based generative tests for parsers/framers.
- ``integration/``:  Multi-component tests using the pure-Python simulator.
- ``cosim/``:        cocotb tests against chipsalliance/i3c-core RTL.
                     Linux/WSL2 only. Excluded from default pytest runs.
- ``vectors/``:      Normative test vectors derived from the specification.

Pytest markers corresponding to each layer are declared in
``pyproject.toml``. Use ``pytest -m unit`` etc. to run a specific layer.
"""
