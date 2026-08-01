from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext, gettext_lazy as _


# CSS 의 --ink-on-accent 와 같은 값. 서버가 인라인 style 로도 내보내야 해서
# 여기에 한 번 더 둔다.
INK_ON_ACCENT = "#0F1A14"


# DB-stored Category 이름/설명을 makemessages가 수집하도록 등록.
# Why: 카테고리는 DB에 한국어로 저장되며 표시 시점에 gettext로 번역된다.
# How to apply: 새 카테고리를 추가하면 이 튜플에도 포함시켜야 en 번역 가능.
_CATEGORY_I18N_REGISTRY = (
    _("수동적 소비시간"),
    _("주도적 사용시간"),
    _("투자시간"),
    _("기초 생활시간"),
    _("수면시간"),
    _("비계획적이고 예정되지 않은 방식으로 소비되어버린 시간"),
    _("계획과 통제 안에서 내가 주도적으로 사용한 시간"),
    _("성과를 얻길 바라는 목표 영역에 대한 투자시간"),
    _("일정과 일정 사이의 기초적인 준비시간"),
    _("잠, 낮잠"),
)


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

    @property
    def display_name(self):
        return gettext(self.name)

    @property
    def display_description(self):
        return gettext(self.description) if self.description else ""

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
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message=_("올바른 HEX 색상 코드를 입력하세요 (예: #FF5733)"),
            )
        ],
        verbose_name=_("색상"),
        help_text=_("카테고리에서 자동으로 정해집니다."),
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

    def save(self, *args, **kwargs):
        """색은 카테고리가 정한다.

        사용자가 색을 고르면 같은 카테고리끼리 한 덩어리로 읽히는 규칙이
        깨지므로, 넘어온 값이 있어도 카테고리 색으로 덮어쓴다.
        """
        if self.category_id:
            self.color = self.category.color
        super().save(*args, **kwargs)

    @property
    def text_color(self):
        """태그 색 위 텍스트는 항상 같은 잉크를 쓴다.

        밝기로 흰 글자와 검은 글자를 뒤집으면 중간 밝기 색에서 4.5:1을
        넘기지 못한다. 다섯 카테고리 색은 모두 이 잉크로 기준을 통과한다.
        """
        return INK_ON_ACCENT

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
