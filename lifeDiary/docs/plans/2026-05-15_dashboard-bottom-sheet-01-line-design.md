# Dashboard Bottom Sheet 01:00 Line Design

## Goal

Limit the mobile dashboard quick input bottom sheet so its top edge rises only to the dashboard grid's 01:00 line.

## Approved Scope

- Mobile-only behavior.
- Use the existing dashboard time slot with `data-slot-index="6"` as the 01:00 reference line.
- Keep desktop sidebar behavior unchanged.
- Keep the existing sheet content and controls unchanged.

## Design

When the sheet opens on mobile, JavaScript measures the 01:00 slot's viewport position and calculates available space from that line to the bottom of the viewport. It writes that value to a CSS custom property on the sheet. CSS uses the property as the mobile sheet `max-height`, with a fallback for cases where the slot is unavailable.

If the 01:00 line cannot be measured, the current `82vh` cap remains the fallback.

## Deferred Work

- Drag handles or resizable bottom sheet behavior.
- Reworking the 144-slot grid layout.
- Browser-device visual tuning beyond the 01:00 line constraint.
