from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("goals/", views.usergoal_list, name="usergoal_list"),
    path("goals/create/", views.usergoal_create, name="usergoal_create"),
    path("goals/<int:pk>/edit/", views.usergoal_update, name="usergoal_update"),
    path("goals/<int:pk>/delete/", views.usergoal_delete, name="usergoal_delete"),
    path("notes/", views.usernote_list, name="usernote_list"),
    path("notes/create/", views.usernote_create, name="usernote_create"),
    path("notes/<int:pk>/edit/", views.usernote_update, name="usernote_update"),
    path("notes/<int:pk>/delete/", views.usernote_delete, name="usernote_delete"),
    path("mypage/", views.mypage, name="mypage"),
    path("mypage/goals-partial/", views.mypage_goals_partial, name="mypage_goals_partial"),
]
