# Ad Revenue Marketing Strategy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make LifeDiary sustainable through advertising revenue first, with a target of covering roughly KRW 30,000/month in server operating costs.

**Architecture:** Keep the personal logging product free and avoid ads in private, high-trust app workflows. Build public, indexable informational pages as the ad inventory surface, then add conservative ad placements only after policy and content readiness checks. Treat revenue as a measured operating experiment, not as guaranteed short-term cost coverage.

**Tech Stack:** Django templates, existing i18n structure, Render, Supabase PostgreSQL, Google AdSense, Google Search Console, and optional Google Analytics or privacy-conscious equivalent.

---

## 1. Current Context

LifeDiary is a Django-based life logging service deployed toward a Render + Supabase production path. The product records time blocks, tags, goals, notes, and statistics. Current monetization direction is advertising-only for the first stage.

The current business constraint is practical:

- Target monthly operating cost: about KRW 30,000.
- Paid subscription is intentionally deferred.
- Advertising revenue is the first monetization channel.
- User trust matters because LifeDiary stores personal daily activity patterns.

This plan therefore separates two surfaces:

- Private app surface: dashboard, time recording, statistics, account pages.
- Public content surface: home, guide, examples, blog/update pages, policy pages.

Ads should live only on the public content surface during the initial stage.

## 2. Strategy Summary

### Recommended Strategy

Use LifeDiary as a free app and build an SEO/content layer around time tracking, life logging, study tracking, and weekly review. Apply for AdSense only after the site has enough original public content, clear policies, and stable navigation.

### Why This Strategy

Advertising needs page views, not just registered users. A private productivity app can have loyal users but few ad impressions if most usage happens behind login. Public informational content creates indexable pages that can generate ad impressions without weakening the core logging experience.

### Non-Goals

- Do not add ads inside the dashboard.
- Do not add ads next to save/delete/account actions.
- Do not block core features behind ads.
- Do not add subscription or tiered payment in this phase.
- Do not use aggressive popups, interstitials, or mobile sticky ads in the first ad rollout.

## 3. Business Targets

| Metric | Initial Target | Notes |
|---|---:|---|
| Monthly operating cost | KRW 30,000 | Current planning baseline |
| Stage 1 revenue target | First ad revenue | Proves ads are serving and reporting |
| Stage 2 revenue target | KRW 1,000/month | Confirms non-zero recurring ad revenue |
| Stage 3 revenue target | KRW 10,000/month | Partial operating cost coverage |
| Stage 4 revenue target | KRW 30,000/month | Operating cost break-even |
| First content target | 8-12 public pages | Enough to look like a real content site, not only an app shell |
| First traffic target | Search impressions and indexed pages | Before optimizing ad layout |

## 4. Positioning

### Core Message

LifeDiary is a free time logging tool that helps users record their day, classify time with tags, and review life patterns through statistics.

### Advertising-Safe Positioning

Use neutral productivity and self-review language:

- "하루를 기록하고 시간 사용 패턴을 돌아보세요."
- "공부, 일, 휴식 시간을 태그로 나누어 볼 수 있습니다."
- "주간 회고를 숫자와 기록으로 확인하세요."

Avoid exaggerated claims:

- Do not claim medical, mental health, coaching, or guaranteed productivity effects.
- Do not claim advertising revenue already covers costs until verified.
- Do not imply user diary content is used for ads.

## 5. Public Content Plan

Create public pages that are useful without login and relevant to LifeDiary.

### Priority 1: Required Trust Pages

These pages support ad review, user trust, and basic product legitimacy.

- Home page: current product introduction, CTA, and feature summary.
- Privacy policy: already exists, but review for advertising and cookie disclosures before ad launch.
- Terms of service: already exists.
- Contact path: visible email or contact method from public pages.
- About/Service introduction: explain what LifeDiary does and who it is for.

### Priority 2: Guide Pages

These should be indexable and useful to non-users.

- `/guide/`: LifeDiary 사용 가이드 index.
- `/guide/time-block/`: 30분 또는 일정 단위 시간 기록 방법.
- `/guide/tags/`: 태그로 하루를 분류하는 방법.
- `/guide/weekly-review/`: 주간 회고를 숫자로 확인하는 방법.
- `/guide/study-tracking/`: 공부 시간 기록 예시.
- `/guide/work-life-balance/`: 일, 휴식, 이동, 자기관리 시간 분류 예시.

### Priority 3: Content/Update Pages

These create ongoing traffic opportunities and portfolio evidence.

