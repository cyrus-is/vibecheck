"""Scrutineer — agentic code review toolkit installer.

This package wires the four Scrutineer tools into a single setup step. The
deterministic work (copying the two static skills with the right names and
running the two generators) lives in :mod:`scrutineer.installer`, and is shared
by both front doors:

* the ``scrutineer install`` CLI (also reachable after ``pip install scrutineer``)
* the ``/scrutineer-setup`` skill, which Claude runs inside Claude Code

The only step the shared core cannot do by itself is the agentic ``servicemap``
crawl. See :mod:`scrutineer.servicemap` for how each front door supplies one.
"""

from .installer import InstallResult, install

__all__ = ["install", "InstallResult"]
__version__ = "1.5.0"
