# Dashboard Quick Input State

## Scope

- Changed the dashboard quick input memo field so `메모 (선택사항)` appears only as the textarea placeholder.
- Added a scoped gray disabled style for the dashboard `저장` button before save prerequisites are met.
- Added a selected-slot next-step prompt: `시간을 선택했어요. 원하는 태그를 선택하세요.`

## Changed Files

- `apps/dashboard/templates/dashboard/index.html`
- `apps/core/static/core/css/style.css`
- `apps/dashboard/static/dashboard/js/dashboard.js`
- `apps/dashboard/tests.py`

## Verification

- `conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short` -> `20 passed in 8.93s`
- `node --check apps/dashboard/static/dashboard/js/dashboard.js` -> exit 0
- `git diff --check` -> exit 0

## Remaining Risk

- Manual browser inspection of the exact disabled color state is not yet verified.

## Deferred Refactoring Note

- Topic: Broader dashboard quick input visual consistency
- Why it is not part of the current scope: The approved scope only covers disabled save button color and memo placeholder text.
- Why it may be needed later: The quick input sidebar and mobile bottom sheet may benefit from a full form-state pass if more controls are added.
- Trigger condition: More dashboard input controls or validation states are introduced.
- Expected change location: `apps/dashboard/templates/dashboard/index.html`, `apps/core/static/core/css/style.css`, `apps/dashboard/static/dashboard/js/dashboard.js`
- Related tests: `apps/dashboard/tests.py`
