# Bug and Risk Audit

This report captures issues found before adding new features.

## 1) Hard-coded Windows paths break JSON persistence on non-Windows hosts
- Status: fixed in `fix/main-working-order`.
- `TEXT_TRACKER` and `VOICE_TRACKER` are relative paths (`Path("TextTracker.json")`, `Path("VoiceTracker.json")`) in `PriorTracker.py`.

## 2) Backfill helper has a mismatched function call signature
- Status: fixed in `fix/main-working-order`.
- Deprecated duplicate helper module removed; canonical backfill path is `PriorTracker.backfill_text_log`.

## 3) Voice data schema mismatch between modules
- Status: fixed in `fix/main-working-order`.
- Duplicate schema writer removed with `Backfill.py`; active tracking/backfill uses one schema in `PriorTracker.py`.

## 4) "Admin-only" backfill command is not permission-gated
- Status: fixed in `fix/main-working-order`.
- `backfill_text_log` now uses `@commands.has_permissions(administrator=True)` and has a missing-permissions error handler.

## 5) Backfill metric is misleading
- Status: fixed in `fix/main-working-order`.
- `log_text_activity` returns whether a new record was persisted and `total_logged` increments only on new entries.

## 6) `funny.py` has a likely import/runtime failure
- `import fight_back` appears to expect a local module that is not in this repository.
- Impact: running `funny.py` likely raises `ModuleNotFoundError`.
- Status: not addressed in this PR (out of scope).

## Quick checks run
- `python -m py_compile SanctumMain.py PriorTracker.py` (should pass in this branch).
