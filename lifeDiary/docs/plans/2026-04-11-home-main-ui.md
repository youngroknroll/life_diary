# Home Main UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the Django home page so the main value is "단순하게 하루를 기록한다" and the primary path leads users to record today.

**Architecture:** Keep the existing Django view and `features` context. Replace the home template markup with page-scoped sections and add scoped CSS in the template's `extra_css` block so the change does not disturb dashboard, stats, or tag pages.

**Tech Stack:** Django templates, Bootstrap 5, Font Awesome, existing `base.html`, existing `core/css/style.css`.

---

### Task 1: Update Home Template Structure

**Files:**
- Modify: `templates/index.html`

**Step 1: Inspect the current template**

Run: `sed -n '1,260p' templates/index.html`

Expected: The current page contains a Bootstrap `jumbotron`, feature cards from `features`, a four-step "사용 방법" section, and an authenticated status banner.

**Step 2: Replace the content block**

Update `templates/index.html` to keep `{% extends 'base.html' %}`, the title block, and Django auth branching. Replace the old content with:

- A hero section with headline "하루를 단순하게 기록하세요"
- A primary CTA that links authenticated users to `{% url 'dashboard:index' %}` with text "오늘 기록하기"
- A primary CTA that links anonymous users to `{% url 'users:login' %}` with text "로그인하고 기록 시작"
- A secondary anonymous CTA to `{% url 'users:signup' %}`
- A superuser admin CTA to `{% url 'admin:index' %}`
- A static preview panel showing simple activity blocks and a note
- Three feature cards with user-facing wording
- An authenticated nudge linking to the dashboard

**Step 3: Keep behavior unchanged**

Verify all existing URL names remain unchanged:

```django
{% url 'dashboard:index' %}
{% url 'users:login' %}
{% url 'users:signup' %}
{% url 'admin:index' %}
```

### Task 2: Add Page-Scoped Styling

**Files:**
- Modify: `templates/index.html`

**Step 1: Add `extra_css` block**

Add scoped CSS inside `{% block extra_css %}` in `templates/index.html`.

**Step 2: Style only home-specific classes**

Use class names prefixed with `home-`, such as:

```css
.home-hero { ... }
.home-preview { ... }
.home-day-block { ... }
.home-feature { ... }
```

Do not change broad selectors such as `body`, `.card`, `.btn-primary`, or `.navbar`.

**Step 3: Responsive checks**

Ensure the hero stacks cleanly below 992px and buttons wrap without text overflow.

### Task 3: Verify Rendering

**Files:**
- Read: `templates/index.html`

**Step 1: Run Django checks**

Run: `python manage.py check`

Expected: `System check identified no issues`.

**Step 2: Optional browser check if the dev server is available**

Run: `python manage.py runserver 127.0.0.1:8000`

Open `/` and verify:

- The headline says "하루를 단순하게 기록하세요"
- Anonymous CTA text is "로그인하고 기록 시작"
- The preview panel does not claim to show live data
- Mobile width does not overflow horizontally

**Step 3: Review diff**

Run: `git diff -- templates/index.html docs/plans/2026-04-11-home-main-ui-design.md docs/plans/2026-04-11-home-main-ui.md`

Expected: The diff only covers the new design/plan docs and home template changes.
