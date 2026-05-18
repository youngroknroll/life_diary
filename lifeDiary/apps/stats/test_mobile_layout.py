"""통계 페이지 모바일 레이아웃 회귀 테스트.

탭 동작은 그대로 유지(클릭 시 pane 전환). 모바일에서는 4개 탭 버튼이
세로로 wrap되지 않고 한 줄에 압축 표시되도록 CSS만 조정.
템플릿 차원에서는 4개 nav-link가 동일 ul 안에 그대로 있는지 확인.
"""
import re
import pytest
from apps.core.messages import LocalizableMessage
from django.urls import reverse


@pytest.mark.django_db
class TestStatsTabsStructure:
    def test_nav_tabs_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        assert response.status_code == 200
        h = response.content.decode()
        assert 'id="statsTabs"' in h
        assert 'data-bs-toggle="tab"' in h

    def test_four_tab_buttons_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        for target in ("#daily", "#weekly", "#monthly", "#tags"):
            assert f'data-bs-target="{target}"' in h, f"{target} 탭 버튼 누락"

    def test_four_tab_panes_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        for pane_id in ("daily", "weekly", "monthly", "tags"):
            assert f'id="{pane_id}"' in h, f"pane {pane_id} 누락"

    def test_only_daily_active_by_default(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        # 첫 번째 pane만 active+show
        assert 'id="daily" role="tabpanel"' in h
        m = re.search(r'class="([^"]+)" id="daily"', h)
        assert m and "show active" in m.group(1)


@pytest.mark.django_db
class TestLifeFeedbackToggleStructure:
    def test_life_feedback_list_collapsed_by_default(self, auth_client, monkeypatch):
        monkeypatch.setattr(
            "apps.stats.views.generate_feedback",
            lambda context: [
                LocalizableMessage(
                    code="stats.feedback.goal_achieved",
                    params={"period": "daily", "name": "Study", "hours": 1},
                    severity="positive",
                )
            ],
        )

        response = auth_client.get(reverse("stats:index"))
        assert response.status_code == 200
        h = response.content.decode()

        assert 'class="life-feedback-panel mt-3"' in h
        assert 'class="life-feedback-toggle collapsed"' in h
        assert 'data-bs-toggle="collapse"' in h
        assert 'data-bs-target="#lifeFeedbackList"' in h
        assert 'aria-expanded="false"' in h
        assert 'aria-controls="lifeFeedbackList"' in h
        assert 'id="lifeFeedbackList" class="collapse"' in h
        assert 'id="lifeFeedbackList" class="collapse show"' not in h
        assert 'class="badge bg-primary-subtle text-primary-emphasis ms-2"' in h
        assert 'class="life-feedback-list list-unstyled mb-0"' in h
        assert "life-feedback-card" in h

    def test_life_feedback_toggle_has_compact_responsive_styles(self):
        css = "apps/core/static/core/css/style.css"
        with open(css, encoding="utf-8") as f:
            content = f.read()

        assert ".life-feedback-toggle" in content
        assert "min-height: 44px;" in content
        assert ".life-feedback-toggle.collapsed .life-feedback-toggle__chevron" in content
        assert "transform: rotate(-90deg);" in content
        assert ".life-feedback-list" in content
        list_rule = re.search(r"\.life-feedback-list\s*\{(?P<body>[^}]+)\}", content)
        assert list_rule
        assert "display: flex;" in list_rule.group("body")
        assert "flex-wrap: wrap;" in list_rule.group("body")
        assert "overflow-x: auto;" not in list_rule.group("body")
