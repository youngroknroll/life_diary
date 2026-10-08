---
paths:
  - "templates/**"
  - "apps/**/templates/**"
  - "apps/**/static/**"
---

# Frontend Work Policy

This file is the Frontend Work Policy and Frontend Dual Review Gate of
`AGENTS.md`, loaded by itself whenever a template, stylesheet, or browser
JavaScript file is read or edited. It carries that guide's authority; if the
two ever disagree, `AGENTS.md` wins.

Django templates, CSS, browser JavaScript, SSR binding, and fetch wiring are
exempt from the backend TDD cycle.

- Do not create automated tests for purely presentational layout, spacing,
  sizing, visual state, transition, animation, or markup rearrangement.
- Do not assert on rendered markup strings, CSS rule text, or JavaScript source
  text. Such tests track the implementation, not the contract, and break on
  every rewrite while proving nothing. Delete them when the code they mirror is
  replaced.
- Verify frontend work with HTTP render checks, browser screenshots at agreed
  viewports, interaction click-through, console inspection, `node --check` on
  changed JS, and accessibility checks appropriate to scope.
- An automated browser regression is allowed only for a concrete measurable
  acceptance gate such as an overflow budget, minimum touch-target size,
  line-clamp height, or post-interaction focus target.
- Any backend endpoint, validation, persistence, or business rule introduced
  for frontend work still follows the Backend TDD Cycle.
- Every frontend review includes both the Web Experience Designer and Browser
  Interaction Reviewer.
- Frontend implementation requires a plan approved in chat and, on
  completion, an entry in `docs/CHANGELOG.md` that carries the browser
  evidence and both reviewer verdicts.
- Do not comment frontend code. Django templates, CSS, and browser JavaScript
  carry no comments unless the user approves a specific one. A template comment
  that leaks reaches the user as visible page text: `{# #}` is single-line only,
  so a comment wrapped across two lines renders literally in the browser.

### Frontend Dual Review Gate

Every frontend implementation requires actual output from both the Web
Experience Designer and Browser Interaction Reviewer before and after editing.
Listing a role under `Activated Roles` is routing evidence, not review
evidence.

Before implementation:

1. The integrated plan selects a review depth and explains why.
2. The Web Experience Designer provides an implementation-ready experience
   specification.
3. The Browser Interaction Reviewer provides interaction and accessibility
   criteria.
4. The Frontend Implementation Engineer must not edit until both outputs
   exist.

After implementation and the planned browser verification:

1. The Web Experience Designer reviews the implementation against the
   approved experience specification.
2. The Browser Interaction Reviewer reviews the implementation against the
   approved interaction criteria.
3. Each reviewer returns `Conforms`, `Deviates`, or `Unverified` with the
   evidence reviewed.
4. The Quality Verification Lead must not mark the frontend task complete
   unless both verdicts are `Conforms`, or the user explicitly accepts the
   stated residual risk for a `Deviates` or `Unverified` verdict.

Review depth is proportional to risk, but neither reviewer nor either verdict
may be skipped:

- `Light`: copy, isolated color, or similarly narrow changes. A concise
  no-impact or conformance statement is sufficient.
- `Standard`: component, form, layout, or responsive changes. Review relevant
  viewports, static accessibility, focus and keyboard implications, and
  recovery.
- `High`: navigation, information architecture, async state, modal, sticky
  geometry, drag interaction, or cross-page pattern changes. Review
  repository-wide patterns and full browser evidence appropriate to the risk.

Every frontend implementation plan (presented in chat) includes a
`Frontend Review Evidence` section containing:

- review depth and rationale;
- Web Experience Designer pre-implementation specification;
- Browser Interaction Reviewer pre-implementation criteria;
- planned browser evidence;
- both post-implementation verdicts and their evidence;
- Quality Verification Lead completion decision.

The post-implementation verdicts and the completion decision are recorded in
the task's `docs/CHANGELOG.md` entry.

For frontend review-only tasks, both reviewers must each deliver their normal
review output. No implementation-phase fields are required, but role names
alone still do not count as review evidence.

