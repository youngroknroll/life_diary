# 관찰 문구가 같은 시간대를 두고 반대로 말하던 문제

범위: `apps/stats/aggregation/density.py` 의 `get_gap_pattern`

## 어떻게 찾았나

시안 정합 7단계 배포를 앞두고 **운영 DB 덤프를 로컬에 복원해 마이그레이션을
리허설**하다가 나왔다. 마이그레이션 자체는 문제가 없었고, 복원본으로 실제
화면 로직을 돌려 보던 중 한 사용자의 요약에서 이게 나왔다.

```
[gap]    00–02시가 비어 있습니다
[steady] 00–02시는 매일 기록했습니다
```

같은 시간대를 두고 정반대로 말한다. 합성 데이터로는 나오지 않았고 **실제
기록 패턴에서만** 나왔다.

## 원인

```python
grid[0..6][0..1] = [[60,60], [0,0], [0,0], [0,0], [0,0], [0,0], [60,60]]
pattern = {'worst_range': (0, 2), 'missing_days': 5, 'best_range': (0, 2)}
```

`_most_common_window` 는 조건에 맞는 날이 **하나라도 있으면** 승자로 뽑는다.
`best_range` 는 "가장 자주 꽉 찬 구간"이지 "매일 꽉 찬 구간"이 아니다.

그런데 화면 문구는 `"%(start)02d–%(end)02d시는 매일 기록했습니다"` 로
**매일이라고 단정한다**(`summary.py` `_observations`). 7일 중 2일만 채운
구간을 두고 매일이라 말한 것이다.

이 사용자는 대부분의 시간을 10분 단위로 띄엄띄엄 적어서 "꽉 찬 시간"이 드물다.
그래서 2일뿐인 00–02시가 최고 기록 구간으로 뽑혔고, 동시에 5일이나 비어서
최악 구간으로도 뽑혔다.

## 고친 것

```python
"best_range": best_range if full_days == len(grid) else None,
```

문구가 "매일"이라고 말하므로, **정말 매일 꽉 찬 구간일 때만** 내세운다.

모순도 함께 사라진다 — 모든 날 꽉 찬 구간은 빈 날이 0이므로 최악 구간이 될
수 없고, 모든 구간의 빈 날이 0이면 `missing_days` 가 0이라 `worst_range` 가
`None` 이 된다.

문구는 손대지 않았다. 고칠 것은 문장이 아니라 그 문장이 참이 아닌 자리에
나오던 조건이다.

## 검증

RED → GREEN. 새 테스트 2건 —

- 7일 중 일부만 꽉 찬 구간은 `best_range` 가 아니다
- 한 구간이 최악과 최고에 동시에 뽑히지 않는다 (`assert (0,2) != (0,2)` 로 실패)

기존 `test_finds_the_window_that_is_full_on_the_most_days` 는 이름이 새 규칙과
어긋나 `..._is_full_every_day` 로 고쳤다. 격자는 이미 7일 전부 꽉 찬 것이라
동작은 그대로 통과한다.

| 검사 | 결과 |
|---|---|
| 전체 회귀 | **468 passed** |
| `manage.py check` | 0 issues |
| 마이그레이션 드리프트 | No changes detected |

운영 데이터 복원본에서 재확인 —

```
before  worst_range=(0,2) missing_days=5 best_range=(0,2)   관찰 3건(모순 포함)
after   worst_range=(0,2) missing_days=5 best_range=None    관찰 2건
```

## 남긴 것

`_most_common_window` 는 `worst_range` 쪽에서는 여전히 "가장 자주"가 맞다.
공백 문구가 `"지난 7일 중 %(days)d일"` 로 **날 수를 함께 말하기 때문**이다.
단정하지 않는 문구라 그대로 둔다.
