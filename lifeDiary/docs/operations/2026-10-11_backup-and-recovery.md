# 백업과 복구 절차

작성 2026-10-11. 운영 DB는 Supabase PostgreSQL(Render 웹 서비스가 transaction pooler 6543 으로 접속)이다.
이 문서가 생기기 전에는 백업 정책이 어디에도 적혀 있지 않았다.

## 지금 기대할 수 있는 것

- Supabase 공식 문서(https://supabase.com/docs/guides/platform/backups)는 Free·Pro·Team·Enterprise 프로젝트를 매일 백업한다고 적는다. 보관 기간은 Pro 7일, Team 14일, Enterprise 30일이고 Free 는 기간이 명시되어 있지 않다. Free 프로젝트에는 CLI `db dump` 로 정기 수출해 외부에 보관하라고 권한다.
- 시점 복구(PITR)는 유료 애드온이다. 지금 플랜에서는 일 단위 스냅샷이 복구 단위다.
- 따라서 지금의 복구 목표는 **RPO 24시간, RTO 1시간**으로 둔다. 더 짧게 가려면 플랜·애드온 결정이 필요하고 그 결정은 사용자 몫이다.

확인할 것(사용자): Supabase 대시보드 Database → Backups 에서 현재 플랜의 백업 목록이 실제로 보이는지. 보이지 않으면 아래 수동 덤프를 즉시 한 번 뜬다.

## 수동 덤프 (주 1회, 배포 전 1회)

transaction pooler(6543)는 `pg_dump` 가 쓰는 세션 기능을 지원하지 않는다. 대시보드 Connect 에서 **session pooler(5432)** 또는 direct 연결 문자열을 쓴다.

```bash
pg_dump "$SUPABASE_SESSION_URL" \
  --format=custom --no-owner --no-privileges \
  --schema=public \
  --file="lifediary-$(date +%Y%m%d-%H%M).dump"
```

- 결과 파일은 개인정보(이메일, 기록)를 담는다. 저장소나 GitHub Artifacts 에 올리지 않는다. 로컬 암호화 볼륨이나 개인 클라우드의 비공개 폴더에 두고, 30일 지난 파일은 지운다.
- `--schema=public` 으로 Supabase 내부 스키마(auth, storage 등)를 뺀다. Django 가 쓰는 테이블은 모두 public 에 있다.
- `auth_user`, `dashboard_timeblock`, `tags_*`, `users_*`, `axes_*`, `django_migrations` 가 들어 있는지 `pg_restore --list` 로 확인한다.

## 자동 덤프 (GitHub Actions, 매일 04:17 KST)

`.github/workflows/db-backup.yml` 이 매일 `pg_dump` 를 떠서 age 로 암호화한 뒤 Actions 아티팩트에 30일 보관한다. 평문은 러너 메모리 밖으로 나가지 않는다. DB 접속은 purge 워크플로가 매일 쓰는 저장소 secrets(`DB_USER`·`DB_PASSWORD`·`DB_HOST`·`DB_NAME`)를 그대로 쓰고, 같은 풀러 호스트에 세션 모드(5432)로 붙는다. 로컬 `.env` 의 값은 운영 비밀번호와 다르므로 쓰지 않는다.

추가로 필요한 secret 은 하나다.

| secret | 값 | 상태 |
|---|---|---|
| `BACKUP_AGE_RECIPIENT` | `ssh-ed25519 AAAA...` 공개키(또는 `age1...` 공개키) | 2026-10-11 등록. 비밀키 `~/.ssh/lifediary_backup_ed25519` |

`age` 는 SSH ed25519 공개키를 수신자로 받으므로 `age-keygen` 없이 `ssh-keygen` 으로 만들었다. **비밀키 `~/.ssh/lifediary_backup_ed25519` 를 암호 관리자에 복사해 둔다.** 이 파일이 없으면 아티팩트를 풀 수 없다. 키를 새로 만들어야 하면:

```bash
ssh-keygen -q -t ed25519 -N "" -C "lifediary-db-backup" -f ~/.ssh/lifediary_backup_ed25519
gh secret set BACKUP_AGE_RECIPIENT --body "$(cut -d' ' -f1,2 ~/.ssh/lifediary_backup_ed25519.pub)"
```

복호화: 아티팩트를 내려받아 `age -d -i ~/.ssh/lifediary_backup_ed25519 <파일>.dump.age > restore.dump`. 그 뒤는 아래 복구 리허설과 같다. 수동 실행은 Actions 탭의 `database backup` → Run workflow.

## 복구 리허설 (분기 1회, 또는 마이그레이션이 테이블을 지우기 전)

1. 로컬 PostgreSQL 에 빈 DB 를 만든다.
   ```bash
   createdb lifediary_restore
   pg_restore --clean --if-exists --no-owner --no-privileges \
     -d lifediary_restore lifediary-YYYYMMDD-HHMM.dump
   ```
2. prod 설정으로 복구본을 가리키고 상태를 확인한다. `DB_HOST=localhost DB_PORT=5432 DB_NAME=lifediary_restore` 를 환경에 넣고 다음을 돈다.
   ```bash
   conda run -n knou-life-diary python manage.py migrate --check --settings=lifeDiary.settings.prod
   conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod
   ```
3. 행 수를 원본과 맞춘다. `SELECT count(*) FROM auth_user;`, `SELECT count(*), max(date) FROM dashboard_timeblock;` 두 값이 덤프 시각의 원본과 같아야 한다.
4. 걸린 시간을 아래 표에 적는다. RTO 1시간을 넘기면 절차를 고친다.

| 날짜 | 덤프 크기 | 복구 소요 | 행 수 일치 | 비고 |
|---|---|---|---|---|
| | | | | |

## 실제 장애 때 순서

1. Render 서비스를 일시 중지해 쓰기를 멈춘다(복구 중 새 기록이 덮이지 않게).
2. Supabase 대시보드 백업으로 복구하거나, 가장 최근 수동 덤프를 위 절차로 새 프로젝트에 올린다.
3. `DB_HOST`·`DB_PASSWORD` 가 바뀌었으면 Render 환경변수를 바꾸고 재배포한다.
4. 로그인 → 오늘 기록 저장 → 통계 화면 순으로 확인한다. 통계 캐시는 `/tmp` 파일이라 재배포로 비워진다.
5. 변경 기록에 날짜·원인·복구 지점·유실 범위를 적는다.

## 데스크톱 빌드

SQLite 파일은 사용자 데이터 폴더(macOS `~/Library/Application Support/LifeDiary/db.sqlite3`)에 있다. 앱이 꺼진 상태에서 파일을 복사하는 것이 백업이다. 앱 안의 자동 백업은 배포 계획 문서의 3B 단계에 있다.

## 남은 결정 (사용자)

- 플랜 업그레이드 또는 PITR 애드온 여부. 자동 덤프가 켜져 있으면 RPO 24시간은 플랜과 무관하게 지켜진다.
- `BACKUP_DATABASE_URL`·`BACKUP_AGE_RECIPIENT` secrets 등록(위 표).
