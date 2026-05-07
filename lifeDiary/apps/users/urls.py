from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("signup/check-username/", views.check_username_view, name="check_username"),
    path("signup/check-email/", views.check_email_view, name="check_email"),
    path("welcome/", views.welcome_view, name="welcome"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password/password_reset_form.html",
            email_template_name="users/password/password_reset_email.txt",
            subject_template_name="users/password/password_reset_subject.txt",
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("username-recovery/", views.username_recovery_view, name="username_recovery"),
    path(
        "username-recovery/done/",
        views.username_recovery_done_view,
        name="username_recovery_done",
    ),
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
