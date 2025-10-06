"""
Backward-compatible re-export for the main autofill module.

Historically the project exposed automation helpers from a top-level
`autofill.py`.  The implementation now lives in `Autofill/autofill.py`,
so this file simply re-exports every public symbol to avoid breaking
existing imports.
"""

from Autofill.autofill import *  # noqa: F401,F403
