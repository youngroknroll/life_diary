import sys, json, os, re

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = d.get('tool_name') or ''
ti = d.get('tool_input') or {}

def deny(reason):
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny',
            'permissionDecisionReason': '[changelog-defer-guard] ' + reason,
        }
    }, ensure_ascii=False))
    sys.exit(0)

if tool == 'Bash':
    cmd = ti.get('command') or ''
    if 'CHANGELOG.md' not in cmd:
        sys.exit(0)
    WRITE = re.compile(r'(>>?\s*\S*CHANGELOG\.md|sed\s+-i|python3?\b|tee\s|write_text|open\(|\bcp\s|\bmv\s|perl\s+-[pi]|awk\s.*>\s)')
    bodies = []

    def stash(m):
        bodies.append(m.group(0))
        return ' __HEREDOC%d__ ' % (len(bodies) - 1)

    stashed = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\1(\n|$)", stash, cmd, flags=re.S)
    for segment in re.split(r'\|\||&&|;|\||\n', stashed):
        with_bodies = re.sub(r'__HEREDOC(\d+)__', lambda m: bodies[int(m.group(1))], segment)
        if 'CHANGELOG.md' in with_bodies and WRITE.search(segment):
            deny('docs/CHANGELOG.md 는 Bash 로 고치지 말고 Edit/Write 도구로 고치세요. 미해결 절에 결함을 넣는 편집은 훅이 검사합니다.')
    sys.exit(0)

fp = ti.get('file_path') or ''
if not fp.endswith('docs/CHANGELOG.md'):
    sys.exit(0)

HEADER = '## 미해결'
existing = ''
if os.path.exists(fp):
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            existing = f.read()
    except Exception:
        existing = ''

def section(text):
    return text.split(HEADER, 1)[1] if HEADER in text else ''

added = []
if tool == 'Write':
    before = set(section(existing).splitlines())
    added = [l for l in section(ti.get('content') or '').splitlines() if l not in before]
else:
    edits = ti.get('edits') or [{'old_string': ti.get('old_string', ''), 'new_string': ti.get('new_string', '')}]
    sec_at = existing.find(HEADER)
    for e in edits:
        old = e.get('old_string') or ''
        new = e.get('new_string') or ''
        idx = existing.find(old) if old else -1
        in_section = (sec_at >= 0 and idx >= sec_at) or (HEADER in new)
        if not in_section:
            continue
        old_lines = set(old.splitlines())
        added += [l for l in new.splitlines() if l not in old_lines]

DEFECT = re.compile(
    r'(결함|버그|회귀|깨[지진짐져]|틀린|잘못|누락|고장|오류|실패|없음|없다|부재|미구현|미적용|안\s*됨|되지\s*않|불가|못함|못\s*함'
    r'|bug|defect|regression|broken|missing|fails?\b|error)',
    re.IGNORECASE,
)
APPROVED = re.compile(r'사용자\s*승인')
SKIP = re.compile(r'^\s*(#|\||$)')

flagged = [l for l in added if not SKIP.match(l) and DEFECT.search(l) and not APPROVED.search(l)]
if flagged:
    sample = flagged[0].strip()
    if len(sample) > 140:
        sample = sample[:140] + '…'
    deny(
        '미해결 절에 결함성 항목을 넣으려 합니다: "' + sample + '". '
        '진행 중 발견한 결함은 미루지 말고 이 작업 안에서 고치세요. 고칠 수 없는 이유가 있으면 AskUserQuestion으로 사용자에게 미룰지 묻고, '
        '승인받은 항목만 줄 끝에 "(사용자 승인 YYYY-MM-DD)" 를 붙여 적으세요.'
    )
sys.exit(0)
