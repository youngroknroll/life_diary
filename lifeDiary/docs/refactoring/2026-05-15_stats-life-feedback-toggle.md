# Stats Life Feedback Toggle Refactoring Log

Date: 2026-05-15

## Scope

Changed the stats page life feedback section from always-visible toast cards to a default-closed Bootstrap collapse section.

## Changed Files

- `apps/stats/templates/stats/life_feedback.html`
- `apps/core/static/core/css/style.css`
- `apps/stats/test_mobile_layout.py`
- `docs/plans/2026-05-15_stats-life-feedback-toggle-design.md`
- `docs/plans/2026-05-15_stats-life-feedback-toggle.md`
- `docs/project-status.md`

## Behavior

- When feedback exists, the stats page now renders a compact life feedback toggle.
- The feedback body starts closed with `class="collapse"`.
- The toggle exposes Bootstrap collapse attributes and accessible `aria-controls` / `aria-expanded` state.
- The expanded feedback list is arranged horizontally and wraps onto the next row when it exceeds the container width.
- Feedback messages remain in the existing order and are still rendered through `render_message`.
- Empty feedback still renders no feedback section.

## Verification

Fresh verification run during implementation:

- `conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestLifeFeedbackToggleStructure::test_life_feedback_list_collapsed_by_default --tb=short` first failed because the current partial had no toggle panel.
- `conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestLifeFeedbackToggleStructure::test_life_feedback_toggle_has_compact_responsive_styles --tb=short` first failed because the stylesheet had no toggle rules.
- After the wrapping-row refinement, the same focused style test first failed because `.life-feedback-list` still used `flex-wrap: nowrap`.
- `conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestLifeFeedbackToggleStructure --tb=short` passed with `2 passed in 1.58s`.
- `conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py apps/stats/tests.py apps/stats/test_i18n_phase5.py --tb=short` passed with `22 passed in 8.44s`.
- `node --check apps/stats/static/stats/js/stats.js` exited `0`.
- `git diff --check` exited `0`.
- `conda run -n knou-life-diary pytest --tb=short` passed with `176 passed in 78.74s (0:01:18)`.

## Unverified

- Manual browser interaction on mobile remains unverified unless performed separately.
- Bootstrap collapse runtime behavior is covered by markup contract tests, not by an in-browser test.

## Deferred Refactoring Note

- Topic: Feedback prioritization and partial reveal.
- Why it is not part of the current scope: The approved request was to make the list toggleable, not to alter feedback generation, sorting, or display limits.
- Why it may be needed later: If feedback count grows, warnings may need priority ordering or a summary view.
- Trigger condition: Users report too many feedback entries even after the section is collapsed by default.
- Expected change location: `apps/stats/life_feedback.py`, `apps/stats/views.py`, and `apps/stats/templates/stats/life_feedback.html`.
- Related tests: Stats feedback generation tests and `apps/stats/test_mobile_layout.py`.
