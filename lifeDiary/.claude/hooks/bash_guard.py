import json
import re
import subprocess
import sys

ENV = 'knou-life-diary'

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if d.get('tool_name') != 'Bash':
    sys.exit(0)

cmd = (d.get('tool_input') or {}).get('command') or ''
cwd = d.get('cwd') or None


def deny(reason):
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny',
            'permissionDecisionReason': '[bash-guard] ' + reason,
        }
    }, ensure_ascii=False))
    sys.exit(0)


def strip_heredocs(text):
    return re.sub(r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\1(\n|$)", '\n', text, flags=re.S)


def segments(text):
    out = []
    for part in re.split(r'\|\||&&|;|\||\n', strip_heredocs(text)):
        part = re.sub(r'^(?:\w+=\S*\s+)+', '', part.strip())
        if part:
            out.append(part)
    return out


def current_branch():
    try:
        r = subprocess.run(
            ['git', 'symbolic-ref', '--short', 'HEAD'],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else ''
    except Exception:
        return ''


GIT_PREFIX = r'^git\s+(?:-C\s+\S+\s+)?(?:-c\s+\S+\s+)*'
COMMIT_PUSH_MERGE = re.compile(GIT_PREFIX + r'(commit|push|merge)\b')
PUSH_TO_MAIN = re.compile(GIT_PREFIX + r'push\b.*(?:\s|:)main(?:\s|$)')
SWITCH_TO_MAIN = re.compile(GIT_PREFIX + r'(?:checkout|switch)\s+(?:-\S+\s+)*main(?:\s|$)')
GH_MERGE = re.compile(r'^gh\s+pr\s+merge\b')
TAG_CREATE = re.compile(GIT_PREFIX + r'tag\s+(?!-l\b|--list\b|-n\d*\b)')

CONDA_RUN = re.compile(r'^conda\s+run\b')
CONDA_ENV = re.compile(r'^conda\s+run\s+(?:-n|--name)\s+' + re.escape(ENV) + r'(?:\s|$)')
NEEDS_ENV = re.compile(
    r'^(?:python3?\s+(?:-m\s+)?)?(?:\./)?(?:pytest\b|manage\.py\b|django-admin\b)'
    r'|^python3?\s+-m\s+pip\s+install\b'
    r'|^pip3?\s+install\b'
    r'|^(?:source|\.)\s+\S*\.venv/'
    r'|^\S*\.venv/bin/'
    r'|^uv\s+(?:run|pip)\b'
)

segs = segments(cmd)

if any(GH_MERGE.match(s) for s in segs):
    deny('PR 머지는 사용자가 합니다. 머지 명령을 지우고 PR 링크만 보고하세요.')

if any(TAG_CREATE.match(s) for s in segs):
    deny('릴리스 태그는 사용자가 만듭니다. 태그 명령을 지우세요.')

if any(PUSH_TO_MAIN.match(s) for s in segs):
    deny('main 으로 push 하지 않습니다. 작업 브랜치를 push 하고 PR 을 여세요.')

if any(COMMIT_PUSH_MERGE.match(s) for s in segs):
    branch = current_branch()
    if branch == 'main' or any(SWITCH_TO_MAIN.match(s) for s in segs):
        deny('main 에서는 commit·push·merge 를 하지 않습니다. 작업 브랜치(feat/<track> 등)를 만들어 거기서 커밋하세요. main 머지는 사용자가 합니다.')

for s in segs:
    if CONDA_RUN.match(s):
        if not CONDA_ENV.match(s):
            deny('Python 은 conda env `' + ENV + '` 에서만 실행합니다: conda run -n ' + ENV + ' ...')
        continue
    if NEEDS_ENV.match(s):
        deny('pytest·manage.py·pip 은 `conda run -n ' + ENV + ' ...` 로 실행합니다. .venv·uv·시스템 Python 은 쓰지 않습니다.')

sys.exit(0)
