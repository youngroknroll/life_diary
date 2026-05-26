# Merge Description Generator

- Date: 2026-05-25
- Scope: Local merge description helper
- Plan: `docs/plans/2026-05-25-merge-description-generator.md`

## What Changed

- Added `scripts/merge_description.py`.
- Added `scripts/test_merge_description.py`.
- The script reads a commit message, extracts Korean body bullets, detects related plan/refactoring docs from changed files, and prints a compact markdown description.
- The output format is:
  - `변경 요약`
  - `검증`
  - `문서`

## Usage

```bash
python scripts/merge_description.py --commit HEAD
```

Override verification commands:

```bash
python scripts/merge_description.py --commit HEAD \
  --verify "pytest apps/users/tests.py lifeDiary/test_prod_settings.py --tb=short" \
  --verify "python manage.py check" \
  --verify "git diff --check"
```

## Design Reason

The previous merge description style copied long commit histories into the description. That made descriptions hard to scan and expensive to maintain. The new helper keeps the merge text short and points readers to the plan/refactoring documents for detail.

The script is local and opt-in. GitHub workflow integration is intentionally deferred until the desired description format is stable.

## Verification Evidence

Fresh verification run on 2026-05-25:

```bash
pytest scripts/test_merge_description.py --tb=short
# RED before implementation: ModuleNotFoundError: No module named 'scripts.merge_description'
```

```bash
pytest scripts/test_merge_description.py --tb=short
# 3 passed in 0.03s
```

```bash
python scripts/merge_description.py --commit HEAD
# Printed compact sections: 변경 요약, 검증, 문서
```

## Not Verified

- GitHub PR or merge automation was not wired to this script.
- The script was not run against a multi-commit range; current implementation summarizes one commit ref.

## Deferred Refactoring Note

- Topic: GitHub workflow integration
- Why it is not part of the current scope: The approved scope was local script generation only.
- Why it may be needed later: The merge description can be automatically inserted into PR bodies once the format is stable.
- Trigger condition: Repeated manual copy/paste of generated descriptions into GitHub PR or merge bodies.
- Expected change location: repository root `.github/workflows/` or an existing deploy/PR helper.
- Related tests: script tests plus workflow dry-run or YAML validation.
