# 2026-04-09 Business Logic Analysis

> Scope: `dashboard`, `tags`, `users`, `stats`, `core` 앱의 비즈니스 로직 구조 분석

## 1. 기능별 비즈니스 로직 분석

이 프로젝트의 핵심 도메인은 "하루를 10분 단위로 기록하고, 태그 기준으로 집계해 목표와 통계로 해석하는 것"이다. 중심 엔티티는 `TimeBlock`, `Tag`, `UserGoal`, `UserNote` 네 가지다.

### 1.1 시간 기록

핵심 모델은 [`apps/dashboard/models.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/dashboard/models.py)의 `TimeBlock`이다.

- 하루를 144개 슬롯으로 분할한다.
- 각 슬롯은 10분 단위다.
- `(user, date, slot_index)` 유니크 제약으로 같은 시간대 중복 기록을 막는다.
- `tag`는 nullable이며, 태그가 없어도 기록 자체는 성립한다.
- `clean()`에서 다른 사용자의 비기본 태그를 참조하지 못하게 막는다.

즉 이 모델은 단순한 로그가 아니라 "사용자의 하루를 전부 채울 수 있는 시간 그리드"라는 도메인 가정을 전제로 한다.

관련 입력 로직은 [`apps/dashboard/views.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/dashboard/views.py)에 있다.

- `dashboard_view()`는 선택한 날짜의 `TimeBlock`을 조회해 144개 슬롯 전체를 렌더링용 데이터로 만든다.
- `time_block_api()`는 슬롯 배열 단위로 기록을 생성, 수정, 삭제한다.
- `POST` 요청에서는 기존 슬롯은 수정하고 없는 슬롯은 생성한다.
- `DELETE` 요청에서는 선택 슬롯 범위의 기록을 일괄 삭제한다.

이 로직의 실질적인 비즈니스 규칙은 아래와 같다.

- 사용자는 하루 전체를 10분 슬롯 단위로 관리한다.
- 여러 슬롯을 한 번에 같은 태그와 메모로 저장할 수 있다.
- 메모는 최대 500자다.
- 태그는 사용자 본인 태그 또는 시스템 기본 태그만 허용된다.

### 1.2 태그 관리

태그 도메인은 [`apps/tags/models.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/tags/models.py) 와 [`apps/tags/views.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/tags/views.py)에 들어 있다.

`Tag` 모델의 규칙은 다음과 같다.

- `user != None` 이면 사용자 전용 태그다.
- `user == None` 이고 `is_default=True` 이면 모든 사용자가 쓰는 기본 태그다.
- 사용자 태그는 사용자별 이름 중복이 금지된다.
- 기본 태그는 전역에서 이름 중복이 금지된다.
- 태그 이름은 trim 후 공백만 남는 값이 될 수 없다.
- 색상은 HEX 형식이어야 한다.

뷰 로직의 규칙은 다음과 같다.

- 일반 사용자는 자기 태그와 기본 태그를 함께 조회할 수 있다.
- 기본 태그 생성은 슈퍼유저만 가능하다.
- 일반 사용자는 기본 태그를 수정, 삭제할 수 없다.
- 기본 태그가 `TimeBlock`에서 사용 중이면 삭제할 수 없다.

즉 태그 기능은 단순 CRUD가 아니라 "개인 태그 + 공용 태그" 권한 모델을 포함한 도메인이다.

### 1.3 목표와 메모

