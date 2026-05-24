# Shared Tag Category Header Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Use one shared category header template so dashboard tag lists and the tag management page display category names with `-` instead of color icon boxes.

**Architecture:** Add a small shared Django partial under `templates/shared/` that renders the category header structure and exposes stable data hooks for JavaScript. Server-rendered dashboard HTML includes the partial directly; JavaScript-rendered dashboard and tag-management lists include the same partial in a `<template>` and clone it at runtime.

**Tech Stack:** Django templates, browser JavaScript, pytest static/template contract tests.

---

### Task 1: Shared Template Contract

**Files:**
- Create: `templates/shared/_tag_category_header.html`
- Modify: `apps/dashboard/templates/dashboard/index.html`
- Modify: `apps/tags/templates/tags/index.html`
- Test: `apps/dashboard/tests.py`
- Test: `apps/tags/tests.py`

**Step 1: Write the failing tests**

Add tests that assert:
- dashboard server-rendered category headers include `templates/shared/_tag_category_header.html` behavior and still show `- 수동적 소비시간`;
- dashboard template contains a `tagCategoryHeaderTemplate` `<template>`;
- tag management template contains the same shared template and no category header color-box markup.

**Step 2: Run tests to verify RED**

Run:

```bash
pytest apps/dashboard/tests.py::TestDashboardIndexRendering::test_sidebar_category_headers_use_separator_not_color_dot apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_dashboard_dynamic_category_header_uses_shared_template apps/tags/tests.py::TestTagModalTemplate::test_tag_management_category_header_uses_shared_template --tb=short
```

Expected: FAIL because the shared partial and JS template do not exist yet, and tag management still renders `<span class="badge me-2" style="background-color: ${cat.color};">&nbsp;</span>`.

**Step 3: Write minimal implementation**

Create `templates/shared/_tag_category_header.html` with:

```django
<div class="{{ category_header_class|default:'tag-category-header small text-muted fw-bold mt-2 mb-1' }}" data-tag-category-header>
    - <span data-tag-category-name>{{ category_name }}</span>{% if category_count %}<small class="text-muted ms-1" data-tag-category-count>({{ category_count }})</small>{% endif %}
</div>
```

Update dashboard server template to include it for each category and add a hidden `<template id="tagCategoryHeaderTemplate">`.

Update dashboard JS and tag-management JS to clone the template, fill `data-tag-category-name`, optionally fill count, and never render category color-box markup.

**Step 4: Run tests to verify GREEN**

Run the same focused command and then:

```bash
pytest apps/dashboard/tests.py apps/tags/tests.py --tb=short
node --check apps/dashboard/static/dashboard/js/dashboard.js
git diff --check
```

Expected: all commands pass.

### Task 2: Documentation

**Files:**
- Create: `docs/refactoring/2026-05-24_shared-tag-category-header.md`
- Modify: `docs/project-status.md`

**Step 1: Document changes**

Record design reason, inserted code locations, verification evidence, and deferred work.

**Step 2: Run final verification**

Run:

```bash
pytest apps/dashboard/tests.py apps/tags/tests.py --tb=short
node --check apps/dashboard/static/dashboard/js/dashboard.js
git diff --check
```

Expected: all commands pass.
