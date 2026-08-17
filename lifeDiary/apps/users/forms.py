from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserGoal, UserNote


User = get_user_model()


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_("이메일"),
        help_text=_("아이디/비밀번호 찾기에 사용됩니다."),
    )

    consent = forms.BooleanField(
        required=True,
        label=_("이용약관과 개인정보처리방침에 동의합니다"),
        error_messages={"required": _("이용약관과 개인정보처리방침에 동의해야 가입할 수 있습니다.")},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].max_length = 30
        self.fields["username"].widget.attrs["maxlength"] = 30
        self.fields["username"].help_text = _(
            "30자 이하. 영문자, 숫자, @/./+/-/_ 만 가능합니다."
        )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if len(username) > 30:
            raise forms.ValidationError(_("사용자명은 30자 이하여야 합니다."))
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("이미 사용 중인 이메일입니다."))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UsernameRecoveryForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label=_("이메일"),
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )


class UserGoalForm(forms.ModelForm):
    class Meta:
        model = UserGoal
        fields = ["tag", "period", "target_hours"]
        labels = {
            "tag": _("태그"),
            "period": _("기간"),
            "target_hours": _("목표 시간"),
        }
        widgets = {
            "tag": forms.Select(attrs={"class": "form-select", "style": "width: 50%"}),
            "period": forms.Select(
                choices=[("daily", _("일간")), ("weekly", _("주간")), ("monthly", _("월간"))],
                attrs={"class": "form-select", "style": "width: 50%"},
            ),
            "target_hours": forms.NumberInput(attrs={"step": 0.5, "min": 0, "class": "form-control"}),
        }
        help_texts = {
            "target_hours": _("주간/월간은 해당 기간의 총 목표 시간입니다."),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user or (self.instance.user if self.instance.pk else None)

    def clean(self):
        """같은 태그·기간 목표는 하나만 둔다. 둘이면 어느 쪽이 진행률에
        반영되는지 사용자가 알 수 없다."""
        cleaned = super().clean()
        tag = cleaned.get("tag")
        period = cleaned.get("period")
        if not (self._user and tag and period):
            return cleaned

        duplicate = UserGoal.objects.filter(
            user=self._user, tag=tag, period=period
        ).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise ValidationError(
                _("%(tag)s %(period)s 목표가 이미 있습니다.")
                % {"tag": tag.name, "period": dict(UserGoal.PERIOD_CHOICES)[period]}
            )
        return cleaned


class UserNoteForm(forms.ModelForm):
    class Meta:
        model = UserNote
        fields = ["note"]
        labels = {
            "note": _("내용"),
        }
        widgets = {
            "note": forms.Textarea(
                attrs={"rows": 4, "placeholder": _("특이사항을 입력하세요."), "class": "form-control"}
            ),
        }
