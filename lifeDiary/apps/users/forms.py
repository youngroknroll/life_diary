from django import forms
from django.core.exceptions import ValidationError
from .models import UserGoal, UserNote


class UserGoalForm(forms.ModelForm):
    class Meta:
        model = UserGoal
        fields = ["tag", "period", "target_hours"]
        labels = {
            "tag": "태그",
            "period": "기간",
            "target_hours": "목표 시간",
        }
        widgets = {
            "tag": forms.Select(attrs={"class": "form-select", "style": "width: 50%"}),
            "period": forms.Select(
                choices=[("daily", "일간"), ("weekly", "주간"), ("monthly", "월간")],
                attrs={"class": "form-select", "style": "width: 50%"},
            ),
            "target_hours": forms.NumberInput(attrs={"step": 0.5, "min": 0, "class": "form-control"}),
        }
        help_texts = {
            "target_hours": "주간/월간은 해당 기간의 총 목표 시간입니다.",
        }

    def clean(self):
        """폼 레벨 유효성 검사"""
        cleaned_data = super().clean()
        period = cleaned_data.get("period")
        target_hours = cleaned_data.get("target_hours")

        if period and target_hours is not None:
            if period == "daily" and target_hours > 24:
                raise ValidationError(
                    {"target_hours": "일간 목표는 24시간을 초과할 수 없습니다."}
                )
            elif period == "weekly" and target_hours > 100:
                raise ValidationError(
                    {"target_hours": "주간 목표는 100시간을 초과할 수 없습니다."}
                )
            elif period == "monthly" and target_hours > 300:
                raise ValidationError(
                    {"target_hours": "월간 목표는 300시간을 초과할 수 없습니다."}
                )

        return cleaned_data

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
        widgets = {
            "note": forms.Textarea(
                attrs={"rows": 4, "placeholder": "특이사항을 입력하세요."}
            ),
        }
