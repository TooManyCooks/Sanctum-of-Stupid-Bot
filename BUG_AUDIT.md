# Bug and Risk Audit

This report captures issues found before adding new features.

## 1) Hard-coded Windows paths break JSON persistence on non-Windows hosts
- `TEXT_TRACKER` and `VOICE_TRACKER` are set to absolute Windows paths.
- On Linux/CI/dev containers, those parents do not exist, so the first write in `load_json` (`path.write_text`) raises `FileNotFoundError`.
- Impact: bot can fail during startup before connecting.

## 2) Backfill helper has a mismatched function call signature
- `Backfill.backfill_text` calls `await log_text_activity(msg, text_data)`.
- In `SanctumMain.py`, `log_text_activity` accepts only one argument (`message`).
- Impact: if this helper is used, it raises `TypeError` and backfill aborts.

## 3) Voice data schema mismatch between modules
- `SanctumMain.py` writes voice data under `{"guilds": {"<gid>": {"users": ...}}}`.
- `Backfill.backfill_voice_from_log` writes under `{"users_by_guild": {"<gid>": ...}}`.
- Impact: tools reading one schema will not see records written by the other.

## 4) "Admin-only" backfill command is not permission-gated
- The command docstring says admin-only, but no decorator/enforcement exists.
- Impact: any user with command access can trigger expensive full history scans.

## 5) Backfill metric is misleading
- `total_logged` increments for every scanned message, even if the message timestamp was already present and `log_text_activity` skipped writing.
- Impact: completion message may overstate what was actually added.

## 6) `funny.py` has a likely import/runtime failure
- `import fight_back` appears to expect a local module that is not in this repository.
- Impact: running `funny.py` likely raises `ModuleNotFoundError`.

## Quick checks run
- `python -m py_compile SanctumMain.py Backfill.py SanctumCommands.py funny.py` (passes syntax/bytecode checks).
