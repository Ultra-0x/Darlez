from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_supply_categories"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(
                help_text="e.g. 'Full Blood Count', 'Chemistry Analyzer', or 'Malaria RDT Kit'",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="sku",
            field=models.CharField(
                max_length=64,
                unique=True,
                verbose_name="Product/Service Code",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Service details or product specifications, model, and usage information.",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="selling_price",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Listed price for a diagnostic service or supply item.",
                max_digits=10,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="stock_quantity",
            field=models.PositiveIntegerField(
                default=0,
                help_text="For services: available slots; for supplies: units in stock.",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="expiry_date",
            field=models.DateField(
                blank=True,
                help_text="Expiry date for stock items when applicable; leave blank otherwise.",
                null=True,
            ),
        ),
    ]
