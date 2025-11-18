# SynQc Temporal Dynamics – Live Timeline Overview

This directory contains high-level documentation for the live SynQc
timeline implementation. The initial code focuses on:

- Building a simple pulse-and-probe schedule
- Running that schedule through a simulated backend that produces I/Q
- Demodulating into amplitude/phase
- Performing a basic adaptive loop toward a target probe amplitude

The intent is to mirror the structure outlined in the HTML design docs
with a minimal but functioning Python implementation that can be
extended toward real hardware backends.
