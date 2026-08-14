from django.db import migrations


SIAN_COLORS = {
    "investment": "#4E8F63",
    "proactive": "#4F8B9E",
    "passive": "#C1715A",
    "basic_life": "#C99A2E",
    "sleep": "#8A9A91",
}

PREVIOUS_COLORS = {
    "investment": "#2196F3",
    "proactive": "#4CAF50",
    "passive": "#9E9E9E",
    "basic_life": "#FF9800",
    "sleep": "#673AB7",
}


def apply_colors(apps, colors):
    Category = apps.get_model("tags", "Category")
    Tag = apps.get_model("tags", "Tag")

    for slug, color in colors.items():
        Category.objects.filter(slug=slug).update(color=color)
        Tag.objects.filter(category__slug=slug).update(color=color)


def forwards(apps, schema_editor):
    apply_colors(apps, SIAN_COLORS)


def backwards(apps, schema_editor):
    apply_colors(apps, PREVIOUS_COLORS)


class Migration(migrations.Migration):
    dependencies = [("tags", "0007_tag_category_not_null")]

    operations = [migrations.RunPython(forwards, backwards)]
