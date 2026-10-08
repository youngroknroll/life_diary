import sys, json, os, re

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if d.get('stop_hook_active'):
    sys.exit(0)

path = d.get('transcript_path') or ''
if not path or not os.path.exists(path):
    sys.exit(0)

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[-3000:]
except Exception:
    sys.exit(0)

texts = []
for line in reversed(lines):
    try:
        e = json.loads(line)
    except Exception:
        continue
    kind = e.get('type')
    if kind == 'user':
        content = (e.get('message') or {}).get('content')
        if isinstance(content, list) and content and all(
            isinstance(c, dict) and c.get('type') == 'tool_result' for c in content
        ):
            continue
        break
    if kind == 'assistant' and not e.get('isSidechain'):
        content = (e.get('message') or {}).get('content') or []
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text' and c.get('text'):
                    texts.append(c['text'])

text = '\n'.join(reversed(texts))
if not text.strip():
    sys.exit(0)

DEFER = re.compile(
    r'(미뤘|미룬|미루|보류|범위\s*밖|다음\s*(작업|라운드|세션|기회|트랙)|나중에|별도\s*(작업|트랙|PR|세션)'
    r'|남겨\s*(둔|뒀|둡|두)|남은\s*일|남은\s*위험|후속|잔여|deferred|defer|follow-?up|out of scope|later)',
    re.IGNORECASE,
)
DEFECT = re.compile(
    r'(결함|버그|회귀|깨[지진짐져]|틀린|틀렸|잘못|누락|고장|동작하지\s*않|작동하지\s*않|되지\s*않|안\s*됨|bug|defect|regression|broken)',
    re.IGNORECASE,
)
EXCLUDE = re.compile(
    r'(결함\s*0건|결함\s*없|결함이\s*없|버그\s*없|사용자\s*승인|사용자가\s*(보류|미루|미뤄|결정|선택)|승인받|승인\s*받|미루지\s*(않|말)|미루지말|보류하지|훅|규칙)',
)

sentences = []
for block in re.split(r'\n+', text):
    for s in re.split(r'(?<=다\.)\s+|(?<=\.)\s+(?=[A-Z가-힣])', block):
        s = s.strip()
        if s:
            sentences.append(s)

hits = [s for s in sentences if DEFER.search(s) and DEFECT.search(s) and not EXCLUDE.search(s)]
if not hits:
    sys.exit(0)

sample = hits[0]
if len(sample) > 160:
    sample = sample[:160] + '…'

reason = (
    '[defect-deferral-guard] 발견한 결함을 다음으로 미루는 문장이 응답에 있습니다: "' + sample + '". '
    '규칙: 진행 중 발견한 결함은 이 작업 안에서 고친다. 지금 고치고, 검증 명령을 다시 돌린 뒤, 고친 내용을 포함해 다시 보고하세요. '
    '정말 이 작업에서 고칠 수 없다면(다른 화면·설계 결정·사용자 판단이 필요하면) 추측하지 말고 AskUserQuestion으로 사용자에게 미룰지 물어보세요. '
    '사용자가 미루기로 답한 항목만 "사용자 승인"이라고 명시해 보고하고, CHANGELOG 미해결에도 같은 표기로 적으세요.'
)
print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
