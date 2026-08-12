/**
 * 태그 관리 목록.
 *
 * 카테고리로 묶은 행 리스트를 그리고 행을 위아래로 옮긴다. 순서는 카테고리
 * 안에서만 움직인다 — 카테고리는 색이자 통계 분류라서, 순서를 바꾸는 동작이
 * 그것까지 건드리면 사용자가 지난달 통계가 달라진 이유를 알 수 없다.
 */
const ORDER_ENDPOINT = '/api/tags/order/';

let categories = [];
let tags = [];
// 마지막으로 서버가 받아 준 순서. 저장에 실패하면 여기로 되돌린다.
let confirmedIds = [];
let sending = false;
let dirty = false;
// 되돌릴 때 포커스를 돌려놓을 자리.
let lastMove = null;
// 모달을 연 버튼. 저장하면 목록을 다시 그리느라 그 버튼이 사라진다.
let pendingFocus = null;

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('tagListContainer');
    if (!container) return;

    container.addEventListener('click', handleRowClick);
    document.addEventListener('tags-updated', loadTags);

    // 모달이 닫히는 시점과 목록을 다시 그리는 시점은 순서가 정해져 있지
    // 않다. 어느 쪽이 나중이든 포커스를 되찾도록 양쪽에서 부른다.
    document.querySelectorAll('.modal').forEach(function (modal) {
        modal.addEventListener('hidden.bs.modal', repairFocus);
    });

    loadTags();
});


/* 목록 읽기 ------------------------------------------------------------- */

async function loadTags() {
    const container = document.getElementById('tagListContainer');
    try {
        const [tagsData, categoryData] = await Promise.all([
            apiCall('/api/tags/'),
            apiCall('/api/categories/'),
        ]);
        categories = categoryData.categories;
        tags = tagsData.tags;
        confirmedIds = tags.map((tag) => tag.id);
        // 모달이 카테고리 선택지를 여기서 가져간다.
        window._categories = categories;
        window._tagsCache = tags;
        render();
    } catch (error) {
        console.error(error);
        container.replaceChildren(errorNotice());
    }
}

function errorNotice() {
    const box = document.createElement('div');
    box.className = 'alert alert-danger';
    // 목록이 통째로 비는 실패다. 눈으로 보지 않으면 빈 화면과 구분되지 않는다.
    box.setAttribute('role', 'alert');
    box.textContent = gettext('태그를 불러오는 중 오류가 발생했습니다.');
    return box;
}


/* 그리기 ---------------------------------------------------------------- */

/**
 * 조각을 만들어 한 번에 갈아 끼운다.
 *
 * 예전 코드는 innerHTML 에 문자열을 더해 붙였는데, 그러면 붙일 때마다 이미
 * 들어가 있던 노드까지 전부 새로 만들어진다. 방금 누른 버튼이 사라지므로
 * 포커스가 문서 바닥으로 떨어지고, 연달아 두 칸을 옮길 수가 없다.
 */
function render() {
    const container = document.getElementById('tagListContainer');
    const emptyState = document.getElementById('tagEmptyState');

    if (!tags.length) {
        container.replaceChildren();
        emptyState.hidden = false;
        repairFocus();
        return;
    }
    emptyState.hidden = true;

    const fragment = document.createDocumentFragment();
    categories.forEach(function (category) {
        const mine = tags.filter((tag) => tag.category_id === category.id);
        if (mine.length) fragment.appendChild(buildGroup(category, mine));
    });
    container.replaceChildren(fragment);
    repairFocus();
}

function buildGroup(category, groupTags) {
    const group = document.createElement('section');
    group.className = 'tag-group';
    group.appendChild(buildGroupHeading(category, groupTags.length));

    groupTags.forEach(function (tag, position) {
        group.appendChild(
            buildRow(tag, category, position, position === groupTags.length - 1)
        );
    });
    return group;
}

function buildGroupHeading(category, count) {
    const heading = document.createElement('h2');
    heading.className = 'tag-group__heading';

    // 색 상자를 붙이지 않는다. 2026-05-24 에 카테고리 머리글은 기록 화면과
    // 여기가 같은 `- 카테고리명` 으로 통일됐고, 여기만 되살리면 다시 갈린다.
    const name = document.createElement('span');
    name.textContent = `- ${category.name}`;
    heading.appendChild(name);

    const badge = document.createElement('span');
    badge.className = 'tag-group__count num';
    badge.textContent = `(${count})`;
    heading.appendChild(badge);

    return heading;
}

