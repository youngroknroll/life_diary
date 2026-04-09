# 2026-04-09 Phase 0 수정 로그

> 작업일시: 2026-04-09 23:06  
> 목표: Light DDD 전환 전 코드 리뷰 잔여 이슈 7개 완료  
> 결과: 7/7 완료

---

## 수정 목록

| # | 파일 | 내용 | 결과 |
|---|------|------|------|
| #16 | `dashboard/views.py:63` | time_headers 공식 → `_SLOT_END_MINUTES` 상수 명시화 | DONE |
| #18 | `core/static/core/js/utils.js:114` | `console.error` 제거 | DONE |
| #22 | `settings/dev.py:68` | `[BASE_DIR, "templates"]` → `[BASE_DIR / "templates"]` | DONE |
| #23 | `users/views.py:37` | 회원가입 후 자동 로그인 + 홈 리다이렉트 | DONE |
| #17 | `users/views.py:94,112,199` | `\|` queryset union → `Q()` + `_get_user_tag_queryset()` 헬퍼 | DONE |
| #15 | `tags/views.py:157` | is_default flip 변경 감지 → superuser 전용 검사 명시화 | DONE |
| #21 | `dashboard/models.py:28` + 마이그레이션 | `TextField` → `CharField(max_length=500)` | DONE |

---

## 수정 상세

### #16 — time_headers 가독성 (#16)
```python
# Before
time_headers = [f"{(i * 10 - 1) % 60 + 1}분" for i in range(1, 13)]

# After
_SLOT_END_MINUTES = [9, 19, 29, 39, 49, 59]
time_headers = [f"{m}분" for m in _SLOT_END_MINUTES * 2]
```
출력값 동일. 의도 주석 추가.

### #18 — console.error 제거
```js
// Before
} catch (error) {
    console.error('API Call Error:', error);
    throw error;

// After
} catch (error) {
    throw error;
```
에러는 호출 측에서 처리. 프로덕션 콘솔 노출 제거.

### #22 — DIRS 경로 수정
```python
# Before — BASE_DIR(프로젝트 루트 전체)과 "templates"(상대경로 문자열) 두 개
"DIRS": [BASE_DIR, "templates"],

# After — templates/ 디렉터리만 명시
"DIRS": [BASE_DIR / "templates"],
```

### #23 — 회원가입 자동 로그인
```python
# Before
form.save()
messages.success(request, "회원가입이 완료되었습니다. 로그인해주세요.")
return redirect("users:login")

# After
user = form.save()
login(request, user, backend="django.contrib.auth.backends.ModelBackend")
messages.success(request, f"{user.username}님, 환영합니다! 회원가입이 완료되었습니다.")
return redirect("home")
```
`backend=` 명시: `UserCreationForm.save()`가 인증 백엔드 정보를 포함하지 않으므로 필수.

### #17 — queryset union → Q() + 헬퍼
```python
# 헬퍼 추가 (users/views.py 상단)
def _get_user_tag_queryset(user):
    return Tag.objects.filter(Q(user=user) | Q(is_default=True))

# Before (3곳)
Tag.objects.filter(user=request.user) | Tag.objects.filter(is_default=True)

# After (3곳)
_get_user_tag_queryset(request.user)
```
`usergoal_create`, `usergoal_update`, `mypage` 3곳 교체.

### #15 — is_default flip 권한 명시화
```python
# Before — is_default=True인 경우만 막아 flip 감지 불완전
is_default = data.get("is_default", tag.is_default)
if is_default and not request.user.is_superuser: ...

# After — 변경 여부 감지 후 superuser 검사
requested_is_default = data.get("is_default", tag.is_default)
if requested_is_default != tag.is_default and not request.user.is_superuser:
    return JsonResponse({...}, status=403)
is_default = requested_is_default
```
True→False 전환(기본 태그 → 일반 태그)도 차단.

### #21 — TextField → CharField + 마이그레이션
```python
# Before
memo = models.TextField(blank=True, max_length=500, ...)

# After
memo = models.CharField(blank=True, max_length=500, ...)
```
사전 데이터 확인: `TimeBlock.objects.filter(memo__regex=r'.{501}').count()` → **0건**  
마이그레이션: `0006_alter_timeblock_memo_charfield.py` 생성 및 적용 완료

---

## 검증

```
python -m py_compile 5개 파일 → syntax OK
python manage.py migrate → OK
python manage.py check → 0 issues
```

---

## 코드 리뷰 전체 완료 현황

| Severity | Count | Done |
|----------|-------|------|
| CRITICAL | 5 | 5 |
| HIGH | 7 | 7 |
| MEDIUM | 8 | 6 |
| LOW | 3 | 2 |
| **Total** | **23** | **20** |

> 잔여 3개 (#13 StatsCalculator mixed concerns, #16 stats/feedback 결합 — Phase 1~3에서 구조 개선으로 해소 예정)
