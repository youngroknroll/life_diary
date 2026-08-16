import pytest


@pytest.mark.django_db
class TestApiDocs:
    def test_openapi_schema_lists_all_five_endpoints(self, client):
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        assert set(paths) == {
            "/api/time-blocks/",
            "/api/time-blocks/undo/",
            "/api/categories/",
            "/api/tags/",
            "/api/tags/{tag_id}/",
        }

    def test_swagger_ui_page_renders_without_login(self, client):
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert b"swagger" in response.content.lower()