- `/updates/`: 개발 및 운영 로그 index.
- "LifeDiary를 Render와 Supabase로 운영하면서 배운 점."
- "시간 기록 앱에서 광고를 어디에 넣지 않기로 했는가."
- "개인 기록 서비스에서 사용자 신뢰를 지키는 UI 원칙."
- "태그 기반 시간 기록을 오래 유지하는 방법."

## 6. Ad Placement Policy

### Allowed Ad Locations

- Home page lower section.
- Guide article body after the first meaningful content section.
- Guide article bottom.
- Update/blog article bottom.
- Public FAQ page, if added later.

### Blocked Ad Locations

- Dashboard.
- Time block input grid.
- Tag selection sheet.
- Statistics page.
- Goal/note management pages.
- Login, signup, password reset, username recovery.
- Account deletion.
- Privacy policy and terms pages unless reviewed separately.

### Layout Rules

- No ad before the main title and first useful paragraph.
- No ad immediately next to primary CTA buttons.
- No ad that looks like navigation, tags, save buttons, or system messages.
- No mobile sticky ad in the first rollout.
- No modal, interstitial, or forced ad view.
- Limit initial placements to one or two per content page.

## 7. Analytics And Operating Metrics

Track revenue and traffic separately from product usage.

### Advertising Metrics

- Page views on public pages.
- Ad impressions.
- Estimated revenue.
- Page RPM.
- CTR.
- Top earning pages.
- Search traffic share.

### Product Metrics

- Signups.
- Active users.
- Time blocks created.
- Returning users.
- Guide-to-signup conversion.
- Ad pages viewed by logged-out users.

### Operating Metrics

- Render monthly cost.
- Supabase monthly cost.
- Email cost.
- Error rate.
- 5xx count.
- Response time trend.
- Database size trend.

## 8. Privacy And Trust Requirements

Before enabling ads, verify these items:

- Public privacy policy explains advertising/cookie usage if AdSense is enabled.
- The site does not say or imply that private diary content is used for ad targeting.
- Ads are not shown on private user content pages during the first rollout.
- Users can understand that the free service is supported by ads on public pages.
- Any analytics tool is documented in the privacy policy.

## 9. Phased Execution

### Phase 1: Content And Policy Readiness

Goal: Make the site reviewable as a useful public content site.

Tasks:

1. Review current home page and public policy pages.
2. Add or refine a visible contact path.
3. Draft guide page IA.
4. Create 5-8 original guide/update pages.
5. Review privacy policy for advertising and analytics disclosures.
6. Verify pages render in Korean and English if they use i18n.

Exit criteria:

- Public pages are reachable without login.
- Pages are not empty, thin, or placeholder content.
- Privacy/terms/contact are visible.
- No ads are placed yet.

### Phase 2: AdSense Application

Goal: Apply only after the public site is credible.

Tasks:

1. Connect domain/site ownership if needed.
2. Add Search Console.
3. Submit sitemap if available, or add one if missing.
4. Apply for AdSense.
5. Do not place aggressive or misleading ad placeholders.

Exit criteria:

- AdSense application submitted.
- Search Console starts collecting indexing data.
- Any rejection reason is documented before resubmission.

### Phase 3: Conservative Ad Rollout

Goal: Start ad serving without harming product trust.

Tasks:

1. Add ad include partial for public pages only.
2. Add a settings flag to disable ads by environment.
3. Add tests that private app pages do not render ad slots.
4. Add tests that selected public content pages can render ad slots when enabled.
5. Deploy with ads limited to public guide/update pages.

Exit criteria:

- Ads do not appear on dashboard, stats, auth, or account pages.
- Public content pages contain limited placements.
- First ad impression is visible in reporting.

### Phase 4: Revenue And Traffic Iteration

Goal: Improve content and placement based on data, not assumptions.

Tasks:

1. Record weekly public page views.
2. Record weekly AdSense estimated revenue.
3. Identify top search queries from Search Console.
4. Add one or two content pages per week around real query demand.
5. Compare revenue against the KRW 30,000 monthly operating target.

Exit criteria:

- At least four weeks of traffic/revenue data exists.
- Monthly ad revenue trend is documented.
- Decision made: continue ads only, add sponsorship/supporter plan, or reduce infrastructure cost.

## 10. Implementation Plan For Future Code Work

This section defines the future code/documentation tasks. Each task needs separate approval before implementation.

### Task 1: Public Content Structure

**Files:**

- Create: `templates/guide/index.html`
- Create: `templates/guide/time_block.html`
- Create: `templates/guide/tags.html`
- Create: `templates/guide/weekly_review.html`
- Modify: `lifeDiary/urls.py`
- Modify: `lifeDiary/views.py`
- Test: `apps/core/tests.py`

