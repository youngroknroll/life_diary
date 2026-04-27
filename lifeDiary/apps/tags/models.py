from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    시간 소비의 대분류 (시스템 고정 5가지).
    - 수동적 소비시간, 주도적 사용시간, 투자시간, 기초 생활시간, 수면시간
    """

    name = models.CharField(max_length=50, unique=True, verbose_name=_("카테고리명"))
    slug = models.SlugField(max_length=50, unique=True, verbose_name=_("슬러그"))
    description = models.TextField(blank=True, verbose_name=_("설명"))
    color = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message=_("올바른 HEX 색상 코드를 입력하세요 (예: #FF5733)"),
            )
        ],
        verbose_name=_("색상"),
    )
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name=_("표시 순서"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("생성일"))

    class Meta:
        verbose_name = _("카테고리")
        verbose_name_plural = _("카테고리들")
        ordering = ["display_order"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    사용자별 태그 관리
    - 이름: 태그명 (예: "업무", "운동", "식사")
    - 색상: HEX 색상 코드 (예: "#FF5733")
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tags",
        verbose_name=_("카테고리"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("사용자"),
        null=True,
        blank=True,
        help_text=_("null이면 기본 태그 (모든 사용자 공용)"),
    )
    name = models.CharField(
        max_length=50, verbose_name=_("태그명"), help_text=_("최대 50자까지 입력 가능")
    )
    color = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message=_("올바른 HEX 색상 코드를 입력하세요 (예: #FF5733)"),
            )
        ],
        verbose_name=_("색상"),
        help_text=_("HEX 색상 코드 (예: #FF5733)"),
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("기본 태그"),
        help_text=_("관리자가 등록한 모든 사용자 공용 태그"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("생성일"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("수정일"))

    class Meta:
        verbose_name = _("태그")
        verbose_name_plural = _("태그들")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_user_tag_name",
                violation_error_message=_("이미 같은 이름의 태그가 존재합니다."),
                condition=models.Q(user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["name"],
                name="unique_default_tag_name",
                violation_error_message=_("이미 같은 이름의 기본 태그가 존재합니다."),
                condition=models.Q(is_default=True),
            ),
        ]
        ordering = ["name"]

    @property
    def text_color(self):
        """배경색 대비 텍스트 색상 (YIQ 공식 기반)"""
        hex_color = self.color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        yiq = (r * 299 + g * 587 + b * 114) / 1000
        return '#212529' if yiq >= 128 else '#ffffff'

    def __str__(self):
        if self.is_default:
            return f"[기본] {self.name}"
        return f"{self.user.username if self.user else '시스템'} - {self.name}"

    def clean(self):
        """추가 유효성 검사"""
        super().clean()
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({"name": _("태그명은 공백일 수 없습니다.")})
