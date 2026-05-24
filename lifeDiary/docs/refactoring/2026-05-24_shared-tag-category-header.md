# Shared Tag Category Header

- Date: 2026-05-24
- Scope: Dashboard and tag-management category header display
- Plan: `docs/plans/2026-05-24-shared-tag-category-header.md`

## What Changed

- Added `templates/shared/_tag_category_header.html` as the shared category header partial.
- Updated the dashboard quick-input tag list to include the shared partial for server-rendered category headers.
- Added `tagCategoryHeaderTemplate` to the dashboard and tag-management templates so JavaScript-rendered category groups can clone the same shared markup.
- Updated dashboard dynamic tag rendering to call `renderCategoryHeader(cat.name)`.
- Updated tag-management dynamic rendering to call `renderCategoryHeader(cat.name, catTags.length)`.
- Removed category color icon boxes from dynamic category headers while keeping tag color badges/buttons intact.

## Code Design Reason

The visible rule is now centralized: category headers render as `- 카테고리명` instead of showing a color icon box. This keeps the mobile dashboard list, desktop/server-rendered dashboard list, and tag-management category groups visually consistent.

Django templates cannot be directly included inside static JavaScript files at runtime, so the shared partial is exposed to JavaScript through a DOM `<template>`. Each JS renderer clones the template and fills stable data hooks:

- `data-tag-category-name`
- `data-tag-category-count`

This avoids duplicating category header HTML strings while keeping the API/model/tag color behavior unchanged.

## Code Insertion Summary

- `templates/shared/_tag_category_header.html`
  - Shared partial with `data-tag-category-header`, `data-tag-category-name`, and optional `data-tag-category-count`.
- `apps/dashboard/templates/dashboard/index.html`
  - Replaced inline server-rendered category header HTML with the shared include.
  - Added `<template id="tagCategoryHeaderTemplate">` containing the shared include.
- `apps/dashboard/static/dashboard/js/dashboard.js`
  - Added `renderCategoryHeader()`.
  - Replaced dynamic category color box markup with the shared-template renderer.
- `apps/tags/templates/tags/index.html`
  - Added `<template id="tagCategoryHeaderTemplate">` containing the shared include.
  - Added `renderCategoryHeader()`.
  - Replaced tag-management category color box markup with the shared-template renderer.

## Verification Evidence

Fresh verification run on 2026-05-24:

```bash
pytest apps/dashboard/tests.py::TestDashboardIndexRendering::test_sidebar_category_headers_use_separator_not_color_dot apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_dashboard_dynamic_category_header_uses_shared_template apps/tags/tests.py::TestTagModalTemplate::test_tag_management_category_header_uses_shared_template --tb=short
# RED before implementation: 2 failed, 1 passed
```

```bash
pytest apps/dashboard/tests.py::TestDashboardIndexRendering::test_sidebar_category_headers_use_separator_not_color_dot apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_dashboard_dynamic_category_header_uses_shared_template apps/tags/tests.py::TestTagModalTemplate::test_tag_management_category_header_uses_shared_template --tb=short
# 3 passed in 1.87s
```

```bash
pytest apps/dashboard/tests.py apps/tags/tests.py --tb=short
# 53 passed in 20.81s
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

- Manual mobile browser rendering was not checked in this session.
- Tag-management browser interaction after editing/creating tags was not manually checked in this session.

## Deferred Refactoring Note

- Topic: Shared frontend helper for cloning Django-backed templates
- Why it is not part of the current scope: Only category header rendering needed consolidation.
- Why it may be needed later: More JS-rendered fragments may need to share Django template markup without duplicating HTML strings.
- Trigger condition: Three or more shared JS-rendered fragments require the same clone/fill pattern.
- Expected change location: `apps/core/static/core/js/` or a small shared template utility.
- Related tests: static JS contract tests and focused page rendering tests.
