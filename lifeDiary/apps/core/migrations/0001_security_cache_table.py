from django.core.management import call_command
from django.db import migrations

SECURITY_CACHE_TABLE = "lifediary_security_cache"


def create_security_cache_table(apps, schema_editor):
    call_command(
        "createcachetable",
        SECURITY_CACHE_TABLE,
        database=schema_editor.connection.alias,
        verbosity=0,
    )


def drop_security_cache_table(apps, schema_editor):
    schema_editor.execute(
        f"DROP TABLE IF EXISTS {schema_editor.quote_name(SECURITY_CACHE_TABLE)}"
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_security_cache_table, drop_security_cache_table),
    ]
