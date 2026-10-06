"""dashboard 0007 — 레거시 tagless 행 제거와 tag 필수 전환.

비가역 데이터 정리 migration이라 현재 모델로는 증명할 수 없다.
production rollback은 코드가 아니라 배포 전 DB backup 복원이다.
"""

from datetime import date

import pytest
from django.db import connection, models
from django.db.migrations.executor import MigrationExecutor

MIGRATE_FROM = [
    ("dashboard", "0006_alter_timeblock_memo_charfield"),
    ("tags", "0016_remove_tag_display_order"),
]
MIGRATE_TO = [("dashboard", "0007_delete_tagless_blocks_and_require_tag")]


@pytest.mark.django_db(transaction=True)
def test_required_tag_migration_removes_legacy_tagless_time_blocks():
    executor = MigrationExecutor(connection)
    leaf_targets = executor.loader.graph.leaf_nodes()
    executor.migrate(MIGRATE_FROM)
    old_apps = executor.loader.project_state(MIGRATE_FROM).apps

    User = old_apps.get_model("auth", "User")
    Category = old_apps.get_model("tags", "Category")
    Tag = old_apps.get_model("tags", "Tag")
    TimeBlock = old_apps.get_model("dashboard", "TimeBlock")

    user = User.objects.create(username="legacyuser")
    category = Category.objects.create(
        name="레거시분류", slug="legacy_cat", color="#112233", display_order=99
    )
    tag = Tag.objects.create(user=user, name="유지", color="#112233", category=category)
    TimeBlock.objects.create(user=user, date=date(2026, 8, 1), slot_index=0, tag=tag)
    TimeBlock.objects.create(
        user=user, date=date(2026, 8, 1), slot_index=1, tag=None, memo="고아 메모"
    )

    try:
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(MIGRATE_TO)
        new_apps = executor.loader.project_state(MIGRATE_TO).apps
        MigratedTimeBlock = new_apps.get_model("dashboard", "TimeBlock")

        assert not MigratedTimeBlock.objects.filter(tag__isnull=True).exists()
        assert MigratedTimeBlock.objects.filter(slot_index=0).count() == 1
        tag_field = MigratedTimeBlock._meta.get_field("tag")
        assert tag_field.null is False
        assert tag_field.remote_field.on_delete is models.CASCADE
    finally:
        restore = MigrationExecutor(connection)
        restore.loader.build_graph()
        restore.migrate(leaf_targets)