사용자별 목표와 메모는 [`apps/users/models.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/users/models.py), [`apps/users/forms.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/users/forms.py), [`apps/users/views.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/users/views.py)에 나뉘어 있다.

`UserGoal`의 핵심 규칙은 다음과 같다.

- 특정 태그에 대해 `daily`, `weekly`, `monthly` 목표 시간을 지정한다.
- 목표 시간은 0 이상이어야 한다.
- 일간 목표는 24시간, 주간은 100시간, 월간은 300시간을 넘을 수 없다.

이 검증은 모델과 폼 양쪽에 중복되어 있다. 이는 사용자 입력 방어에는 도움이 되지만, 규칙 변경 시 수정 지점이 둘이라는 의미이기도 하다.

`mypage()`는 목표 조회와 달성률 계산의 연결 지점이다.

- 사용자의 목표를 읽는다.
- 통계 계산 결과를 가져온다.
- 각 목표의 실제 시간과 달성률을 계산해 뷰 모델에 주입한다.

`UserNote`는 구조상 단순 메모 모델이지만, 마이페이지와 통계 페이지의 부가 문맥 데이터로 활용된다.

### 1.4 통계와 피드백

가장 밀도 높은 비즈니스 계산은 [`apps/stats/logic.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/stats/logic.py)에 있다.

여기서는 `StatsCalculator`가 공통 규칙을 담당하고, 그 위에서 일간, 주간, 월간 통계를 만든다.

- `get_daily_stats_data()`
- `get_weekly_stats_data()`
- `get_monthly_stats_data()`
- `get_tag_analysis_data()`
- `get_stats_context()`

이 통계 계층의 핵심 규칙은 다음과 같다.

- 기록이 없는 시간도 분석 대상에 포함한다.
- 비어 있는 슬롯은 `미분류` 시간으로 계산한다.
- 월간 집계에서는 태그별 일일 누적 시간과 총 시간을 함께 계산한다.
- 주간 집계에서는 수면과 미분류를 제외한 활동 시간을 별도 계산한다.
- 목표 달성률 계산은 통계 결과를 재활용한다.

즉 이 프로젝트는 "입력된 데이터만 집계"하는 구조가 아니라, 비어 있는 시간까지 해석해서 사용자의 하루와 달 전체를 분석하려는 구조다.

