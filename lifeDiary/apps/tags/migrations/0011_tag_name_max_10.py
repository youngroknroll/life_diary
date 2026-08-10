"""태그 이름을 10자로 줄인다 (사용자 결정 D3).

앞 10자가 같은 두 이름은 절삭만 하면 유니크 제약이 깨지므로, 사용자별로
이미 쓰인 이름을 보며 충돌을 피한다.
"""

from django.db import migrations, models

from apps.tags.name_limit import MAX_TAG_NAME_LENGTH, shorten_tag_name


def shorten_existing_names(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")
    taken_by_owner = {}

    for tag in Tag.objects.all().order_by("id"):
        owner = tag.user_id
        if owner not in taken_by_owner:
            taken_by_owner[owner] = {
                name
                for name in Tag.objects.filter(user_id=owner)
                .exclude(pk=tag.pk)
                .values_list("name", flat=True)
                if len(name) <= MAX_TAG_NAME_LENGTH
            }

        if len(tag.name) <= MAX_TAG_NAME_LENGTH:
            taken_by_owner[owner].add(tag.name)
            continue

        shortened = shorten_tag_name(tag.name, taken_by_owner[owner])
        tag.name = shortened
        tag.save(update_fields=["name"])
        taken_by_owner[owner].add(shortened)


def restore_is_a_no_op(apps, schema_editor):
    """되돌려도 잘린 이름은 복원되지 않는다. 열 길이만 되돌린다."""


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0010_pastel_category_palette"),
    ]

    operations = [
        migrations.RunPython(shorten_existing_names, restore_is_a_no_op),
        migrations.AlterField(
            model_name="tag",
            name="name",
            field=models.CharField(
                help_text="최대 10자까지 입력 가능",
                max_length=MAX_TAG_NAME_LENGTH,
                verbose_name="태그명",
            ),
        ),
    ]
