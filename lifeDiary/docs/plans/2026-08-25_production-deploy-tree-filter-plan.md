# production 배포 트리에서 문서 경로 제외 계획

작성 2026-08-25. 브랜치 `chore/production-deploy-tree-filter`.

## Context

현재 배포 흐름:

```
main push → .github/workflows/deploy-pr.yml 이 main→production PR 생성·갱신
          → 사람이 PR 병합 → production 갱신 → Render 자동 배포
```

문제 둘.

1. **문서만 바꿔도 배포가 움직인다.** `deploy-pr.yml` 은 main 으로의 모든 push 에
   반응한다. 계획서 한 줄을 고쳐도 배포 PR 이 갱신되고, 병합하면 Render 가 다시
   빌드한다.
2. **런타임에 필요 없는 파일이 production 에 실린다.** `lifeDiary/docs/` 만
   135개 3.6MB 다. Django 가 서빙하지 않으므로 런타임 영향은 없지만 배포 대상에
   들어갈 이유도 없다.

조사로 확인한 사실:

- 런타임 코드가 이 파일들을 읽는 곳은 없다. `apps/stats/aggregation/weekly_summary.py:7`
  의 docstring 참조 한 건뿐이고 파일을 열지 않는다.
- 지금 `origin/production` 에만 있는 blob 은 **0건**이다. main 과 내용이 같다.
  배포 모델을 바꾸기에 가장 안전한 시점이다.
