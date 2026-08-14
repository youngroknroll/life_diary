"""사용자가 정하는 태그 순서를 두지 않기로 했다 (2026-08-12 사용자).

카테고리 순서는 시스템이 정하고 태그는 그 안에서 이름순이다. 0015 가 넣은
컬럼은 하루도 쓰이지 않았고 운영 DB 에도 올라간 적이 없다. 0015 를 지우는
대신 걷어내는 마이그레이션을 더한다 — 이미 0015 를 돌린 개발 DB 가 있다.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0015_tag_display_order"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tag",
            name="display_order",
        ),
    ]
