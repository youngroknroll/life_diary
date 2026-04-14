from django.db import migrations


def backfill_tag_category(apps, schema_editor):
    """기존 태그 중 category가 NULL인 것을 '수동적 소비시간'에 배정"""
    Tag = apps.get_model("tags", "Tag")
    Category = apps.get_model("tags", "Category")
    passive = Category.objects.filter(slug="passive").first()
    if passive:
        Tag.objects.filter(category__isnull=True).update(category=passive)


def reverse_backfill(apps, schema_editor):
    """되돌리기: backfill된 태그의 category를 NULL로"""
    Tag = apps.get_model("tags", "Tag")
    Category = apps.get_model("tags", "Category")
    passive = Category.objects.filter(slug="passive").first()
    if passive:
        Tag.objects.filter(category=passive).update(category=None)


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0005_seed_categories"),
    ]

    operations = [
        migrations.RunPython(backfill_tag_category, reverse_backfill),
    ]
