from urllib.parse import parse_qs, urlparse

from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from customers.models import Customer
from .models import Category, Product, Promotion


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PublicCatalogDepartmentTests(TestCase):
    def setUp(self):
        diagnostics, _ = Category.objects.get_or_create(name="Haematology")
        reagents, _ = Category.objects.get_or_create(name="Reagents & Kits")
        equipment, _ = Category.objects.get_or_create(name="Diagnostic Equipment")
        Product.objects.create(
            name="Full Blood Count",
            sku="TEST-001",
            category=diagnostics,
            selling_price="3500.00",
            stock_quantity=10,
        )
        Product.objects.create(
            name="Malaria RDT Kit",
            sku="SUP-001",
            category=reagents,
            selling_price="12000.00",
            stock_quantity=10,
        )
        Product.objects.create(
            name="Chemistry Analyzer",
            sku="EQ-001",
            category=equipment,
            selling_price="500000.00",
            stock_quantity=1,
        )

    def test_diagnostics_catalog_excludes_supply_items(self):
        response = self.client.get(reverse("storefront:catalog"), {"department": "diagnostics"})

        self.assertContains(response, "Full Blood Count")
        self.assertNotContains(response, "Malaria RDT Kit")
        self.assertNotContains(response, "Chemistry Analyzer")

    def test_supply_catalog_includes_equipment_and_reagents(self):
        response = self.client.get(reverse("storefront:catalog"), {"department": "supplies"})

        self.assertContains(response, "Malaria RDT Kit")
        self.assertContains(response, "Chemistry Analyzer")
        self.assertNotContains(response, "Full Blood Count")


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PublicHomeHeroTests(TestCase):
    def test_hero_promotes_diagnostics_and_supplies_with_separate_actions(self):
        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, "Diagnostics and laboratory supplies for better care.")
        self.assertContains(response, "Browse Diagnostic Tests")
        self.assertContains(response, "Explore Equipment &amp; Supplies")
        self.assertContains(response, "Talk to our team")
        self.assertContains(response, "Diagnostic testing")
        self.assertContains(response, "Equipment &amp; supplies")
        self.assertContains(response, "Direct WhatsApp contact")
        self.assertContains(response, "cta-whatsapp-btn")

    def test_homepage_promotes_home_sample_collection(self):
        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, "Diagnostic testing, from the comfort of home")
        self.assertContains(response, "Our team can visit your home to collect samples for testing.")
        self.assertContains(response, "Request Home Testing")
        self.assertContains(response, "confirm service availability and appointment details")

    def test_homepage_displays_both_supplied_worker_photos(self):
        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, 'src="/static/img/darlez-lab-worker.png"')
        self.assertContains(response, 'src="/static/img/darlez-patient-care.png"')
        self.assertContains(response, 'alt="Darlez laboratory worker operating diagnostic equipment"')
        self.assertContains(response, 'alt="Darlez laboratory worker collecting a blood sample from a patient"')

    def test_header_and_footer_link_to_the_site_map(self):
        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, "10 Lingu Cres, Wuse II, Abuja 900288, Federal Capital Territory")
        self.assertContains(response, "View on Google Maps")
        self.assertContains(response, 'title="Darlez Medical Diagnostics Laboratory location map"')

    def test_how_it_works_explains_diagnostic_and_facility_supply_requests(self):
        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, "How it works")
        self.assertContains(response, "Diagnostic testing")
        self.assertContains(response, "Facility supply orders")
        self.assertContains(response, "Choose home collection")
        self.assertContains(response, "availability and order details")
        self.assertContains(response, "Browse Diagnostic Tests")
        self.assertContains(response, "Browse Equipment &amp; Supplies")

    def test_primary_home_sections_use_the_accent_color_classes(self):
        diagnostics, _ = Category.objects.get_or_create(name="Haematology")
        supplies, _ = Category.objects.get_or_create(name="Reagents & Kits")
        diagnostic_product = Product.objects.create(
            name="Featured diagnostic service",
            sku="TEST-ACCENT-DIAG",
            category=diagnostics,
            selling_price="1000.00",
            stock_quantity=10,
        )
        Product.objects.create(
            name="Featured supply item",
            sku="TEST-ACCENT-SUPPLY",
            category=supplies,
            selling_price="1000.00",
            stock_quantity=10,
        )
        promotion = Promotion.objects.create(title="Accent test promotion", discount_percent="10.00")
        promotion.products.add(diagnostic_product)

        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, 'class="mb-0 home-section-title"', count=3)
        self.assertContains(response, ".content-panel .home-section-title{")
        self.assertContains(response, "color:var(--darlez-red-dark); font-size:clamp")
        self.assertContains(response, ".cta-band .cta-whatsapp-btn{ color:#fff; background:#16834a; border-color:#16834a; }")


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PublicContactRequestTests(TestCase):
    def test_homepage_displays_message_request_form(self):
        response = self.client.get(reverse("storefront:home"))

        self.assertContains(response, 'id="contact-request"')
        self.assertContains(response, 'action="/contact-request/"')
        self.assertContains(response, "Send a message request")
        self.assertContains(response, "Continue to WhatsApp")

    def test_homepage_contact_form_builds_whatsapp_request_for_staff_reply(self):
        response = self.client.post(
            reverse("storefront:contact_request"),
            {
                "name": "Example Medical Centre",
                "phone": "09000000000",
                "request_type": "supplies",
                "message": "Please contact me about reagent availability.",
            },
        )

        self.assertEqual(response.status_code, 302)
        destination = urlparse(response["Location"])
        self.assertEqual(destination.scheme, "https")
        self.assertEqual(destination.netloc, "wa.me")
        self.assertEqual(destination.path, f"/{settings.WHATSAPP_BUSINESS_NUMBER}")
        whatsapp_message = parse_qs(destination.query)["text"][0]
        self.assertIn("Name / facility: Example Medical Centre", whatsapp_message)
        self.assertIn("Contact number: 09000000000", whatsapp_message)
        self.assertIn("Enquiry type: Equipment, reagents or consumables", whatsapp_message)
        self.assertIn("Please contact me about reagent availability.", whatsapp_message)

    def test_invalid_contact_request_renders_form_errors(self):
        response = self.client.post(
            reverse("storefront:contact_request"),
            {
                "name": "",
                "phone": "",
                "request_type": "unknown",
                "message": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "This field is required.", status_code=400)


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PublicFeaturedEquipmentTests(TestCase):
    def test_featured_flyer_models_have_quote_links_without_stock_prices(self):
        response = self.client.get(reverse("storefront:home"))

        for model, image in (
            ("Chemwell 2910", "img/equipment/chemwell-2910.png"),
            ("Autolyser", "img/equipment/autolyser.png"),
            ("HRJ-C100", "img/equipment/hrj-c100.png"),
        ):
            with self.subTest(model=model):
                self.assertContains(response, model)
                self.assertContains(response, image)
        self.assertContains(response, "Request a Quote", count=3)
        self.assertContains(response, "Confirm availability, configuration and pricing by request.")
        self.assertContains(
            response,
            "text=Hello%20Darlez%2C%20please%20send%20me%20a%20quote%20for%20Chemwell%202910.",
        )

    def test_sample_placeholder_equipment_is_hidden_from_public_storefront(self):
        category, _ = Category.objects.get_or_create(name="Diagnostic Equipment")
        product = Product.objects.create(
            name="Sample Placeholder Analyzer",
            sku="TEST-PLACEHOLDER-EQUIPMENT",
            category=category,
            description="Sample placeholder only. No Darlez model, specifications, image, price, or stock is confirmed.",
            selling_price="999999.00",
            stock_quantity=1,
        )

        home_response = self.client.get(reverse("storefront:home"))
        catalog_response = self.client.get(
            reverse("storefront:catalog"),
            {"department": "supplies"},
        )
        detail_response = self.client.get(
            reverse("storefront:product_detail", args=[product.pk]),
        )

        self.assertNotContains(home_response, "Sample Placeholder Analyzer")
        self.assertNotContains(catalog_response, "Sample Placeholder Analyzer")
        self.assertEqual(detail_response.status_code, 404)


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PublicProductImageTests(TestCase):
    def test_2hpp_shows_matching_image_on_catalog_and_product_page(self):
        category, _ = Category.objects.get_or_create(name="Clinical Chemistry")
        product = Product.objects.create(
            name="DEMO - 2hr Post Prandial Sugar (2HPP)",
            sku="TEST-2HPP-IMAGE",
            category=category,
            selling_price="2000.00",
            stock_quantity=10,
        )

        catalog_response = self.client.get(
            reverse("storefront:catalog"),
            {"department": "diagnostics"},
        )
        home_response = self.client.get(reverse("storefront:home"))
        detail_response = self.client.get(
            reverse("storefront:product_detail", args=[product.pk]),
        )

        image_path = "img/tests/2hpp-postprandial-glucose.svg"
        self.assertContains(catalog_response, image_path)
        self.assertContains(home_response, image_path)
        self.assertContains(detail_response, image_path)

    def test_category_fallback_images_appear_on_catalog_and_product_detail(self):
        image_cases = [
            ("Haematology", "Blood test", "img/products/diagnostic-lab.svg"),
            ("Diagnostic Equipment", "Analyzer", "img/products/diagnostic-equipment.svg"),
            ("Reagents & Kits", "Test kit", "img/products/reagents-kits.svg"),
            ("Consumables", "Lab supplies", "img/products/lab-consumables.svg"),
            ("Ultrasound Scan", "Ultrasound", "img/products/ultrasound-scan.svg"),
            ("ECG", "ECG", "img/products/ecg-testing.svg"),
        ]
        products = []
        for index, (category_name, name, _) in enumerate(image_cases):
            category, _ = Category.objects.get_or_create(name=category_name)
            products.append(
                Product.objects.create(
                    name=name,
                    sku=f"TEST-FALLBACK-{index}",
                    category=category,
                    selling_price="1000.00",
                    stock_quantity=10,
                )
            )

        catalog_response = self.client.get(reverse("storefront:catalog"))
        home_response = self.client.get(reverse("storefront:home"))
        detail_response = self.client.get(
            reverse("storefront:product_detail", args=[products[0].pk]),
        )

        for _, _, image_path in image_cases:
            with self.subTest(image_path=image_path):
                self.assertContains(catalog_response, image_path)
                self.assertContains(home_response, image_path)
        self.assertContains(detail_response, "img/products/diagnostic-lab.svg")


class DarlezSampleSeedDataTests(TestCase):
    def test_seed_command_adds_equipment_and_fictional_patients(self):
        call_command("seed_demo_data", stdout=StringIO())

        self.assertTrue(
            Product.objects.filter(
                name="Automated 3-Part Hematology Analyzer",
                category__name="Diagnostic Equipment",
            ).exists()
        )
        self.assertTrue(Customer.objects.filter(name="Patient One").exists())
