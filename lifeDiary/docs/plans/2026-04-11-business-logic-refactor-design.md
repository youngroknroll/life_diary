# Business Logic Refactor Design

## Goal

Reduce coupling in the Python business-logic layer by extracting repeated constants, repeated data-shape builders, and repeated branching logic without touching templates or frontend assets.

## Scope

Allowed:
- `apps/stats/*.py`
- `apps/dashboard/*.py`
- `apps/users/*.py`
- `apps/tags/*.py`
- shared Python utility modules if needed

Forbidden:
- Django templates
- CSS
- JavaScript
- static assets

## Problems Found

1. `apps/stats/logic.py`
   - Repeats unclassified-tag dictionary shapes for daily, weekly, monthly, and analysis modes.
   - Repeats hour and day conversions inline.
   - Contains several hardcoded values and period-specific list sizes.

2. `apps/dashboard/views.py`
   - Embeds slot-header construction and API validation/error literals directly in the view.
   - View is responsible for both HTTP flow and domain validation details.

3. `apps/users/domain_services.py`
   - Repeats period-specific data lookup logic.
   - Couples progress calculation to the current stats payload layout in a repetitive way.

4. `apps/tags/domain_services.py`
   - `can_edit` and `can_delete` share the same authorization rule but duplicate the implementation.

## Design

1. Extract repeated stats shapes into helper builders
   - Add a Python helper module for stats data builders and small aggregations.
   - Keep the existing public `get_*_stats_data()` and `get_stats_context()` functions unchanged.

2. Extract dashboard business constants and validation helpers
   - Move slot-header generation and slot-index validation into a dedicated Python helper/service.
   - Keep the view responsible for request/response wiring only.

3. Normalize goal progress lookup
   - Replace repeated `if goal.period == ...` loops with a period-to-extractor mapping inside the domain service.

4. Collapse repeated tag-management policy
   - Introduce one internal policy helper and delegate `can_edit` / `can_delete` to it.

## Testing

- Add focused unit tests for:
  - stats helper builders and aggregates
  - dashboard slot-header generation and slot-index validation
  - goal progress calculation by period
  - tag policy behavior

- Keep tests independent from templates and frontend rendering.
