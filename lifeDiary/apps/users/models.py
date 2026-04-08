from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from apps.tags.models import Tag

# Create your models here.


class UserGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    period = models.CharField(
        max_length=10,
        choices=[("daily", "일간"), ("weekly", "주간"), ("monthly", "월간")],
    )
    target_hours = models.FloatField(validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.tag.name} ({self.period}): {self.target_hours}시간"

    def clean(self):
        """목표 시간 유효성 검사"""
        super().clean()

        if self.target_hours is not None:
            if self.period == "daily":
                if self.target_hours > 24:
                    raise ValidationError(
                        {"target_hours": "일간 목표는 24시간을 초과할 수 없습니다."}
                    )
            elif self.period == "weekly":
                if self.target_hours > 100:
                    raise ValidationError(
                        {"target_hours": "주간 목표는 100시간을 초과할 수 없습니다."}
                    )
            elif self.period == "monthly":
                if self.target_hours > 300:
                    raise ValidationError(
                        {"target_hours": "월간 목표는 300시간을 초과할 수 없습니다."}
                    )


class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"
