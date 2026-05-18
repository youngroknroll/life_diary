# Header Utility Controls Design

Date: 2026-05-19

## Approved Scope

Improve the shared Life Diary header and dashboard drag polish.

1. Header utility controls
   - Replace the dark/light toggle icon expression with visible localized text.
   - Keep only the language selector and theme toggle as a fixed horizontal row immediately to the right of the `Life Diary` / `라이프 다이어리` brand.
   - Preserve the existing Bootstrap collapsed navigation behavior for nav links, login/signup, and user menu.

2. Dashboard time-grid drag polish
   - Prevent browser text selection while dragging time blocks.
   - Limit text-selection prevention to the time-grid and time-slot interaction area.

## Non-Scope

- Redesigning the full navbar or changing navigation links.
- Changing authentication, user menu, login/signup behavior, or route structure.
- Changing dashboard time-block save, delete, or selection data behavior.
- Editing generated `staticfiles/` output.
- Adding new visual themes, icons, or branding beyond the requested text toggle.

## UX Guidance

The Web UX / UI Designer reviewed the current header structure and recommended a dedicated utility group beside the brand.

Expected layout:

```text
[Life Diary] [Language] [Dark/Light]        [Menu]
```

- Desktop: brand, language selector, and theme button stay on the top row. Main navigation continues to use the existing Bootstrap navbar flow.
- Mobile/tablet: brand and the two utility controls remain together in a non-wrapping row. The menu toggler may stay at the far right and collapsed nav content remains separate.
- Tight widths should use compact labels rather than wrapping the utility controls.

Theme toggle text:

- Korean light mode action: `다크`
- Korean dark mode action: `라이트`
- English light mode action: `Dark`
- English dark mode action: `Light`

Accessibility:

- Theme button visible text describes the next available action.
- `aria-label` also describes the action.
- `aria-pressed` exposes whether dark mode is currently active.
- Language selector and theme button keep visible focus states.
- Utility controls should remain touch-friendly on mobile.

## Design Decisions

- Add a header utility wrapper in `templates/base.html` around the language form and theme button.
- Move the language selector's inline sizing into source CSS.
- Replace the theme button's `<i>` icon dependency with a text span.
- Update the inline theme script so it changes button text and accessibility attributes instead of Font Awesome classes.
- Add source CSS for the header utility row and compact controls.
- Add `user-select: none` behavior to the time-grid/time-slot area to avoid selected text during drag.

## Acceptance Criteria

- Korean header shows the brand text, language selector, and theme button as adjacent controls on the top row.
- English header renders the theme button with English visible text.
- The theme toggle no longer depends on a moon/sun icon element.
- Theme toggle click still switches the `data-theme` and `data-bs-theme` attributes.
- The language selector and theme button remain in the same utility row outside the collapsed nav content.
- Time-grid dragging no longer selects slot text.
- Existing nav links and auth menu remain in the Bootstrap collapse area.

## Risks

- Text labels are wider than the current icon-only button, so the utility group must be compact at 320px widths.
- Current theme JavaScript assumes an `<i>` inside `#themeToggle`; implementation must update that assumption.
- Inline template JavaScript is harder to syntax-check directly than standalone JS.
- CSS text-selection prevention must not block text selection in forms or general page content.

## Verification Plan

- RED/GREEN focused Django rendering tests for the header utility structure and visible theme text.
- RED/GREEN CSS source test for time-grid text-selection prevention.
- Focused regression: `conda run -n knou-life-diary pytest apps/core/tests.py apps/core/test_i18n_phase1.py apps/dashboard/tests.py --tb=short`
- Whitespace check: `git diff --check`
- Optional manual browser check at 320px, 375px, and desktop widths for header wrapping.
