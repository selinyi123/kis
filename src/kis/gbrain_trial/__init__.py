"""KIS-016 GBrain read-only trial.

Validates whether GBrain can act as a *derived index* over the Obsidian
knowledge base WITHOUT becoming a second source of truth.

HARD RULES:
  * GBrain only ever reads a filtered SAFE EXPORT snapshot — never the raw vault.
  * blocked/secret/confidential/credential/DPMS-sensitive files never export.
  * GBrain output goes ONLY into trial artifacts/report — never written back to
    Obsidian, store, lifecycle, review, or canonical.
  * Real GBrain is never a hard dependency; mock/manual paths run fully offline.
    If GBrain is unavailable the trial degrades to baseline + report.
"""

TRIAL_VERSION = "0.3.3"

__all__ = ["TRIAL_VERSION"]