피드백 로직은 [`apps/stats/feedback.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/stats/feedback.py)에 따로 분리되어 있다.

- 월간 목표 미달 또는 달성 여부 피드백
- 주간 증감 비교 피드백
- 특정 태그 편중 피드백
- 활동 리듬 변동성 피드백
- 휴식 과다 비중 피드백
- 미기록 시간 비중 피드백
- 루틴 제안 피드백

즉 피드백은 별도의 AI 모델이 아니라, 통계 결과를 규칙 기반으로 해석하는 문장 생성 계층이다.

### 1.5 공통 유틸리티

[`apps/core/utils.py`](/Users/yeongroksong/Desktop/study/project/knou/lifeDiary/apps/core/utils.py)에는 비즈니스 로직을 간접적으로 떠받치는 공통 규칙이 들어 있다.

- 날짜 파싱
- 슬롯과 시간 간 변환
- 기록량 기반 시간 계산
- 표준 JSON 응답 포맷
- 목표 달성률 계산
- 주간, 월간 날짜 범위 계산

특히 `calculate_goal_percent()`는 `users`와 `stats` 사이에 걸친 교차 도메인 계산을 공통화한 지점이다.

## 2. 현재 구조의 설계상 문제점

전체 도메인 개념은 비교적 선명하지만, 실제 구현 구조에는 몇 가지 명확한 약점이 있다.

### 2.1 비즈니스 규칙이 뷰에 많이 들어가 있음

시간 블록 저장, 태그 생성, 태그 수정, 태그 삭제 같은 핵심 규칙이 `views.py`에 직접 들어 있다.

- 입력 검증
- 권한 검사
- 중복 정책
- 생성, 수정, 삭제 분기
- 응답 포맷

이 구조는 초기 개발에는 빠르지만, 같은 규칙을 다른 진입점에서 재사용하기 어렵다. 예를 들어 REST API, Django form, admin action, 배치 작업이 동시에 생기면 규칙이 쉽게 분산된다.

### 2.2 모델, 폼, 뷰에 규칙이 중복됨

대표적으로 목표 시간 상한 검증은 모델과 폼 양쪽에 들어 있다. 태그 이름 trim, 중복 규칙, 권한 정책도 일부는 모델, 일부는 뷰에 있다.

이 구조의 문제는 다음과 같다.

- 규칙의 단일 출처가 없다.
- 수정 시 누락 가능성이 있다.
- 테스트 작성 범위가 넓어진다.

### 2.3 통계 계산기의 책임이 큼

`StatsCalculator`와 `stats/logic.py`는 사실상 아래 책임을 동시에 가진다.

- 날짜 범위 계산
- 빈 슬롯 보정
- 태그별 시간 집계
- 활동 시간 계산
- 월간 분석용 데이터 생성
- 뷰 컨텍스트 조립

즉 "계산 엔진"과 "화면용 데이터 빌더"가 한 파일 안에 섞여 있다. 이 구조는 수정 시 영향 범위를 넓히고, 특정 계산만 독립 테스트하기 어렵게 만든다.

### 2.4 태그 정책이 암묵적으로 퍼져 있음

태그는 개인 태그와 기본 태그라는 중요한 도메인 차이를 갖지만, 그 정책이 여러 파일에 산재해 있다.

- `Tag` 모델의 제약
- `TimeBlock.clean()`의 태그 소유권 검사
- 태그 뷰의 접근 권한
- 목표 폼의 태그 queryset 제한

정책이 분산되면 "어떤 태그를 누가 쓸 수 있는가"가 코드 탐색 없이는 바로 보이지 않는다.

### 2.5 피드백 로직이 통계 컨텍스트 구조에 강하게 결합됨

`generate_feedback()`는 `context` 딕셔너리 내부 구조를 많이 알고 있다. 이 방식은 간단하지만, 통계 컨텍스트 키 이름이나 데이터 구조가 바뀌면 피드백 로직도 쉽게 깨진다.

즉 현재는 느슨한 인터페이스가 아니라, 내부 구현 디테일에 직접 의존하는 형태다.

### 2.6 도메인 서비스 계층 부재

현재 구조는 Django 앱 분리는 되어 있지만, 실제 도메인 유스케이스를 표현하는 서비스 계층은 없다. 그래서 "시간 기록 저장", "태그 정책 검증", "목표 달성 계산", "통계 생성"이 각각 모델, 유틸, 뷰 함수로 흩어져 있다.

프로젝트가 커질수록 이 문제는 아래와 같이 드러난다.

- 로직 재사용이 어려움
- 테스트가 뷰 중심으로 기울어짐
- 정책 변경의 영향 범위가 넓음
- 프론트엔드나 API 확장 시 중복 구현 가능성 증가

## 3. 서비스 레이어 기준 리팩터링 방향

현재 구조를 전면 재작성할 필요는 없다. 다만 비즈니스 규칙을 유스케이스 단위 서비스로 옮기면 구조가 훨씬 안정된다. 추천 방향은 "모델은 데이터 제약, 서비스는 유스케이스, 뷰는 입출력" 원칙으로 정리하는 것이다.

### 3.1 dashboard 서비스 분리

우선순위가 가장 높은 것은 시간 기록 저장 로직이다.

예시 분리 방향:

- `apps/dashboard/services/time_block_service.py`
- `get_daily_slots(user, date)`
- `save_time_blocks(user, date, slot_indexes, tag_id, memo)`
- `delete_time_blocks(user, date, slot_indexes)`

이렇게 하면 뷰는 요청 파싱과 HTTP 응답만 담당하고, 핵심 규칙은 서비스가 맡게 된다.

서비스가 맡아야 할 규칙:

- 슬롯 배열 검증
- 메모 길이 검증
- 태그 접근 가능 여부 검증
- 기존 블록 조회
- 생성 대상과 수정 대상 분리
- bulk create, bulk update 수행

### 3.2 tag 정책 서비스 분리

태그는 CRUD보다 정책이 중요하므로 서비스 계층으로 묶는 편이 좋다.

예시 분리 방향:

- `apps/tags/services/tag_service.py`
- `get_available_tags(user)`
- `create_tag(actor, name, color, is_default=False)`
- `update_tag(actor, tag, name, color, is_default=None)`
- `delete_tag(actor, tag)`
- `can_use_tag(user, tag)`

이 계층이 생기면 태그 정책을 한곳에서 설명할 수 있고, `dashboard`, `users`, `tags` 앱이 같은 규칙을 공유하게 된다.

### 3.3 stats 계산 계층 분해

현재 `stats/logic.py`는 너무 많은 역할을 하므로 최소 3개 층으로 나누는 것이 좋다.

- `range_service`: 주간, 월간 날짜 범위 계산
- `aggregation_service`: 일간, 주간, 월간 시간 집계
- `presentation_service`: 템플릿이나 차트용 JSON 직렬화 컨텍스트 조립

예시 구조:

- `apps/stats/services/date_ranges.py`
- `apps/stats/services/time_aggregation.py`
- `apps/stats/services/stats_context_builder.py`
- `apps/stats/services/feedback_service.py`

이렇게 나누면 "순수 계산"과 "화면 표시용 구조 생성"을 분리할 수 있다.

### 3.4 goal 계산 책임 정리

`calculate_goal_percent()`는 이미 공통화가 되어 있지만, 장기적으로는 `users` 도메인 서비스로 옮기는 것이 더 자연스럽다.

예시 분리 방향:

- `apps/users/services/goal_service.py`
- `calculate_goal_progress(goal, stats_bundle)`
- `attach_goal_progress(goals, stats_bundle)`

이렇게 하면 목표는 통계를 소비하는 독립 도메인으로 표현되고, `core/utils.py`는 진짜 범용 유틸만 남길 수 있다.

### 3.5 피드백 입력 계약 명확화

현재 `generate_feedback(context)`는 너무 넓은 입력을 받는다. 이를 아래처럼 좁히는 것이 좋다.

- `generate_feedback(monthly_stats, weekly_stats=None, goals=None)`
- 또는 `FeedbackInput` 같은 명시적 데이터 객체 사용

핵심은 피드백 계층이 전체 템플릿 컨텍스트를 아는 구조를 끊는 것이다.

### 3.6 추천 리팩터링 순서

리스크와 효과를 같이 보면 다음 순서가 적절하다.

1. `dashboard` 시간 기록 저장 로직 서비스화
2. `tags` 정책 로직 서비스화
3. `stats/logic.py` 계산과 컨텍스트 조립 분리
4. `goal` 계산을 `users` 서비스로 이동
5. `feedback` 입력 구조 축소

이 순서가 좋은 이유는 현재 사용자 영향도가 큰 저장 로직부터 경계가 분명해지고, 이후 통계와 피드백 쪽은 비교적 안전하게 내부 구조를 정리할 수 있기 때문이다.

## 결론

이 프로젝트의 도메인 자체는 명확하다. 사용자는 10분 단위로 하루를 기록하고, 태그를 기준으로 시간을 분류하며, 그 결과를 목표 달성률과 통계, 피드백으로 확인한다.

문제는 도메인이 약한 것이 아니라, 그 도메인 규칙이 뷰, 모델, 유틸, 통계 파일에 분산되어 있다는 점이다. 따라서 다음 리팩터링의 핵심 목표는 기능 추가가 아니라 "규칙의 위치를 정리하는 것"이어야 한다.

가장 효과적인 방향은 서비스 레이어를 도입해 유스케이스 단위로 규칙을 모으고, 뷰는 HTTP 입출력에 집중하게 만드는 것이다. 특히 `dashboard`, `tags`, `stats` 세 영역부터 정리하면 이후 테스트성과 확장성이 크게 좋아질 가능성이 높다.