function buildRow(tag, category, position, isLast) {
    const row = document.createElement('div');
    row.className = 'settings-row tag-row';
    row.dataset.tagRow = tag.id;

    const info = document.createElement('div');
    info.className = 'tag-row__info';

    const name = document.createElement('span');
    name.className = 'tag-row__name';
    name.textContent = tag.name;
    info.appendChild(name);

    const meta = document.createElement('span');
    meta.className = 'tag-row__meta num';
    meta.textContent = tag.block_count
        ? interpolate(gettext('누적 %s시간'), [tag.total_hours])
        : gettext('아직 기록 없음');
    info.appendChild(meta);

    row.appendChild(info);
    row.appendChild(buildActions(tag, category, position === 0, isLast));
    return row;
}

function buildActions(tag, category, isFirst, isLast) {
    const actions = document.createElement('div');
    actions.className = 'tag-row__actions';

    actions.appendChild(moveButton(tag, category, 'up', isFirst));
    actions.appendChild(moveButton(tag, category, 'down', isLast));
    actions.appendChild(
        actionButton(tag, 'edit', gettext('수정'), 'fa-pen',
            interpolate(gettext('%s 태그 수정'), [tag.name]))
    );
    actions.appendChild(
        actionButton(tag, 'delete', gettext('삭제'), 'fa-trash',
            interpolate(gettext('%s 태그 삭제'), [tag.name]))
    );
    return actions;
}

function moveButton(tag, category, direction, atEdge) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn-sian btn-sian--icon';
    button.dataset.tagId = tag.id;
    button.dataset.move = direction;
    // 카테고리 안에서의 처음과 끝이다. 목록 전체의 처음과 끝이 아니다.
    button.disabled = atEdge;
    button.setAttribute(
        'aria-label',
        interpolate(
            direction === 'up'
                ? gettext('%(tag)s 위로 이동, %(category)s 안에서')
                : gettext('%(tag)s 아래로 이동, %(category)s 안에서'),
            { tag: tag.name, category: category.name },
            true
        )
    );

    const icon = document.createElement('i');
    icon.className = `fas ${direction === 'up' ? 'fa-arrow-up' : 'fa-arrow-down'}`;
    icon.setAttribute('aria-hidden', 'true');
    button.appendChild(icon);
    return button;
}

function actionButton(tag, action, label, iconName, accessibleName) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn-sian btn-sian--compact';
    if (action === 'delete') button.classList.add('btn-sian--danger');
    button.dataset.tagId = tag.id;
    button.dataset.action = action;
    // 보이는 글자가 행마다 똑같아서 "수정, 삭제, 수정, 삭제"로만 읽힌다.
    button.setAttribute('aria-label', accessibleName);

    const icon = document.createElement('i');
    icon.className = `fas ${iconName} d-none d-md-inline`;
    icon.setAttribute('aria-hidden', 'true');
    button.appendChild(icon);

    const text = document.createElement('span');
    text.textContent = label;
    button.appendChild(text);
    return button;
}


/* 순서 바꾸기 ------------------------------------------------------------ */

function handleRowClick(event) {
    const button = event.target.closest('button[data-tag-id]');
    if (!button) return;

    const tagId = Number(button.dataset.tagId);
    if (button.dataset.move) {
        moveTag(tagId, button.dataset.move);
        return;
    }
    pendingFocus = { tagId: tagId, action: button.dataset.action };

    if (button.dataset.action === 'edit') {
        const tag = tags.find((item) => item.id === tagId);
        if (tag) window.openTagFormModal(tag);
        return;
    }
    if (button.dataset.action === 'delete') window.deleteTag(tagId);
}

/**
 * 모달을 연 버튼으로 포커스를 돌려놓는다.
 *
 * 저장이 끝나면 목록을 통째로 다시 그리므로 모달이 기억해 둔 버튼은 이미
 * 문서에서 떨어져 나갔다. 그 버튼에 포커스를 주려는 시도는 조용히 실패하고
 * 포커스는 문서 바닥에 남는다 — 키보드 사용자는 처음부터 다시 탭해야 한다.
 * 지운 태그처럼 돌아갈 행이 없으면 `새 태그` 로 보낸다.
 */
