"""태그에 사용자가 정하는 표시 순서를 준다.

기본값 0 으로 컬럼만 더하면 모든 태그가 동점이 되어 순서가 DB 마음대로
정해진다. 사용자는 어제와 같은 화면으로 시작해야 하므로, 지금 보이는 순서
(카테고리 → 이름) 그대로 번호를 매겨 둔다.
"""

from django.db import migrations, models


def backfill_display_order(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")

    # 순서는 카테고리 안에서만 의미가 있다. (사용자, 카테고리) 묶음마다
    # 0 부터 새로 센다.
    ordered = Tag.objects.order_by("user_id", "category_id", "name")

    updated = []
    group = None
    position = 0
    for tag in ordered:
        key = (tag.user_id, tag.category_id)
        if key != group:
            group = key
            position = 0
        tag.display_order = position
        position += 1
        updated.append(tag)

    Tag.objects.bulk_update(updated, ["display_order"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0014_drop_shared_tag_concept"),
    ]

    operations = [
        migrations.AddField(
            model_name="tag",
            name="display_order",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="표시 순서"),
        ),
        migrations.RunPython(backfill_display_order, migrations.RunPython.noop),
    ]
