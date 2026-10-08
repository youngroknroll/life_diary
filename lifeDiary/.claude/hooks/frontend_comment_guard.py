import json
import os
import re
import sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = d.get('tool_name') or ''
ti = d.get('tool_input') or {}
if tool not in ('Edit', 'Write', 'MultiEdit'):
    sys.exit(0)

fp = (ti.get('file_path') or '').replace('\\', '/')
if not re.search(r'/(templates|static)/', fp):
    sys.exit(0)

ext = os.path.splitext(fp)[1].lower()
PATTERNS = {
    '.html': re.compile(r'\{#|<!--|^\s*//'),
    '.css': re.compile(r'/\*'),
    '.js': re.compile(r'/\*|^\s*//|\s//\s'),
}
pattern = PATTERNS.get(ext)
if pattern is None:
    sys.exit(0)

existing = ''
if os.path.exists(fp):
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            existing = f.read()
    except Exception:
        existing = ''

if tool == 'Write':
    before = set(existing.splitlines())
    added = [l for l in (ti.get('content') or '').splitlines() if l not in before]
else:
    edits = ti.get('edits') or [{'old_string': ti.get('old_string', ''), 'new_string': ti.get('new_string', '')}]
    added = []
    for e in edits:
        old_lines = set((e.get('old_string') or '').splitlines())
        added += [l for l in (e.get('new_string') or '').splitlines() if l not in old_lines]

APPROVED = re.compile(r'사용자\s*승인')
flagged = [l for l in added if pattern.search(l) and not APPROVED.search(l)]
if not flagged:
    sys.exit(0)

sample = flagged[0].strip()
if len(sample) > 120:
    sample = sample[:120] + '…'
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': (
            '[frontend-comment-guard] 템플릿·CSS·브라우저 JS 에 주석을 넣으려 합니다: "' + sample + '". '
            '규칙: 프런트엔드 코드는 주석 없이 이름과 구조로 뜻을 드러낸다 (여러 줄 `{# #}` 는 화면에 그대로 찍힌다). '
            '주석을 지우고 이름·구조로 다시 쓰세요. 꼭 필요하면 AskUserQuestion 으로 사용자 승인을 받고 그 줄에 "(사용자 승인 YYYY-MM-DD)" 를 적으세요.'
        ),
    }
}, ensure_ascii=False))
sys.exit(0)
