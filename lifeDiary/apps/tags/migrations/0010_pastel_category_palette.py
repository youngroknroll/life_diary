from django.db import migrations


PASTEL_COLORS = {'investment': '#7CD9A0', 'proactive': '#7DCFE8', 'passive': '#FFA98C', 'basic_life': '#FFD166', 'sleep': '#B8A6F0'}

PREVIOUS_COLORS = {'investment': '#4E8F63', 'proactive': '#4F8B9E', 'passive': '#C1715A', 'basic_life': '#C99A2E', 'sleep': '#8A9A91'}


def apply_colors(apps, colors):
    Category = apps.get_model("tags", "Category")
    Tag = apps.get_model("tags", "Tag")

    for slug, color in colors.items():
        Category.objects.filter(slug=slug).update(color=color)
        Tag.objects.filter(category__slug=slug).update(color=color)


def forwards(apps, schema_editor):
    apply_colors(apps, PASTEL_COLORS)


def backwards(apps, schema_editor):
    apply_colors(apps, PREVIOUS_COLORS)


class Migration(migrations.Migration):
    dependencies = [("tags", "0009_alter_tag_color")]

    operations = [migrations.RunPython(forwards, backwards)]