**Behavior:**

- Public guide pages return HTTP 200 without login.
- Header/footer remain consistent with existing layout.
- Pages are indexable and have useful titles.

**Verification:**

```bash
pytest apps/core/tests.py --tb=short
python manage.py check
git diff --check
```

### Task 2: Advertising Disclosure Review

**Files:**

- Modify: `templates/legal/privacy.html`
- Modify: `locale/ko/LC_MESSAGES/django.po`
- Modify: `locale/en/LC_MESSAGES/django.po`
- Test: `apps/core/test_i18n_phase1.py`

**Behavior:**

- Privacy page describes advertising cookies/analytics only if they are actually enabled.
- Korean and English pages render equivalent meaning.

**Verification:**

```bash
pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short
python manage.py compilemessages
git diff --check
```

### Task 3: Ad Slot Infrastructure

**Files:**

- Create: `templates/shared/_ad_slot.html`
- Modify: `lifeDiary/settings/dev.py`
- Modify: `lifeDiary/settings/prod.py`
- Modify: selected public templates only.
- Test: `apps/core/tests.py`

**Behavior:**

- Ads are controlled by an explicit setting.
- Public content pages can render ad slots.
- Private app pages never render ad slots during the first rollout.

**Verification:**

```bash
pytest apps/core/tests.py apps/dashboard/tests.py apps/stats/test_mobile_layout.py apps/users/test_auth_enhance_render.py --tb=short
python manage.py check
git diff --check
```

### Task 4: Search And Indexing Support

**Files:**

- Create or modify: sitemap/robots support, exact files to be determined after current URL inspection.
- Test: core routing/render tests.

**Behavior:**

- Public guide/update pages can be discovered by search engines.
- Private app pages are not exposed as indexable content.

**Verification:**

```bash
pytest apps/core/tests.py --tb=short
python manage.py check
git diff --check
```

## 11. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| AdSense rejection due to thin content | Delays monetization | Add original guide/update pages before applying |
| Ads damage user trust | Lower retention | Keep ads off private app workflows |
| Revenue too low for KRW 30,000/month | Server cost remains uncovered | Track four-week data, then decide cost reduction or supporter plan |
| Privacy policy mismatch | Compliance and trust issue | Update policy before enabling analytics/ads |
| Mobile ad layout harms UX | Higher bounce rate | Avoid sticky/interstitial ads initially |
| Search traffic grows slowly | Slow revenue growth | Publish query-driven guide content weekly |

## 12. Decision Gates

### Gate A: Content Readiness

Approve AdSense application only when:

- At least 5 substantial public pages exist.
- Privacy, terms, and contact path are visible.
- No placeholder pages are linked.

### Gate B: Ad Placement Readiness

Approve ad slot implementation only when:

- AdSense account/site status allows serving.
- Private app pages are explicitly excluded.
- Privacy disclosure is updated if needed.

### Gate C: Revenue Viability

After four weeks of ad data, decide one:

- Continue advertising-only strategy.
- Add more public content before changing monetization.
- Reduce infrastructure cost.
- Reconsider KRW 1,000 supporter subscription later.

## 13. Reporting Template

Weekly report:

```text
LifeDiary Ad Revenue Report

- Week:
- Public page views:
- Ad impressions:
- Estimated ad revenue:
- Top public pages:
- Search queries:
- Render cost:
- Supabase cost:
- Incidents/errors:
- Content shipped:
- Next experiment:
```

## 14. Deferred Refactoring Notes

Deferred Refactoring Note

- Topic: Subscription or supporter payment
- Why it is not part of the current scope: The current monetization decision is advertising-only.
- Why it may be needed later: Advertising may not cover KRW 30,000/month reliably at early traffic levels.
- Trigger condition: Four weeks of ad revenue data shows a clear gap against operating cost, or users request ad-free support.
- Expected change location: payment integration, account settings, privacy/terms, pricing page.
- Related tests: payment webhook tests, plan entitlement tests, ad visibility tests.

Deferred Refactoring Note

- Topic: Dedicated content management system
- Why it is not part of the current scope: Static Django templates are enough for the first 5-12 public pages.
- Why it may be needed later: Weekly content publishing may become cumbersome in templates.
- Trigger condition: More than 20 public guide/update pages or frequent non-developer editing.
- Expected change location: new content app, models, admin, sitemap.
- Related tests: public page routing, rendering, sitemap tests.
