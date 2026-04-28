from django import forms
from django.utils.translation import gettext_lazy as _
from .models import UserGoal, UserNote


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # period 필드 변경 시 target_hours 필드의 max 속성을 동적으로 설정
        if "period" in self.fields:
            self.fields["period"].widget.attrs.update(
                {"onchange": "updateTargetHoursMax()"}
            )


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
