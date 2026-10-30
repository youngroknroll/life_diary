---
paths:
  - "**/*.py"
---

# Python Style

This file is the Python Style section of `AGENTS.md`, loaded by itself
whenever a Python module is read or edited. It carries that guide's
authority; if the two ever disagree, `AGENTS.md` wins. Comment policy stays in
`AGENTS.md` Comments; test authoring stays in `backend-tests.md`.

The Google Python Style Guide
(https://google.github.io/styleguide/pyguide.html) is the base. Where this
file is silent, follow the guide. Where this file differs, this file wins.

## Enforced By ruff

`ruff.toml` enforces what a linter can check, and CI runs `ruff check`, so a
violation blocks the PR. Run it before claiming a change is done:

```bash
conda run -n knou-life-diary ruff check .
```

| Family | Covers |
|---|---|
| `E4`, `E7`, `E9`, `F` | syntax, undefined names, unused imports and variables |
| `E501` | line length 100 |
| `W` | trailing whitespace, blank lines at end of file |
| `I` | import grouping and order |
| `N` | pep8 naming |
| `UP` | syntax available on Python 3.13 (`str \| None`, f-strings, no `typing.List`) |
| `B` | bug-prone patterns (mutable defaults, closure capture, bare `except`) |
| `SIM` | simplification (ternary, `contextlib.suppress`, merged `with`) |
| `D` | docstring presence (`D1`) and form (google convention) |

`ruff --fix` is allowed for `I`, `W`, `UP`, and `D` formatting fixes. Read the
diff: it has already mangled a banner module docstring and re-sorted files
that were out of scope.

## Project Exceptions To The Guide

- Line length is 100, not 80. There is no `ruff format` step; keep the
  surrounding file's wrapping style.
- `from module import Name` stays, as is idiomatic in Django. The guide's
  "import packages and modules only" rule is not enforced.
- Type annotations are not required. Keep the ones that exist; add them when
  they make a signature clearer, not to satisfy a quota.
- `.claude/hooks/*.py` are exempt from `E401`, `E741`, `E501`, `I`, `UP`, and
  `D` so the guards are not edited for style.
- `lifeDiary/__init__.py` is exempt from `N999`; the package name is the
  project name.
- `lifeDiary/settings/*.py` may use `from .base import *` (`F403`, `F405`).

## Imports

- Absolute imports only (`from apps.tags.models import Tag`), never relative,
  except the settings `from .base import *`.
- Three groups separated by one blank line: standard library, third party
  (`django`, `ninja`, `pytest`), then first party (`apps`, `lifeDiary`,
  `desktop`). `I` sorts within a group; keep imports at module top unless a
  function-local import breaks a cycle or defers a heavy desktop dependency.
- No wildcard imports outside settings.

## Naming

- Modules and packages `snake_case`, classes `CapWords`, functions, methods,
  and variables `snake_case`, module constants `UPPER_SNAKE`.
- Exception classes end in `Error` (`ResendBlockedError`, not
  `ResendBlocked`).
- A leading underscore marks module-private helpers (`_daily_target_minutes`);
  do not export them from another module.
- Never `l`, `O`, or `I` as a name. A local that holds a class is lowercase
  (`user_model = get_user_model()`, not `User = ...`).
- Test names follow `backend-tests.md` (behavior-centered).

## Docstrings

Public API is the `use_cases`, `domain_services`, `services`, `api`, and
`views` modules. Their public modules, classes, functions, and methods must
have a docstring (`D1`). Every other module is listed in `ruff.toml`
per-file-ignores under `D1`; when a new module is public API, do not add it
there.

Form, in any module that carries a docstring:

- One-line summary on the first line, ending with a period, written as a
  statement of what the object does or returns. Korean is fine; the codebase
  is Korean.
- A blank line, then the body, only when the summary is not enough.
- `Args:`, `Returns:`, `Raises:` sections only for what the name and type
  hints cannot show: a non-obvious unit, an exception the caller must handle,
  a return shape. Do not list every parameter.
- No banner lines (`====`), no restating the function name.

```python
def on_http_error(request, exc):
    """JSON 파싱 실패는 400 INVALID_JSON, 그 밖의 HTTP 오류는 원래 상태와 detail로 응답한다."""


def goal_hit_dates(user, start, end, goal, calculator=None) -> set:
    """기간 안에서 목표 시간을 채운 날들.

    주간·월간 목표도 하루치로 환산해 센다. 달성일은 "그날 목표만큼 했나"를
    묻는 지표라 기간 총합으로는 답할 수 없다.
    """
```

## Code Shape

- Re-raise with context: `raise HttpError(...) from exc`, or `from None` when
  the cause is deliberately hidden (`B904`).
- Catch the narrowest exception that the test or caller needs; `except
  Exception` and `pytest.raises(Exception)` are not accepted.
- Mutable default arguments are not allowed; use `None` and build inside.
- A closure defined inside a loop binds loop variables through default
  arguments (`process_block(block, _date=date_item)`), not through late
  lookup.
- Prefer `contextlib.suppress(OSError)` over `try: ... except OSError: pass`,
  a ternary over a four-line `if/else` assignment, and one `with (a, b):`
  over nested `with` blocks, as `SIM` reports.
- Wrap long lines with parentheses, not backslashes. Long string messages
  split into adjacent literals inside parentheses.

## When ruff Reports Something You Disagree With

Do not add `# noqa` or a per-file ignore to make a report disappear. Either
fix the code, or bring the case to the user with the rule id and the reason it
is a false positive. The two exemptions above (hooks, package name) are the
only ones a task may rely on without asking.
