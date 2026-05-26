# Merge Description Generator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate a short merge description locally from recent commit messages.

**Architecture:** Add a stdlib-only Python script under `scripts/` that reads commit messages with `git log`, extracts Korean body bullets from the selected commit range, and prints a compact markdown description with `변경 요약`, `검증`, and `문서` sections. Keep it local and opt-in; do not wire GitHub automation yet.

**Tech Stack:** Python stdlib, pytest, Git CLI.

---

### Task 1: Script Unit Behavior

**Files:**
- Create: `scripts/merge_description.py`
- Create: `scripts/test_merge_description.py`

**Steps:**
1. Write failing tests for extracting bullet items and rendering the compact markdown format.
2. Implement pure functions first: `extract_bullets`, `extract_doc_paths`, `render_description`.
3. Add CLI wrapper that reads `git log --format=%B`.
4. Verify with `pytest scripts/test_merge_description.py --tb=short`.

### Task 2: Documentation

**Files:**
- Create: `docs/refactoring/2026-05-25_merge-description-generator.md`
- Modify: `docs/project-status.md`

**Verification commands:**

```bash
pytest scripts/test_merge_description.py --tb=short
python scripts/merge_description.py --commit HEAD
git diff --check
```
