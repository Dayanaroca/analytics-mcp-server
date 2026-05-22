"""
sql_limit_enforcer
~~~~~~~~~~~~~~~~~~

A lightweight, zero-dependency library for enforcing an upper LIMIT on
MySQL-compatible SELECT queries.
"""

from .enforcer import enforce_limit

__all__ = ["enforce_limit"]
