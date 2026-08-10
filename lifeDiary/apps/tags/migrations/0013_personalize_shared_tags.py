"""공유 기본 태그를 사용자별 개인 태그로 복제한 뒤 원본을 지운다.

되돌릴 수 없다. 기록과 목표의 참조가 복제본으로 옮겨 가고 나면 어느 행이
원래 공유 태그였는지 알 방법이 남지 않는다.

같은 이름의 개인 태그를 이미 가진 사용자에게는 복제본을 만들지 않고 그가 쓰던
태그로 참조를 옮긴다. `unique_user_tag_name` 을 지키기 위해서이기도 하고,
사용자가 이미 자기 이름으로 정리해 둔 것을 존중하기 위해서이기도 하다.
"""

from django.db import migrations


def personalize_shared_tags(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")
    TimeBlock = apps.get_model("dashboard", "TimeBlock")
    UserGoal = apps.get_model("users", "UserGoal")
    User = apps.get_model("auth", "User")

    shared = list(Tag.objects.filter(user__isnull=True))
    if not shared:
        return

    users = list(User.objects.all())
    for tag in shared:
        for user in users:
            personal = Tag.objects.filter(user=user, name=tag.name).first()
            if personal is None:
                personal = Tag.objects.create(
                    user=user,
                    name=tag.name,
                    color=tag.color,
                    category_id=tag.category_id,
                    is_default=False,
                )

            TimeBlock.objects.filter(tag=tag, user=user).update(tag=personal)

            for goal in UserGoal.objects.filter(tag=tag, user=user):
                clash = (
                    UserGoal.objects.filter(
                        user=user, tag=personal, period=goal.period
                    )
                    .exclude(pk=goal.pk)
                    .exists()
                )
                if clash:
                    goal.delete()
                else:
                    goal.tag = personal
                    goal.save(update_fields=["tag"])

        # 소유자가 사라진 사용자의 잔여 참조까지 CASCADE 로 끌려가지 않도록
        # 여기서 확인한다. 정상 데이터라면 0건이다.
        TimeBlock.objects.filter(tag=tag).delete()
        UserGoal.objects.filter(tag=tag).delete()
        tag.delete()


def unpersonalize(apps, schema_editor):
    raise RuntimeError(
        "공유 기본 태그 복제는 되돌릴 수 없습니다. 백업에서 복원하세요."
    )


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0012_sian_category_order"),
        ("dashboard", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(personalize_shared_tags, unpersonalize),
    ]
