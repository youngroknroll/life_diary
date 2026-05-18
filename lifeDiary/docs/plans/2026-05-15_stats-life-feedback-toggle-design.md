# Stats Life Feedback Toggle Design

Date: 2026-05-15

## Approved Scope

Change the stats page life feedback list from always-visible toast cards to a toggleable section.

The default state is closed. The user sees a compact "Life feedback N" header/button and opens the list only when needed.

## Non-Scope

- Do not change feedback generation rules.
- Do not sort, limit, or slice feedback items in the view.
- Do not change stats tabs, charts, or goal cards.
- Do not introduce new JavaScript beyond Bootstrap collapse behavior.

## UX Design

Use the existing Bootstrap collapse pattern already used by the goal cards.

The collapsed header should:

- show the life feedback label;
- show the number of feedback items;
- expose `aria-expanded="false"` and `aria-controls`;
- use a chevron affordance consistent with existing goal cards.

The expanded body should render the existing feedback cards in the current order. The cards are arranged horizontally and wrap onto the next row when they exceed the available width. Empty feedback still renders nothing, matching the current behavior.

## Accessibility

The toggle is a real `<button>`, not a link or custom clickable container. Bootstrap collapse updates the expanded state during interaction. The collapsed region has a stable id connected by `aria-controls`.

## Risks

Native Bootstrap collapse behavior is not covered by server-rendered Django tests. The regression tests should verify the HTML contract that Bootstrap needs: toggle button, target id, closed collapse body, and feedback count.

## Acceptance Criteria

- When `feedback_list` exists, the stats page renders a closed feedback toggle section.
- The toggle button targets the feedback list collapse body.
- The button displays the number of feedback messages.
- Existing feedback card content and dismiss buttons remain present inside the collapsible body.
- The expanded feedback list uses a horizontal wrapping row without a horizontal slide area.
- No feedback list markup is rendered when `feedback_list` is empty.
