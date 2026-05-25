#!/usr/bin/env python3
"""Generate a compact merge description from recent commit metadata."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


DEFAULT_VERIFICATION = [
    "pytest <관련 테스트 명령>",
    "python manage.py check",
    "git diff --check",
]


def extract_bullets(message: str) -> list[str]:
    bullets: list[str] = []
    for line in message.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        item = stripped[2:].strip()
        if not item:
            continue
        if item.lower().startswith(("pytest ", "python ", "git ", "node ")):
            continue
        bullets.append(item)
    return bullets


def extract_doc_paths(paths: list[str]) -> list[str]:
    docs = []
    for path in paths:
        if path.startswith(("docs/plans/", "docs/refactoring/")) and path.endswith(".md"):
            docs.append(path)
    return docs


def render_description(
    bullets: list[str],
    verification: list[str] | None = None,
    docs: list[str] | None = None,
) -> str:
    verification = verification or DEFAULT_VERIFICATION
    docs = docs or []

    sections = ["## 변경 요약", ""]
    sections.extend(f"- {item}" for item in bullets)
    sections.extend(["", "## 검증", ""])
    sections.extend(f"- {item}" for item in verification)
    if docs:
        sections.extend(["", "## 문서", ""])
        sections.extend(f"- {path}" for path in docs)
    return "\n".join(sections)


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def get_commit_message(rev: str) -> str:
    return run_git(["log", "-1", "--format=%B", rev])


def get_changed_files(rev: str) -> list[str]:
    output = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", rev])
    if not output:
        return []
    prefix = f"{Path.cwd().name}/"
    files = []
    for line in output.splitlines():
        files.append(line.removeprefix(prefix))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a short markdown merge description."
    )
    parser.add_argument("--commit", default="HEAD", help="Commit ref to summarize.")
    parser.add_argument(
        "--verify",
        action="append",
        dest="verification",
        help="Verification command to include. Can be passed multiple times.",
    )
    args = parser.parse_args()

    message = get_commit_message(args.commit)
    bullets = extract_bullets(message)
    docs = extract_doc_paths(get_changed_files(args.commit))
    print(render_description(bullets, args.verification, docs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
