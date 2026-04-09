from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.tags.models import Tag
from apps.core.utils import UNCLASSIFIED_TAG_NAME

# Create your models here.


class TimeBlock(models.Model):
    """
    10분 단위 시간 블록 관리
    - 하루 24시간 = 144개 슬롯 (0~143)
    - 각 슬롯은 10분 단위 (00:00~00:10 = 슬롯 0, 00:10~00:20 = 슬롯 1, ...)
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    date = models.DateField(verbose_name="날짜")
    slot_index = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(143)],
        verbose_name="슬롯 인덱스",
        help_text="0~143 (0: 00:00-00:10, 143: 23:50-24:00)",
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True, verbose_name="태그"
    )
    memo = models.CharField(
        blank=True,
        max_length=500,
        verbose_name="메모",
        help_text="최대 500자까지 입력 가능",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "시간 블록"
        verbose_name_plural = "시간 블록들"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date", "slot_index"],
                name="unique_user_date_slot",
                violation_error_message="해당 시간대에 이미 기록이 존재합니다.",
            )
        ]
        ordering = ["date", "slot_index"]
        indexes = [
            models.Index(fields=["user", "date"], name="idx_user_date"),
            models.Index(fields=["user", "tag"], name="idx_user_tag"),
            models.Index(fields=["date", "slot_index"], name="idx_date_slot"),
        ]

    def __str__(self):
        tag_name = self.tag.name if self.tag else UNCLASSIFIED_TAG_NAME
        return f"{self.user.username} - {self.date} [{self.get_time_range()}] {tag_name}"

    def get_time_range(self):
        """슬롯 인덱스를 시간 범위로 변환"""
        start_hour, start_minute = divmod(self.slot_index * 10, 60)
        end_hour, end_minute = divmod((self.slot_index + 1) * 10, 60)

        return f"{start_hour:02d}:{start_minute:02d}-{end_hour:02d}:{end_minute:02d}"

    @staticmethod
    def time_to_slot_index(hour, minute):
        """시간을 슬롯 인덱스로 변환"""
        return hour * 6 + minute // 10

    @staticmethod
    def slot_index_to_time(slot_index):
        """슬롯 인덱스를 시간으로 변환"""
        total_minutes = slot_index * 10
        hour, minute = divmod(total_minutes, 60)
        return hour, minute

    def clean(self):
        """추가 유효성 검사"""
        super().clean()
        # 태그와 사용자가 일치하는지 확인 (기본 태그는 제외)
        if (
            self.tag
            and self.user
            and not self.tag.is_default
            and self.tag.user != self.user
        ):
            raise ValidationError({"tag": "다른 사용자의 태그는 사용할 수 없습니다."})
