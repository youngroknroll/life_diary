from django.urls import path
from . import views

app_name = "dashboard_api"

urlpatterns = [
    # 시간 블록 관리 API
    path("time-blocks/", views.time_block_api, name="time_block_api"),
    path("time-blocks/undo/", views.time_block_undo_api, name="time_block_undo_api"),
]
