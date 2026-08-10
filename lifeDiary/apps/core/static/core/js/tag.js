/**
 * =================================================================================
 * 태그 관리 공통 JavaScript
 * - 이 스크립트는 _tag_modal.html과 함께 사용되어야 합니다.
 * - 태그 폼 모달을 열고, 태그를 생성/수정/삭제하는 API를 호출합니다.
 * - 작업 성공 시 'tags-updated' 커스텀 이벤트를 발생시켜 각 페이지에서
 *   태그 목록을 새로고침하도록 합니다.
 * - core/utils.js의 apiCall과 showNotification 함수를 사용합니다.
 * =================================================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    const tagFormModalEl = document.getElementById('tagFormModal');
    if (!tagFormModalEl) return; // 모달이 없는 페이지에서는 실행하지 않음

    const tagFormModal = new bootstrap.Modal(tagFormModalEl);

    // 모달을 data-bs-toggle 이 아니라 JS 로 열기 때문에 Bootstrap 이 트리거를
    // 모른다. 닫을 때 포커스를 직접 돌려주지 않으면 body 로 떨어진다.
    let modalOpener = null;
    tagFormModalEl.addEventListener('hidden.bs.modal', function () {
        if (modalOpener && document.contains(modalOpener)) {
            modalOpener.focus();
        }
        modalOpener = null;
    });
    
    const colorPicker = document.getElementById('tagFormColor');
    const colorText = document.getElementById('tagFormColorText');
    const colorSwatch = document.getElementById('tagFormColorSwatch');

    /** 색은 카테고리가 정한다. 사용자가 고르면 같은 카테고리끼리 묶여
        읽히는 규칙이 깨지므로 미리보기만 보여 준다. */
    function syncTagColorInputs(color) {
        if (!/^#[0-9a-fA-F]{6}$/.test(color || '')) return;
        if (colorPicker) colorPicker.value = color;
        if (colorText) colorText.value = color;
        if (colorSwatch) colorSwatch.style.backgroundColor = color;
    }

    // 시안 7b 의 카테고리별 한 줄 설명. 7a 의 전체 설명과 달리 고르는 자리에서
    // 읽는 짧은 꼬리표다.
    const CATEGORY_HINTS = {
        investment: gettext('목표 영역'),
        proactive: gettext('계획 안'),
        passive: gettext('계획 밖'),
        basic_life: gettext('준비 · 이동'),
        sleep: gettext('잠 · 낮잠')
    };

    function chosenCategory() {
        const picked = document.querySelector('input[name="tagFormCategory"]:checked');
        if (!picked || !window._categories) return null;
        return window._categories.find(cat => String(cat.id) === picked.value) || null;
    }

    function updatePreview() {
        const category = chosenCategory();
        const nameInput = document.getElementById('tagFormName');
        const previewName = document.getElementById('tagFormPreviewName');
        const note = document.getElementById('tagFormColorNote');

        if (previewName) {
            previewName.textContent = (nameInput && nameInput.value.trim()) || gettext('새 태그');
        }
        if (category) {
            syncTagColorInputs(category.color);
        }
        if (note) {
            note.textContent = category
                ? interpolate(gettext('%s 색으로 저장됩니다. 같은 카테고리 태그와 한 덩어리로 보입니다.'), [category.name])
                : gettext('카테고리를 고르면 색이 정해집니다.');
        }
    }

    // 카테고리 선택지 — 네이티브 라디오라 방향키 이동과 탭 정지 하나를
    // 브라우저가 처리한다. div 로 흉내 내면 둘 다 직접 만들어야 한다.
    function populateCategorySelect(selectedCategoryId) {
        const host = document.getElementById('tagFormCategoryOptions');
        if (!host || !window._categories) return;
        host.innerHTML = '';

        window._categories.forEach(cat => {
            const id = `tagFormCategory_${cat.id}`;
            const label = document.createElement('label');
            label.className = 'category-picker__option';
            label.setAttribute('for', id);

            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'tagFormCategory';
            input.id = id;
            input.value = cat.id;
            input.required = true;
            input.className = 'category-picker__radio';
            if (selectedCategoryId && cat.id === selectedCategoryId) {
                input.checked = true;
            }
            input.addEventListener('change', updatePreview);

            const swatch = document.createElement('span');
            swatch.className = 'category-picker__swatch';
            swatch.style.backgroundColor = cat.color;

            const name = document.createElement('span');
            name.className = 'category-picker__name';
            name.textContent = cat.name;

            const hint = document.createElement('span');
            hint.className = 'category-picker__hint';
            hint.textContent = CATEGORY_HINTS[cat.slug] || '';

            label.append(input, swatch, name, hint);
            host.appendChild(label);
        });

        updatePreview();
    }

    const nameInputEl = document.getElementById('tagFormName');
    if (nameInputEl) nameInputEl.addEventListener('input', updatePreview);

    // 전역 함수로 모달 열기 함수 등록
    window.openTagFormModal = function(tag = null) {
        // 카테고리가 아직 안 왔으면 라디오가 빈 채로 열린다. 고를 것이 없는
        // 모달을 여느니 기다리라고 말한다.
        if (!window._categories || !window._categories.length) {
            showNotification(gettext('카테고리를 불러오는 중입니다. 잠시 후 다시 눌러주세요.'), 'warning');
            return;
        }
        const form = document.getElementById('tagForm');
        form.reset();
        
        const titleEl = document.getElementById('tagFormModalTitle');
        const tagIdInput = document.getElementById('tagFormTagId');
        const nameInput = document.getElementById('tagFormName');
        const colorInput = document.getElementById('tagFormColor');
        const colorTextInput = document.getElementById('tagFormColorText');
        const isDefaultCheckbox = document.getElementById('tagFormIsDefault');
        const saveLabel = document.getElementById('saveTagFormBtn');

        if (tag) {
            // 태그 수정
            titleEl.textContent = gettext('태그 수정');
            if (saveLabel) saveLabel.textContent = gettext('저장');
            tagIdInput.value = tag.id;
            nameInput.value = tag.name;
            colorInput.value = tag.color;
            colorTextInput.value = tag.color; // 텍스트 필드 값도 설정
            populateCategorySelect(tag.category_id);
            if (isDefaultCheckbox) {
                isDefaultCheckbox.checked = tag.is_default || false;
            }
        } else {
            // 새 태그 생성
            titleEl.textContent = gettext('새 태그');
            if (saveLabel) saveLabel.textContent = gettext('태그 만들기');
            tagIdInput.value = '';
            colorInput.value = '';
            colorTextInput.value = '';
            populateCategorySelect(null);
            if (isDefaultCheckbox) {
                isDefaultCheckbox.checked = false;
            }
        }
        
        modalOpener = document.activeElement;
        tagFormModal.show();
    };

    // 저장 버튼 클릭 이벤트 (core utils 사용)
    document.getElementById('saveTagFormBtn').addEventListener('click', async function() {
        const tagId = document.getElementById('tagFormTagId').value;
        const name = document.getElementById('tagFormName').value.trim();
        const color = document.getElementById('tagFormColor').value; // 색상 선택기의 최종 값을 사용
        const isDefaultEl = document.getElementById('tagFormIsDefault');
        const is_default = isDefaultEl ? isDefaultEl.checked : false;
        const pickedCategory = document.querySelector('input[name="tagFormCategory"]:checked');
        const category_id = pickedCategory ? parseInt(pickedCategory.value) : null;

        if (!name) {
            showNotification(gettext('태그명을 입력해주세요.'), 'warning');
            return;
        }

        if (!category_id) {
            showNotification(gettext('카테고리를 선택해주세요.'), 'warning');
            return;
        }

        const url = tagId ? `/api/tags/${tagId}/` : '/api/tags/';
        const method = tagId ? 'PUT' : 'POST';
        const saveBtn = this;

        try {
            const result = await apiCall(url, {
                method: method,
                data: { name, color, is_default, category_id },
                loadingElement: saveBtn
            });

            tagFormModal.hide();
            showNotification(result.message, 'success');
            // 태그 목록 업데이트가 필요하다는 이벤트를 발생시킴
            document.dispatchEvent(new CustomEvent('tags-updated'));
            
        } catch (error) {
            console.error('태그 저장 오류:', error);
            showNotification(interpolate(gettext('태그 저장 실패: %s'), [error.message]), 'error');
        }
    });

    // 전역 함수로 태그 삭제 함수 등록 (core utils 사용)
    const deleteModalEl = document.getElementById('tagDeleteModal');
    const deleteModal = deleteModalEl ? new bootstrap.Modal(deleteModalEl) : null;

    async function requestDelete(tagId, moveToId) {
        try {
            const result = await apiCall(`/api/tags/${tagId}/`, {
                method: 'DELETE',
                data: { move_to_id: moveToId }
            });
            showNotification(result.message, 'success');
            document.dispatchEvent(new CustomEvent('tags-updated'));
        } catch (error) {
            console.error('태그 삭제 오류:', error);
            showNotification(interpolate(gettext('태그 삭제 실패: %s'), [error.message]), 'error');
        }
    }

    /**
     * 기록이 붙은 태그를 그냥 지우면 그 구간이 미기록으로 돌아가 통계 수치가
     * 조용히 바뀐다. 옮길 곳을 기본값으로 두고 확인을 받는다.
     */
    function openDeleteModal(tag) {
        const select = document.getElementById('tagDeleteMoveTo');
        const others = (window._tagsCache || []).filter(other => other.id !== tag.id);

        select.innerHTML = '';
        others.forEach(other => {
            const option = document.createElement('option');
            option.value = other.id;
            option.textContent = other.name;
            select.appendChild(option);
        });

        document.getElementById('tagDeleteSummary').textContent = interpolate(
            gettext("'%(name)s'에는 %(hours)s시간(%(blocks)s칸)이 붙어 있습니다. 그냥 지우면 그 구간이 미기록으로 되돌아가 통계 수치가 바뀝니다."),
            { name: tag.name, hours: tag.total_hours, blocks: tag.block_count },
            true
        );

        const moveButton = document.getElementById('tagDeleteMoveAndDelete');
        moveButton.disabled = others.length === 0;
        moveButton.onclick = () => {
            deleteModal.hide();
            requestDelete(tag.id, parseInt(select.value, 10));
        };
        document.getElementById('tagDeleteOnly').onclick = () => {
            deleteModal.hide();
            requestDelete(tag.id, null);
        };

        deleteModal.show();
    }

    window.deleteTag = function(tagId) {
        const tag = (window._tagsCache || []).find(item => item.id === tagId);
        if (!tag) return;

        if (!tag.block_count) {
            if (confirmDelete(interpolate(gettext("'%s' 태그를 정말 삭제하시겠습니까?"), [tag.name]))) {
                requestDelete(tag.id, null);
            }
            return;
        }

        if (deleteModal) {
            openDeleteModal(tag);
        }
    };
});
