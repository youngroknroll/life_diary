from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("signup/check-username/", views.check_username_view, name="check_username"),
    path("signup/check-email/", views.check_email_view, name="check_email"),
    path("signup/verify/", views.signup_verify_view, name="signup_verify"),
    path(
        "signup/verify/resend/",
        views.signup_verify_resend_view,
        name="signup_verify_resend",
    ),
    path("welcome/", views.welcome_view, name="welcome"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", views.password_reset_view, name="password_reset"),
    path(
        "password-reset/verify/",
        views.password_reset_verify_view,
        name="password_reset_verify",
    ),
    path(
        "password-reset/verify/resend/",
        views.password_reset_resend_view,
        name="password_reset_resend",
    ),
    path(
        "password-reset/set/",
        views.password_reset_set_view,
        name="password_reset_set",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="users/password/password_change_form.html",
            success_url=reverse_lazy("users:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/password/password_change_done.html",
        ),
        name="password_change_done",
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
    path("account/delete/", views.account_delete, name="account_delete"),
]
