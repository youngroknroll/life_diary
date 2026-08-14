"""`is_default` 컬럼과 소유자 없는 태그를 허용하던 스키마를 걷어낸다.

0013 이 null 소유자 행을 모두 없앤 뒤라야 `user` 를 non-nullable 로 바꿀 수
있다. 순서가 곧 전제다.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tags", "0013_personalize_shared_tags"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="tag",
            name="unique_default_tag_name",
        ),
        migrations.RemoveConstraint(
            model_name="tag",
            name="unique_user_tag_name",
        ),
        migrations.RemoveField(
            model_name="tag",
            name="is_default",
        ),
        migrations.AlterField(
            model_name="tag",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="사용자",
            ),
        ),
        migrations.AddConstraint(
            model_name="tag",
            constraint=models.UniqueConstraint(
                fields=("user", "name"),
                name="unique_user_tag_name",
                violation_error_message="이미 같은 이름의 태그가 존재합니다.",
            ),
        ),
    ]
