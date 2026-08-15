import django.db.models.deletion
from django.db import migrations, models


def delete_tagless_blocks(apps, schema_editor):
    """과거 UI의 "기록까지 함께 삭제"가 남긴 tag_id NULL 행을 지운다.

    비가역 데이터 정리다. rollback은 reverse migration이 아니라
    배포 전 DB backup 복원으로만 가능하다.
    """
    TimeBlock = apps.get_model("dashboard", "TimeBlock")
    TimeBlock.objects.filter(tag__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0006_alter_timeblock_memo_charfield"),
    ]

    operations = [
        migrations.RunPython(delete_tagless_blocks, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="timeblock",
            name="tag",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="tags.tag",
                verbose_name="태그",
            ),
        ),
    ]
