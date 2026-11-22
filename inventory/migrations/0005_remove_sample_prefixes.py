from django.conf import settings
from django.db import migrations


def remove_sample_prefixes(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Supplier = apps.get_model("inventory", "Supplier")
    Promotion = apps.get_model("inventory", "Promotion")
    Customer = apps.get_model("customers", "Customer")
    user_app, user_model = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app, user_model)
    database = schema_editor.connection.alias

    products = Product.objects.using(database).filter(name__startswith="DEMO -")
    for product in products.iterator():
        product.name = product.name[len("DEMO - "):]
        if product.description:
            product.description = product.description.replace("Demo", "Sample")
        product.save(using=database, update_fields=["name", "description"])

    Supplier.objects.using(database).filter(
        name="Demo Supplier (Placeholder)"
    ).update(name="Sample Supplier (Placeholder)")

    Promotion.objects.using(database).filter(
        title="Demo Screening Promotion"
    ).update(
        title="Screening Promotion",
        banner_text="Promotion only - replace with Darlez-approved offer before launch.",
    )

    patient_names = {
        "Demo Patient One": "Patient One",
        "Demo Patient Two": "Patient Two",
        "Demo Patient Three": "Patient Three",
    }
    for old_name, new_name in patient_names.items():
        Customer.objects.using(database).filter(name=old_name).update(name=new_name)

    User.objects.using(database).filter(
        username="labtech",
        first_name="Demo Technician",
    ).update(first_name="Technician")
    User.objects.using(database).filter(
        username="frontdesk",
        first_name="Demo Front Desk",
    ).update(first_name="Front Desk")


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0001_initial"),
        ("inventory", "0004_update_product_diagnostic_supply_help"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(remove_sample_prefixes, migrations.RunPython.noop),
    ]
