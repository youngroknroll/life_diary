# Home Main UI Design

## Goal

Change the home page from a generic feature landing page into a simple app home centered on this value: "단순하게 하루를 기록한다."

## Direction

The first screen should feel like an entry point to a daily recording habit, not a technical time-grid demo. The primary copy should avoid overemphasizing 10-minute slots. The page may still hint at color-blocked daily records because that is part of the product, but the user-facing message should be about easy daily reflection and lightweight recording.

## Page Structure

1. Hero section
   - Headline: "하루를 단순하게 기록하세요"
   - Supporting copy: "활동을 고르고, 오늘의 흐름을 남기고, 나중에 돌아봅니다."
   - Authenticated CTA: "오늘 기록하기"
   - Anonymous CTA: "로그인하고 기록 시작"
   - Optional secondary CTA for anonymous users: "회원가입"
   - Optional admin CTA for superusers

2. Daily preview panel
   - A non-data preview that shows simple colored blocks and a short daily note.
   - This preview must not imply it is live user data.
   - The visual focus is "a simple day record", not "10-minute precision".

3. Feature section
   - Replace technical wording with low-friction user wording.
   - Suggested cards:
     - "기록하기": 오늘 한 일을 가볍게 남깁니다.
     - "정리하기": 태그로 하루의 흐름을 구분합니다.
     - "돌아보기": 쌓인 기록에서 생활 패턴을 확인합니다.

4. Authenticated nudge
   - Keep a compact signed-in prompt near the bottom.
   - Message should invite the user to continue today's record.

## Constraints

- Keep the Django template structure and existing URL names.
- Prefer Bootstrap utilities and small page-scoped CSS over broad global changes.
- Do not modify unrelated docs changes already present in the worktree.
- Keep responsive layout stable on mobile and desktop.
- Preserve current login/admin branching behavior.
