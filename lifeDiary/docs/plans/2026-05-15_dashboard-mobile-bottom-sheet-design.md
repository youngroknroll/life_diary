# Dashboard Mobile Bottom Sheet Design

## Goal

Improve the mobile dashboard flow so users can select time slots and assign tags without scrolling from the grid down to the sidebar.

## Context

The dashboard already has mobile grid work for touch scrolling and a desktop quick input sidebar. The remaining mobile problem is the selection-to-tag path: after selecting slots, tag controls live below the grid on narrow screens.

## Design

Use a mobile-only bottom sheet for quick tag assignment.

- Desktop and tablet-large layouts keep the existing `#quickInputSidebar`.
- Mobile (`max-width: 767.98px`) uses a fixed bottom sheet tied to the existing sidebar markup.
- Selecting a slot opens the sheet.
- The sheet shows selected slot info, tag controls, memo, and save action.
- Closing the sheet returns focus to the selected grid area where practical.

## Interaction Rules

- Vertical touch movement should remain page scroll.
- Intentional grid selection still updates selected slots.
- Tag buttons and primary actions must meet a practical 44px touch target.
- The sheet must have a close button, an overlay, `aria-hidden`, and an accessible label.
- Desktop behavior must not change.

## Deferred Work

- Redesigning the whole 144-slot grid.
- Reworking tag management and category explanation modals.
- Adding advanced mobile gestures such as long-press or pinch.
- Live browser/device testing beyond local checks.
