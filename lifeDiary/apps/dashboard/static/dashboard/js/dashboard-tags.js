// ── 태그 로딩/렌더링 ──

async function loadAvailableTags() {
    try {
        const result = await apiCall('/api/tags/');
        renderTagContainer(result.tags);
        renderTagLegend(result.tags);
    } catch (error) {
        showTagError(gettext('태그 로드 중 오류가 발생했습니다.'));
    }
}

function renderTagButton(tag) {
    const safeName = escapeHtml(tag.name);
    const safeColor = escapeHtml(tag.color);
    return `
        <button type="button" class="tag-btn chip chip--pick"
                data-tag-id="${tag.id}"
                data-tag-color="${safeColor}"
                data-tag-name="${safeName}">
            <span class="chip__swatch" style="background-color: ${safeColor}"></span>${safeName}
        </button>`;
}

function renderCategoryHeader(categoryName, categoryCount = null) {
    const template = document.getElementById('tagCategoryHeaderTemplate');
    const safeName = escapeHtml(categoryName);
    if (!template || !template.content || !template.content.firstElementChild) {
        const countHtml = categoryCount === null ? '' :
            `<small class="text-muted ms-1">(${categoryCount})</small>`;
        return `<div class="tag-category-header small text-muted fw-bold mt-2 mb-1">- ${safeName}${countHtml}</div>`;
    }

    const header = template.content.firstElementChild.cloneNode(true);
    const nameEl = header.querySelector('[data-tag-category-name]');
    const countEl = header.querySelector('[data-tag-category-count]');
    if (nameEl) nameEl.textContent = `- ${categoryName}`;
    if (countEl) {
        if (categoryCount === null) {
            countEl.remove();
        } else {
            countEl.classList.remove('d-none');
            countEl.textContent = `(${categoryCount})`;
        }
    }

    return header.outerHTML;
}

function renderTagContainer(tags) {
    const tagContainer = document.getElementById('tagContainer');
    if (tags.length === 0) {
        const emptyText = gettext('태그가 없습니다. 아래에서 추가하세요.');
        tagContainer.innerHTML = `<p class="quick-input-sheet__empty-tags">${emptyText}</p>`;
        return;
    }

    const categories = window._categories || [];
    // 카테고리 메타가 아직 로드되지 않았으면 flat 폴백
    if (categories.length === 0) {
        tagContainer.innerHTML = `<div class="quick-input-tag-list">${tags.map(renderTagButton).join('')}</div>`;
        return;
    }

    const byCategory = new Map();
    for (const tag of tags) {
        const key = tag.category_id;
        if (!byCategory.has(key)) byCategory.set(key, []);
        byCategory.get(key).push(tag);
    }

    const sorted = [...categories].sort(
        (a, b) => a.display_order - b.display_order
    );

    tagContainer.innerHTML = sorted
        .filter(cat => byCategory.has(cat.id))
        .map(cat => `
            <div class="tag-category-group">
                ${renderCategoryHeader(cat.name)}
                <div class="quick-input-tag-list">
                    ${byCategory.get(cat.id).map(renderTagButton).join('')}
                </div>
            </div>
        `).join('');
}

function renderTagLegend(tags) {
    const tagLegend = document.getElementById('tagLegend');
    if (tags.length === 0) {
        tagLegend.innerHTML = `<small class="text-muted">${gettext('생성된 태그가 없습니다.')}</small>`;
        return;
    }
    tagLegend.innerHTML = tags.map(tag => {
        const textColor = getContrastTextColor(tag.color);
        return `
        <button type="button" class="badge btn-tag-legend"
                data-tag-id="${tag.id}"
                data-tag-color="${escapeHtml(tag.color)}"
                data-tag-name="${escapeHtml(tag.name)}"
                style="background-color: ${escapeHtml(tag.color)}; color: ${textColor}; border: 0;">${escapeHtml(tag.name)}</button>`;
    }).join('');
}

function showTagError(message) {
    const tagContainer = document.getElementById('tagContainer');
    tagContainer.innerHTML = `<div class="alert alert-danger p-2 small">${message}</div>`;
}
