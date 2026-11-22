from django.test import TestCase, override_settings

from inventory.models import Category, Product
from .models import WhatsAppOrder, WhatsAppOrderItem


class WhatsAppSupplyOrderMessageTests(TestCase):
    @override_settings(SITE_NAME="Darlez Medical Diagnostics Laboratory")
    def test_supply_request_includes_facility_and_delivery_address(self):
        category, _ = Category.objects.get_or_create(name="Diagnostic Equipment")
        product = Product.objects.create(
            name="Chemistry Analyzer",
            sku="EQ-001",
            category=category,
            selling_price="500000.00",
            stock_quantity=1,
        )
        order = WhatsAppOrder.objects.create(
            customer_name="Example Medical Centre",
            customer_phone="09000000000",
            delivery_address="Abuja, Nigeria",
        )
        WhatsAppOrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price="500000.00",
        )

        message = order.build_whatsapp_message()

        self.assertIn("New diagnostic or supply request — Darlez Medical Diagnostics Laboratory", message)
        self.assertIn("Customer / facility: Example Medical Centre (09000000000)", message)
        self.assertIn("Address provided: Abuja, Nigeria", message)
