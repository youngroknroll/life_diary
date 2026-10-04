from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .account_deletion import cancel_account_deletion


class LifeDiarySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing and not sociallogin.user.is_active:
            cancel_account_deletion(sociallogin.user)
