"""카테고리 표시 순서를 시안 순서로 맞춘다.

시안 7a·7b 는 투자 → 주도적 → 수동적 → 기초 → 수면 순으로 그린다. 자기통제력이
높은 쪽에서 낮은 쪽으로 읽는 배열이다. DB 는 정반대(수동적이 먼저)였다.

`Category.Meta.ordering = ["display_order"]` 이라 이 값 하나가 카테고리를
나열하는 모든 화면을 바꾼다.
"""

from django.db import migrations

SIAN_ORDER = {
    "investment": 1,
    "proactive": 2,
    "passive": 3,
    "basic_life": 4,
    "sleep": 5,
}

PREVIOUS_ORDER = {
    "passive": 1,
    "proactive": 2,
    "investment": 3,
    "basic_life": 4,
    "sleep": 5,
}


def apply_order(order_map):
    def migrate(apps, schema_editor):
        Category = apps.get_model("tags", "Category")
        for slug, position in order_map.items():
            Category.objects.filter(slug=slug).update(display_order=position)

    return migrate


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0011_tag_name_max_10"),
    ]

    operations = [
        migrations.RunPython(apply_order(SIAN_ORDER), apply_order(PREVIOUS_ORDER)),
    ]
