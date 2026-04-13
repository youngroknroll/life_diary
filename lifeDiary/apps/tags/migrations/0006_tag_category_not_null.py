import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0005_seed_categories"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tags",
                to="tags.category",
                verbose_name="카테고리",
            ),
        ),
    ]