function repairFocus() {
    if (!pendingFocus) return;
    if (document.querySelector('.modal.show')) return;

    const row = document.querySelector(`[data-tag-row="${pendingFocus.tagId}"]`);
    const target =
        (row && row.querySelector(`[data-action="${pendingFocus.action}"]`)) ||
        document.querySelector('.page-head .btn-sian--primary');

    pendingFocus = null;
    if (target) target.focus();
}

function moveTag(tagId, direction) {
    const from = tags.findIndex((tag) => tag.id === tagId);
    if (from < 0) return;

    const to = direction === 'up' ? from - 1 : from + 1;
    const neighbour = tags[to];

    // 카테고리가 다르면 이웃이 아니다. 목록은 카테고리 순으로 오므로 같은
    // 카테고리의 태그끼리는 서로 붙어 있다.
    if (!neighbour || neighbour.category_id !== tags[from].category_id) return;

    const next = tags.slice();
    next[to] = next[from];
    next[from] = neighbour;
    tags = next;
    lastMove = { tagId: tagId, direction: direction };

    render();
    announceMove(tagId);
    focusMoveButton(tagId, direction);
    flushOrder();
}

function announceMove(tagId) {
    const status = document.getElementById('tagOrderStatus');
    if (!status) return;

    const tag = tags.find((item) => item.id === tagId);
    const peers = tags.filter((item) => item.category_id === tag.category_id);
    const category = categories.find((item) => item.id === tag.category_id);

    // 덮어쓴다. 빠르게 여러 번 누르면 중간 상태를 다 읽는 대신 마지막 자리만
    // 읽힌다.
    status.textContent = interpolate(
        gettext('%(tag)s, %(category)s의 %(position)s번째'),
        {
            tag: tag.name,
            category: category ? category.name : '',
            position: peers.indexOf(tag) + 1,
        },
        true
    );
}

/**
 * 옮긴 태그를 따라간다.
 *
 * 행이 자리를 바꾸면 방금 누른 버튼은 화면의 다른 곳에 있다. 같은 방향
 * 버튼이 이제 끝이라 눌리지 않으면 반대 방향으로, 그것도 없으면 수정으로
 * 옮긴다. 아무 데도 못 가면 포커스가 문서 바닥으로 떨어진다.
 */
function focusMoveButton(tagId, direction) {
    const row = document.querySelector(`[data-tag-row="${tagId}"]`);
    if (!row) return;

    const other = direction === 'up' ? 'down' : 'up';
    const target =
        enabled(row.querySelector(`[data-move="${direction}"]`)) ||
        enabled(row.querySelector(`[data-move="${other}"]`)) ||
        row.querySelector('[data-action="edit"]');
    if (target) target.focus();
}

function enabled(button) {
    return button && !button.disabled ? button : null;
}

/**
 * 순서를 서버에 맡긴다.
 *
 * 보내는 것은 목록 전체라 나중 요청이 앞선 요청을 온전히 덮어쓴다. 이미
 * 보내는 중이면 표시만 해 두었다가 끝난 뒤 최신 순서로 한 번 더 보낸다 —
 * 빠르게 여러 번 누를 때 오래된 응답이 새 순서를 되돌리지 않게 한다.
 */
async function flushOrder() {
    if (sending) {
        dirty = true;
        return;
    }

    sending = true;
    const attempt = tags.map((tag) => tag.id);
    try {
        await apiCall(ORDER_ENDPOINT, {
            method: 'PATCH',
            data: { tag_ids: attempt },
            showLoading: false,
        });
        confirmedIds = attempt;
    } catch (error) {
        // 기다리던 다음 이동까지 함께 되돌아간다. 한 번 실패했다고만 말하면
        // 두 번 눌렀던 사람은 한 칸은 남았으리라 믿게 된다.
        dirty = false;
        rollbackOrder();
        showNotification(
            interpolate(
                gettext('순서를 저장하지 못해 되돌렸습니다: %s'),
                [error.message]
            ),
            'error'
        );
        return;
    } finally {
        sending = false;
    }

    if (dirty) {
        dirty = false;
        flushOrder();
    }
}

function rollbackOrder() {
    const byId = new Map(tags.map((tag) => [tag.id, tag]));
    tags = confirmedIds.map((id) => byId.get(id)).filter(Boolean);
    render();
    // 화면을 다시 그리면 누른 버튼이 사라진다. 되돌아온 자리에서 다시 잡아
    // 준다 — 실패했다고 포커스까지 잃으면 키보드로는 다시 시도할 수 없다.
    if (lastMove) focusMoveButton(lastMove.tagId, lastMove.direction);
}
