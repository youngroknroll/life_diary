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

    function syncColorFromCategory() {
        const select = document.getElementById('tagFormCategory');
        if (!select || !window._categories) return;
        const chosen = window._categories.find(cat => String(cat.id) === select.value);
        syncTagColorInputs(chosen && chosen.color);
    }

    const categorySelect = document.getElementById('tagFormCategory');
    if (categorySelect) {
        categorySelect.addEventListener('change', syncColorFromCategory);
    }

    // 카테고리 드롭다운 초기화
    function populateCategorySelect(selectedCategoryId) {
        const select = document.getElementById('tagFormCategory');
        if (!select || !window._categories) return;
        select.innerHTML = `<option value="">${gettext('카테고리를 선택하세요')}</option>`;
        window._categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            if (selectedCategoryId && cat.id === selectedCategoryId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        syncColorFromCategory();
    }

    // 전역 함수로 모달 열기 함수 등록
    window.openTagFormModal = function(tag = null) {
        const form = document.getElementById('tagForm');
        form.reset();
        
        const titleEl = document.getElementById('tagFormModalTitle');
        const tagIdInput = document.getElementById('tagFormTagId');
        const nameInput = document.getElementById('tagFormName');
        const colorInput = document.getElementById('tagFormColor');
        const colorTextInput = document.getElementById('tagFormColorText');
        const isDefaultCheckbox = document.getElementById('tagFormIsDefault');

        if (tag) {
            // 태그 수정
            titleEl.textContent = gettext('태그 수정');
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
            titleEl.textContent = gettext('새 태그 생성');
            tagIdInput.value = '';
            const defaultColor = '#007bff';
            colorInput.value = defaultColor;
            colorTextInput.value = defaultColor; // 텍스트 필드 값도 설정
            populateCategorySelect(null);
            if (isDefaultCheckbox) {
                isDefaultCheckbox.checked = false;
            }
        }
        
        tagFormModal.show();
    };

    // 저장 버튼 클릭 이벤트 (core utils 사용)
    document.getElementById('saveTagFormBtn').addEventListener('click', async function() {
        const tagId = document.getElementById('tagFormTagId').value;
        const name = document.getElementById('tagFormName').value.trim();
        const color = document.getElementById('tagFormColor').value; // 색상 선택기의 최종 값을 사용
        const isDefaultEl = document.getElementById('tagFormIsDefault');
        const is_default = isDefaultEl ? isDefaultEl.checked : false;
        const categorySelect = document.getElementById('tagFormCategory');
        const category_id = categorySelect ? parseInt(categorySelect.value) : null;

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
