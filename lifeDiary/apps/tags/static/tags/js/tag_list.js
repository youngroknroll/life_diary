/**
 * 태그 관리 목록.
 *
 * 카테고리로 묶은 행 리스트를 그린다. 카테고리 순서는 시스템이 정하고
 * 태그는 그 안에서 이름순이다 — 사용자가 손으로 정하는 순서는 두지 않는다.
 */
let categories = [];
let tags = [];
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
        // 모달이 카테고리 선택지와 옮길 태그 목록을 여기서 가져간다.
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
 * 들어가 있던 노드까지 전부 새로 만들어진다. 포커스를 들고 있던 노드도
 * 함께 사라진다.
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
    groupTags.forEach((tag) => group.appendChild(buildRow(tag)));
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

function buildRow(tag) {
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
    row.appendChild(buildActions(tag));
    return row;
}

function buildActions(tag) {
    const actions = document.createElement('div');
    actions.className = 'tag-row__actions';

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


/* 수정과 삭제 ------------------------------------------------------------ */

function handleRowClick(event) {
    const button = event.target.closest('button[data-tag-id]');
    if (!button) return;

    const tagId = Number(button.dataset.tagId);
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