- production 은 main 보다 커밋 1개 앞선다(PR #60 병합 커밋).

## 사용자 결정 (2026-08-25)

| 항목 | 결정 |
|---|---|
| 제외 범위 | **둘 다** — 배포 트리거도 막고 production 브랜치에서 파일도 없앤다 |
| 제외 경로 | `lifeDiary/docs/**`, `.claude/**`, `README.md`, `lifeDiary/prompt_plan.md`, `lifeDiary/AGENTS.md`, `lifeDiary/CLAUDE.md` |

## 설계 — production 을 "생성된 배포 트리"로 바꾼다

핵심은 **머지를 배포 수단에서 뺀다**는 것이다. 머지로 배포하면 main 의 트리가
그대로 production 에 실려서 경로를 뺄 방법이 없다. 대신 main 의 트리에서 제외
경로를 지운 트리를 만들어 production 에 커밋한다.

```
main@abc123 트리
  └─ 제외 경로 제거 → TREE
       └─ git commit-tree TREE -p origin/production -m "deploy: main@abc123"
            └─ git push origin <commit>:refs/heads/production   (force 아님)
```

`-p origin/production` 이므로 production 은 **선형으로 이어지고 force-push 가
필요 없다.** 히스토리가 배포 단위로 하나씩 쌓인다.

### 문서만 바뀌면 배포가 아예 불가능해진다

필터된 트리 해시를 현재 production 트리 해시와 비교한다. 문서만 바뀐 main
커밋은 **필터 후 트리가 완전히 동일**하므로 푸시할 것이 없다. 워크플로가 여기서
멈춘다. 트리거를 "막는" 게 아니라 배포할 내용이 없어서 못 하는 구조다.

### 트리거는 수동으로

`workflow_dispatch` 로만 돈다. main push 자동 트리거를 두지 않는다. 사용자가
"지속적으로 배포되는 게 싫다"고 했고, `AGENTS.md` 도 배포 실행을 사용자 몫으로
둔다.

## 승인 범위

1. `.github/workflows/deploy.yml` 신규 — 수동 배포, 트리 필터, 검증, 푸시
2. `.github/workflows/deploy-pr.yml` 제거 — 머지 배포 경로를 없앤다
3. `.github/workflows/pr-checks.yml` 의 `branches: [main, production]` 에서
   `production` 제거 — production 으로 가는 PR 자체가 없어진다
4. 배포 문서 갱신 (`docs/` 내 해당 항목, `docs/project-status.md`)

## 명시적 제외

- Render 대시보드 설정 변경 (자동 배포 대상 브랜치는 production 그대로)
- 브랜치 보호 규칙 설정 — GitHub 설정이라 사용자가 직접 해야 한다. 권고만 남긴다
- `lifeDiary/docs/` 를 다른 저장소로 옮기는 것
- 기존 production 히스토리 정리

## 수락 기준

| # | 기준 |
|---|---|
| A1 | 배포는 `workflow_dispatch` 로만 실행된다. main push 는 어떤 배포도 일으키지 않는다 |
| A2 | 배포된 production 트리에 제외 경로 파일이 하나도 없다 |
| A3 | 제외 경로 외 모든 파일은 main 과 바이트 단위로 같다 |
| A4 | 문서만 바뀐 main 커밋으로 배포를 돌리면 "배포할 변경 없음"으로 끝나고 production 이 갱신되지 않는다 |
| A5 | production 에만 있는 파일이 감지되면 배포가 **실패로 중단**된다 (지금은 경고만) |
| A6 | 배포 전 기존 검증(`test_prod_settings.py`, `test_email_backends.py`, prod deploy check)이 그대로 돈다 |
| A7 | 각 배포 커밋 메시지에 원본 main SHA 가 남아 무엇이 배포됐는지 추적된다 |
| A8 | force-push 없이 fast-forward 로 푸시된다 |

## 활성 역할 / 미활성 역할

Risk-Based Routing 의 "Deployment/configuration 변경" 행.

| 역할 | 상태 | 이유 |
|---|---|---|
| Deployment & Operations Reviewer | 활성 | 배포 경로·롤백·실패 모드가 통째로 바뀐다 |
| Backend & Integration Engineer | 활성 | 워크플로 파일 구현 |
| Quality Verification Lead | 활성 | 실배포 전 검증 증거 판정 |
| Security & Resilience Reviewer | 활성(조건) | 워크플로에 `contents: write` 권한과 브랜치 푸시가 생긴다 |
| Backend TDD Coach | 미활성 | Django 런타임 행위가 바뀌지 않는다. 검증은 워크플로 실측이다 |
| Product Scope Owner / Domain Architecture Reviewer | 미활성 | 제품 범위·도메인 경계 변화 없음 |
| 프런트엔드 3역 · AI Automation Architect | 미활성 | 해당 없음 |

## 위험과 대응

| 위험 | 대응 |
|---|---|
| production 에 직접 커밋한 내용이 다음 배포에서 사라진다 | 배포 전 orphan blob 검사. 발견되면 **중단**한다. 현재 워크플로는 경고만 하는데 이번에 강화한다 |
| 머지 PR 이 사라져 "무엇이 배포 대기 중인지" 보기 어려워진다 | 배포 커밋 메시지에 `deploy: main@<sha>` 를 남기고, 워크플로 job summary 에 이번에 실리는 커밋 목록을 출력한다. 대기 목록은 `<마지막 배포 sha>..main` 으로 언제든 뽑을 수 있다 |
| production 으로 PR 을 머지하면 필터를 우회한다 | `pr-checks.yml` 에서 production 트리거를 빼고, 브랜치 보호로 직접 push·머지를 막도록 사용자에게 권고한다 |
| 워크플로에 쓰기 권한이 생긴다 | `permissions: contents: write` 를 이 잡에만 준다. `concurrency` 로 동시 배포를 막는다 |
| 롤백 경로 | production 히스토리가 배포 단위로 선형이므로 이전 배포 커밋으로 되돌려 push 하면 된다. 필요하면 그 SHA 로 워크플로를 다시 돌린다 |
| 첫 배포가 잘못되면 | 지금 production == main 이라 되돌릴 지점이 명확하다. 첫 실행은 dry-run(푸시 없이 트리 비교만) 으로 확인한 뒤 실제 푸시한다 |

## 구현 단계 (운영 리뷰 반영 — 단계적 롤아웃)

리뷰가 "신규 경로를 한 번도 안 써 보고 유일한 배포 수단을 없애는 순서"를
블로커로 지적했다. 옛 경로와 **병존**시키고, 실배포 1회 성공 뒤에 철거한다.

### 1단계 — 신규 워크플로 + 옛 경로의 문서 트리거만 차단

| 파일 | 작업 |
|---|---|
| `.github/workflows/deploy.yml` | 신규. 수동 배포, 트리 필터, 검증, fast-forward 푸시 |
| `.github/workflows/deploy-pr.yml` | **유지.** `paths-ignore` 만 추가해 문서 커밋이 배포 PR 을 흔들지 않게 한다 |

이 단계만으로 사용자 요구 1(문서 변경이 배포를 흔들지 않음)이 즉시 충족되고,
기존 배포 경로는 안전망으로 남는다.

### 2단계 — dry-run

`deploy.yml` 을 `dry_run=true` 로 실행해 orphan 검사·트리 비교·job summary 를
실측한다. production 은 변하지 않는다.

### 3단계 — 최초 실배포

`dry_run=false`. **여기가 되돌릴 수 없는 지점이다.** Render 배포 후 앱 기동과
화면 렌더를 확인한다.

### 4단계 — 롤백 리허설

정상 상황에서 `ref` 에 직전 배포 SHA 를 넣어 다시 실행해 롤백 경로가 실제로
동작하는지 확인한다. 사고 상황에서 처음 시도하지 않는다.

### 5단계 — 옛 경로 철거 (실배포·리허설 성공 뒤에만)

| 파일 | 작업 |
|---|---|
| `.github/workflows/deploy-pr.yml` | 삭제 |
| `.github/workflows/pr-checks.yml` | `branches: [main, production]` → `[main]` |

### 6단계 — 문서

작업 로그와 `docs/project-status.md` 갱신. 배포 절차가 "PR 병합" 에서
"Actions → Deploy 실행" 으로 바뀐 것을 명시한다.

## 검증

로컬에서 워크플로 로직과 동일한 명령을 돌려 트리를 만들어 검증한다. 실제 푸시는
사용자 승인 뒤 dry-run → 실배포 순서로 한다.

```bash
# 필터된 트리 생성 (로컬, 푸시 없음)
git read-tree origin/main
git rm -r --cached -q lifeDiary/docs .claude README.md \
    lifeDiary/prompt_plan.md lifeDiary/AGENTS.md lifeDiary/CLAUDE.md
TREE=$(git write-tree)

# A2: 제외 경로가 없는가
git ls-tree -r --name-only "$TREE" | grep -E '^(lifeDiary/docs/|\.claude/|README\.md$|lifeDiary/(prompt_plan|AGENTS|CLAUDE)\.md$)' | wc -l   # 0 이어야 한다

# A3: 나머지가 main 과 같은가
diff <(git ls-tree -r origin/main | grep -vE '<제외 패턴>') <(git ls-tree -r "$TREE")   # 차이 없어야 한다

# A4: 문서만 바뀐 커밋이면 트리가 그대로인가
# 문서 커밋 앞뒤로 위 과정을 돌려 TREE 해시가 같은지 본다
```

기대 증거: 제외 경로 파일 수 0, 나머지 트리 diff 없음, 문서 커밋 전후 트리 해시
동일, orphan 검사 0건.

## 대안 (더 작은 변경)

파일은 그대로 두고 트리거만 막는 방법도 있다. `deploy-pr.yml` 에
`paths-ignore` 를 넣고 Render 의 Ignored Paths 에 문서 경로를 넣으면 5줄로
끝나고 배포 모델은 그대로다. 사용자가 "둘 다" 를 선택해 이 계획을 택했지만,
위험 대비 이득이 맞지 않는다고 판단되면 이쪽으로 축소할 수 있다.

## Deferred

- 브랜치 보호 규칙 (GitHub 설정, 사용자 몫)
- 배포 대기 상태를 보여주는 별도 알림
- `lifeDiary/docs/` 를 별도 저장소로 분리


## 운영 리뷰 반영 (2026-08-25)

Deployment & Operations Reviewer 사전 리뷰에서 블로커 4건이 나왔다. 조치는
다음과 같다.

| # | 블로커 | 조치 |
|---|---|---|
| 1 | **승인 게이트 부재.** 지금은 PR diff 를 보고 병합하는 행위가 곧 승인인데, `workflow_dispatch` 는 버튼 누른 사람이 곧 승인자다 | job 에 `environment: production` 을 붙인다. GitHub Environments 에 required reviewers 를 켜면 그 즉시 승인 게이트가 생기고, 켜지 않아도 워크플로는 그대로 동작한다. 켜는 방법을 문서에 남긴다 |
| 2 | **브랜치 보호와 충돌.** production 에 "Require a pull request" 를 걸면 이 워크플로의 직접 push 가 거부된다 | 계획과 작업 로그에 "브랜치 보호를 걸 때 Actions 를 예외로 두어야 한다"를 명시한다. 예외 없이 걸면 배포가 막힌다 |
| 3 | **`deploy-pr.yml` 즉시 삭제 위험** | 위 단계적 롤아웃으로 바꿨다. 실배포 1회 성공 뒤 철거 |
| 4 | **orphan 차단 시 복구 런북 없음** | 아래 런북을 추가한다 |

리뷰가 `docs/project-status.md` 462-499행에서 찾아낸 근거: 2026-08-12 에 도메인
`ALLOWED_HOSTS` 수정이 production 에 직접 들어가 main 과 어긋난 적이 있다.
orphan 검사를 경고에서 차단으로 올리는 판단은 가설이 아니라 실제 이력에 근거한다.

### 런북 — orphan 검사로 배포가 막혔을 때

```
1. 워크플로 로그의 orphan 파일 목록을 확인한다.
2. 그 내용이 아직 필요한가?
   필요하다  → production 의 해당 변경을 main 에 먼저 반영한다(PR).
                main 에 들어간 뒤 다시 배포한다.
   불필요하다 → main 에 이미 대체 내용이 있는지 확인하고,
                확인되면 배포를 다시 돌린다(검사가 통과한다).
3. 급한 배포가 겹쳤다면: orphan 을 main 에 반영하는 PR 이 가장 빠른 길이다.
   검사를 끄고 배포하면 그 내용이 조용히 사라진다. 끄지 않는다.
```

### 롤백 절차

```
1. Actions → Deploy to production 실행
2. ref = 마지막으로 정상이었던 main SHA
3. dry_run=true 로 무엇이 배포되는지 확인
4. dry_run=false 로 실행
```

그 SHA 의 필터된 트리가 현재 production 을 부모로 새 커밋이 되어 올라간다.
fast-forward 제약과 맞는다.

**production 을 되돌리는 것과 main 을 고치는 것은 별개다.** 롤백해도 main 의
문제 커밋은 그대로라 다음 정배포에서 다시 실린다. main 쪽 revert PR 을 따로
올려야 한다.

### 사용자가 직접 확인해야 하는 항목 (레포에서 확인 불가)

- GitHub → Settings → Environments → `production` 에 required reviewers 를 켤지
- GitHub → Settings → Branches → production 브랜치 보호 현재 상태와 Actions 예외
- Render 대시보드 → Build/Release Command (마이그레이션·collectstatic 실행 지점),
  auto-deploy 대상 브랜치, Root Directory
  - 특히 빌드 명령이 `README.md` 나 `lifeDiary/docs/` 를 참조하지 않는지

### 남는 트레이드오프

배포가 수동이 되면 "머지는 됐는데 아무도 배포를 안 눌렀다"가 조용한 정상 상태로
보인다. 지금은 배포 PR 이 그 역할을 했다. 대기 상태 알림은 Deferred 로 둔다.

production 히스토리가 배포 단위 스냅샷이 되어 `git blame` 이 원래 커밋 대신 배포
커밋을 가리킨다. 커밋 메시지의 `main@<sha>` 를 따라 main 으로 가야 한다.
