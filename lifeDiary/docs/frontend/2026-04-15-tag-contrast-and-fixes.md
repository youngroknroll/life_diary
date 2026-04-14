# 태그 카테고리 수정 및 텍스트 대비 색상 개선

**날짜:** 2026-04-15
**범위:** 배포 마이그레이션 수정 · 태그 모달 카테고리 기능 복구 · JS 정리 · 텍스트 대비 색상 자동 조절

---

## 배경

카테고리(Category) 계층 구조 추가 이후 여러 문제가 발생했다.

1. **배포 환경(Render) 500 에러**: `manage.py migrate`가 dev 설정(SQLite)으로 실행되어 Supabase에 마이그레이션이 적용되지 않음
2. **태그 모달 카테고리 미표시**: 소스 `tag.js`에 `populateCategorySelect()` 함수가 누락됨 (staticfiles 복사본에만 존재)
3. **JS 중복/dead code**: `goToToday()` 3곳 중복 정의, `formatDate()` 미사용 코드 존재
4. **밝은 태그 글씨 안 보임**: 노란색 등 밝은 배경에서 흰색 글씨가 보이지 않는 문제

---

## 1. 배포 마이그레이션 수정

**문제**: Render start command의 `python manage.py migrate`가 `manage.py`의 기본 설정인 `lifeDiary.settings.dev`(SQLite)를 사용하여 Supabase에 마이그레이션이 적용되지 않았다.

**해결**: start command에 `--settings=lifeDiary.settings.prod` 명시.

```
cd lifeDiary && python manage.py collectstatic --no-input && python manage.py migrate --settings=lifeDiary.settings.prod && gunicorn lifeDiary.wsgi:application
```

---

## 2. 태그 모달 카테고리 기능 복구

**문제**: `collectstatic`으로 복사된 `staticfiles/core/js/tag.js`에만 카테고리 관련 코드가 있고, 소스 파일(`apps/core/static/core/js/tag.js`)에는 누락되어 있었다.

**수정 파일**: `apps/core/static/core/js/tag.js`

- `populateCategorySelect(selectedCategoryId)` 함수 추가 — `window._categories`에서 카테고리 목록을 읽어 `<select>` 옵션 생성
- 모달 열기 시 `populateCategorySelect()` 호출 (생성/수정 모두)
- 저장 시 `category_id`를 API 요청 데이터에 포함
- 카테고리 미선택 시 유효성 검사 추가

**수정 파일**: `apps/dashboard/templates/dashboard/index.html`

- `window._categories = JSON.parse('{{ categories_json|escapejs }}');` 추가하여 전역 카테고리 데이터 제공

---

## 3. JS dead code 제거 및 통일

### `goToToday()` 중복 제거

기존에 3곳에서 각각 다른 방식으로 정의되어 있었다.

| 위치 | 기존 구현 |
|------|----------|
| `utils.js` | `url.searchParams.set('date', formatDate(new Date()))` |
| dashboard | `url.searchParams.delete('date')` |
| stats | `location.href = '?date=' + today` |

`utils.js`의 `goToToday()`를 date 파라미터 제거 방식으로 통일하고 (서버가 date 없으면 오늘로 처리), dashboard/stats의 재정의를 삭제했다.

### `formatDate()` 제거

프로젝트 어디서도 호출되지 않는 dead code. 삭제.

### `loadAvailableTags()` API 호출 통일

dashboard의 `loadAvailableTags()`에서 raw `fetch()`를 `apiCall()` 래퍼로 교체하여 다른 API 호출과 패턴 통일.

---

## 4. 태그 텍스트 대비 색상 자동 조절

**문제**: 태그 badge의 텍스트가 `color: white`로 고정되어, 노란색 등 밝은 배경에서 글씨가 보이지 않았다.

**해결**: YIQ 밝기 공식으로 배경색 밝기를 판별하여 텍스트 색상을 자동 결정.

```
YIQ = (R×299 + G×587 + B×114) / 1000
밝기 ≥ 128 → 어두운 글씨 (#212529)
밝기 < 128 → 밝은 글씨 (#ffffff)
```

### JS (클라이언트 렌더링)

`apps/core/static/core/js/utils.js`에 `getContrastTextColor(hexColor)` 함수 추가.

```javascript
function getContrastTextColor(hexColor) {
    const hex = hexColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const yiq = (r * 299 + g * 587 + b * 114) / 1000;
    return yiq >= 128 ? '#212529' : '#ffffff';
}
```

### Python (서버 렌더링)

`apps/tags/models.py`의 Tag 모델에 `text_color` property 추가.

```python
@property
def text_color(self):
    hex_color = self.color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return '#212529' if yiq >= 128 else '#ffffff'
```

### 적용 위치

| 파일 | 위치 | 방식 |
|------|------|------|
| `dashboard/index.html` | 타임슬롯 텍스트 | `{{ slot.data.tag.text_color }}` |
| `dashboard/index.html` | 서버 범례 badge | `{{ tag.text_color }}` |
| `dashboard/index.html` | JS 범례 badge | `getContrastTextColor(tag.color)` |
| `tags/index.html` | 태그 카드 badge | `getContrastTextColor(tag.color)` |

> stats 페이지의 badge는 모두 `&nbsp;` 색상 스와치(텍스트 없음)이므로 수정 불필요.

---

## 수정 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `apps/core/static/core/js/utils.js` | `getContrastTextColor()` 추가, `formatDate()` 제거, `goToToday()` 통일 |
| `apps/core/static/core/js/tag.js` | `populateCategorySelect()` 추가, 카테고리 관련 로직 복구 |
| `apps/dashboard/templates/dashboard/index.html` | `window._categories` 초기화, `goToToday()` 중복 제거, 대비 색상 적용 |
| `apps/stats/templates/stats/index.html` | `goToToday()` 중복 제거 |
| `apps/tags/models.py` | Tag.text_color property 추가 |
| `apps/tags/templates/tags/index.html` | `color: white` → `getContrastTextColor()` |
| `apps/tags/migrations/0006_*`, `0007_*` | 카테고리 backfill 및 NOT NULL 마이그레이션 분리 |
| `apps/users/migrations/0002_*` | UserGoal.target_hours 유효성 검사 수정 |
