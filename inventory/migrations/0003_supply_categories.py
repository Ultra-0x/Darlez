from django.db import migrations


def create_supply_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    for name in ("Diagnostic Equipment", "Reagents & Kits", "Consumables"):
        Category.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_alter_product_description_alter_product_expiry_date_and_more"),
    ]

    operations = [
        migrations.RunPython(create_supply_categories, migrations.RunPython.noop),
    ]
