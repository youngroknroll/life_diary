from django.urls import path
from . import views

app_name = "tags_api"

urlpatterns = [
    path("categories/", views.category_list, name="category_list"),
    path("tags/", views.tag_list_create, name="tag_list_create"),
    path("tags/order/", views.tag_order, name="tag_order"),
    path(
        "tags/<int:tag_id>/",
        views.tag_detail_update_delete,
        name="tag_detail_update_delete",
    ),
]
