"""cocotb cosimulation tests against chipsalliance/i3c-core RTL.

This directory contains tests that run the actual I3C RTL (Apache-2.0
SystemVerilog from chipsalliance/i3c-core) under Verilator, driven by
cocotb testbenches written in Python.

These tests are **Linux/WSL2 only** and require Verilator 5.012+,
Icarus Verilog 12.0+, and Verible to be installed. They are excluded
from the default pytest run and gated behind an explicit ``make cosim``
target (to be added to the repository Makefile).

This file is intentionally empty of imports so it does not break CI on
Windows. The actual testbenches are added incrementally alongside each
sublayer implementation.
"""
