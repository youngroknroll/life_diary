from django.db import migrations

CATEGORIES = [
    {
        "name": "수동적 소비시간",
        "slug": "passive",
        "description": "비계획적이고 예정되지 않은 방식으로 소비되어버린 시간",
        "color": "#9E9E9E",
        "display_order": 1,
    },
    {
        "name": "주도적 사용시간",
        "slug": "proactive",
        "description": "계획과 통제 안에서 내가 주도적으로 사용한 시간",
        "color": "#4CAF50",
        "display_order": 2,
    },
    {
        "name": "투자시간",
        "slug": "investment",
        "description": "성과를 얻길 바라는 목표 영역에 대한 투자시간",
        "color": "#2196F3",
        "display_order": 3,
    },
    {
        "name": "기초 생활시간",
        "slug": "basic_life",
        "description": "일정과 일정 사이의 기초적인 준비시간",
        "color": "#FF9800",
        "display_order": 4,
    },
    {
        "name": "수면시간",
        "slug": "sleep",
        "description": "잠, 낮잠",
        "color": "#673AB7",
        "display_order": 5,
    },
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("tags", "Category")
    for cat_data in CATEGORIES:
        Category.objects.get_or_create(slug=cat_data["slug"], defaults=cat_data)


def unseed_categories(apps, schema_editor):
    Category = apps.get_model("tags", "Category")
    slugs = [c["slug"] for c in CATEGORIES]
    Category.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0004_category_tag_category"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
