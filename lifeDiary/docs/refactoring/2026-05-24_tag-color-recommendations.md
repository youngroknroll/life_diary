# Tag Color Recommendations

- Date: 2026-05-24
- Scope: Tag create/edit modal recommended color row
- Plan: `docs/plans/2026-05-24-tag-color-recommendations.md`

## What Changed

- Added a compact `추천색상:` row under the existing tag color picker.
- Added 14 recommended swatches: red, orange, yellow, green, blue, navy, and purple, two options each.
- Kept the existing color picker and HEX text input.
- Added delegated swatch click handling so selecting a swatch updates both existing color inputs.
- Added focused template and JavaScript contract tests.

## Recommended Colors

- Red: `#e85d5d`, `#c94a4a`
- Orange: `#e48f4f`, `#c9783f`
- Yellow: `#f0c24b`, `#d4a93a`
- Green: `#4f9f68`, `#3f8757`
- Blue: `#5a9fd6`, `#477fb3`
- Navy: `#5d6fc2`, `#4858a3`
- Purple: `#9b6ccf`, `#7d55ad`

## Code Design Reason

The row is intentionally simple: one label plus swatch buttons. It avoids a separate palette picker or grouped UI because the requirement is quick visual selection while preserving manual color control.

The JavaScript updates the existing `#tagFormColor` and `#tagFormColorText` inputs instead of introducing another state field. This keeps create/update API behavior unchanged because save still reads the existing color picker value.

## Verification Evidence

Fresh verification run on 2026-05-24:

```bash
pytest apps/tags/tests.py::TestTagModalTemplate::test_tag_modal_has_one_line_recommended_color_swatches apps/tags/tests.py::TestTagModalTemplate::test_tag_modal_swatch_js_syncs_existing_color_inputs --tb=short
# RED before implementation: 2 failed
```

```bash
pytest apps/tags/tests.py::TestTagModalTemplate::test_tag_modal_has_one_line_recommended_color_swatches apps/tags/tests.py::TestTagModalTemplate::test_tag_modal_swatch_js_syncs_existing_color_inputs --tb=short
# 2 passed in 0.07s
```

```bash
pytest apps/tags/tests.py apps/dashboard/tests.py --tb=short
# 55 passed in 19.79s
```

```bash
node --check apps/core/static/core/js/tag.js
# exit 0
```

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
# exit 0
```

```bash
git diff --check
# exit 0
```

## Not Verified

- Manual browser inspection of the modal row on mobile and desktop was not performed in this session.

## Deferred Refactoring Note

- Topic: Palette source centralization
- Why it is not part of the current scope: The current requirement is a fixed one-line recommended color list.
- Why it may be needed later: If colors are reused in multiple frontend surfaces, duplication could drift.
- Trigger condition: The recommended palette appears in two or more templates or needs user/category-specific behavior.
- Expected change location: shared Django context, a static JSON palette, or `apps/core/static/core/js/`.
- Related tests: palette rendering tests and JS color selection tests.
