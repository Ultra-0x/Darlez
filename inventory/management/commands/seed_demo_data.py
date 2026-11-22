import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import StaffProfile
from customers.models import Customer
from inventory.models import Category, Supplier, Product, Promotion

# category -> [(name, price), ...]
SERVICE_CATALOG = {
    "Haematology": [
        ("Full Blood Count (FBC)", 3500),
        ("Hemoglobin (HB)", 1500),
        ("Packed Cell Volume (PCV)", 1200),
        ("White Blood Cell (WBC)", 1500),
        ("WBC (Differential Count)", 2000),
        ("Blood Film", 1800),
        ("Platelet Count", 1500),
        ("Erythrocyte Sedimentation Rate (ESR)", 1500),
        ("HB Genotype", 2500),
        ("Sickle Cell Screening", 2000),
        ("Mean Cell Volume (MCV)", 1500),
    ],
    "Clinical Chemistry": [
        ("Full Electrolyte (Na, K, Cl, HCO3)", 7000),
        ("Sodium (Na)", 2000),
        ("Potassium (K)", 2000),
        ("Chloride (Cl)", 2000),
        ("Bicarbonate (HCO3)", 2000),
        ("Urea", 2000),
        ("Creatinine", 2000),
        ("Full Lipid Profile", 8500),
        ("Total Cholesterol", 2500),
        ("Triglyceride", 2500),
        ("HDL Cholesterol", 2500),
        ("LDL Cholesterol", 2500),
        ("VLDL Cholesterol", 2500),
        ("Liver Function Test (LFT)", 9000),
        ("Total Bilirubin", 2000),
        ("Direct Bilirubin", 2000),
        ("SGPT (ALT)", 2000),
        ("SGOT (AST)", 2000),
        ("Alkaline Phosphatase", 2000),
        ("Glucose Tolerance Test (GTT)", 4500),
        ("Fasting Blood Sugar (FBS)", 1800),
        ("Random Blood Sugar (RBS)", 1500),
        ("2hr Post Prandial Sugar (2HPP)", 2000),
        ("Urinalysis", 1500),
    ],
    "Blood Serology": [
        ("Blood Grouping (ABO, RH)", 2000),
        ("VDRL (RPR/TPHA)", 2500),
        ("Hepatitis B Test", 3000),
        ("Hepatitis C Test", 3000),
        ("Widal Test", 2500),
        ("H. Pylori Test", 4500),
    ],
    "Microbiology & Parasitology": [
        ("Urine - Microscopy", 2000),
        ("Ear Swab - Culture & Sensitivity", 4000),
        ("Eye Swab - Culture & Sensitivity", 4000),
        ("Wound Swab - Culture & Sensitivity", 4000),
        ("Urethral Swab - Culture & Sensitivity", 4500),
        ("Vaginal Swab - Culture & Sensitivity", 4500),
        ("Throat Swab - Culture & Sensitivity", 4000),
        ("Malaria Parasite (MP)", 2000),
        ("Stool for Occult Blood", 1800),
        ("Stool Microscopy", 1800),
        ("Stool Culture & Sensitivity", 4000),
    ],
    "Semen Analysis": [
        ("Seminal Fluid Analysis (SFA)", 5000),
        ("Semen - Microscopy, Culture & Sensitivity", 6500),
    ],
    "Skin Tests": [
        ("Skin Snip for Microfilaria", 3000),
        ("Skin Scrapping (Fungal)", 2500),
        ("Mantoux / Heaf Test", 2500),
    ],
    "Ultrasound Scan": [
        ("Obstetric Ultrasound Scan", 15000),
        ("Pelvic Ultrasound Scan", 12000),
        ("Lower Abdomen Ultrasound Scan", 12000),
        ("Upper Abdomen Ultrasound Scan", 13000),
        ("Abdomino-Pelvic Ultrasound Scan", 16000),
    ],
    "Pregnancy Test": [
        ("Pregnancy Test (Urine)", 1200),
        ("Pregnancy Test (Blood - Beta hCG)", 4000),
    ],
    "Hormonal Profiles": [
        ("Male Infertility Profile (FSH, LH, PROL, Testosterone)", 15000),
        ("Female Fertility Profile (FSH, LH, PROL, Progesterone)", 15000),
        ("Thyroid Screening", 12000),
        ("Menstrual Disorder Profile", 13000),
        ("Prostate Specific Antigen (PSA)", 8000),
    ],
    "ECG": [
        ("Pre-Exercise ECG", 5000),
        ("Post-Exercise ECG", 5000),
        ("Pre & Post Exercise ECG", 8000),
    ],
}

REAGENTS_AND_CONSUMABLES = [
    # name, category, cost, price, stock, expiry_days_from_today (None = no expiry)
    ("Malaria RDT Kit (box of 25)", "Reagents & Kits", 8000, 12000, 3, 20),
    ("HIV Rapid Test Kit (box of 30)", "Reagents & Kits", 15000, 22000, 2, 10),
    ("Glucose Test Strips (box)", "Reagents & Kits", 4500, 7000, 15, 200),
    ("Widal Antigen Reagent Set", "Reagents & Kits", 9000, 13500, 4, 5),
    ("VDRL Antigen Reagent Set", "Reagents & Kits", 7000, 10500, 3, 15),
    ("Blood Collection Tubes (EDTA, pack)", "Consumables", 3000, 4500, 40, 400),
    ("Disposable Syringes (box of 100)", "Consumables", 2500, 3800, 6, None),
    ("Lab Gloves (box, medium)", "Consumables", 2000, 3200, 25, None),
    ("Specimen Containers (pack of 50)", "Consumables", 3500, 5000, 8, None),
]

SAMPLE_EQUIPMENT = [
    # name, cost, price, stock
    ("Automated 3-Part Hematology Analyzer", 1000000, 1250000, 1),
    ("Semi-Automated Chemistry Analyzer", 1800000, 2300000, 1),
    ("Benchtop Centrifuge", 250000, 320000, 2),
]


class Command(BaseCommand):
    help = "Seed Darlez staff, sample diagnostic services, supply products, and fictional patients."

    def handle(self, *args, **options):
        today = timezone.localdate()

        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser("admin", "", "admin12345")
            StaffProfile.objects.create(user=admin, role=StaffProfile.ROLE_ADMIN)
            self.stdout.write(self.style.SUCCESS("Created admin user (username=admin, password=admin12345)"))

        if not User.objects.filter(username="labtech").exists():
            labtech = User.objects.create_user("labtech", "labtech@example.com", "labtech12345", first_name="Technician")
            StaffProfile.objects.create(user=labtech, role=StaffProfile.ROLE_LAB_TECH)
            self.stdout.write(self.style.SUCCESS("Created lab tech user (username=labtech, password=labtech12345)"))

        if not User.objects.filter(username="frontdesk").exists():
            frontdesk = User.objects.create_user("frontdesk", "frontdesk@example.com", "frontdesk12345", first_name="Front Desk")
            StaffProfile.objects.create(user=frontdesk, role=StaffProfile.ROLE_CASHIER)
            self.stdout.write(self.style.SUCCESS("Created front desk user (username=frontdesk, password=frontdesk12345)"))

        all_category_names = list(SERVICE_CATALOG.keys()) + [
            "Diagnostic Equipment", "Reagents & Kits", "Consumables",
        ]
        categories = {}
        for name in all_category_names:
            categories[name], _ = Category.objects.get_or_create(name=name)

        supplier, _ = Supplier.objects.get_or_create(name="Sample Supplier (Placeholder)")

        created_products = []
        sku_counter = 1

        # Seeded product details and prices are samples, not approved Darlez listings.
        for category_name, items in SERVICE_CATALOG.items():
            for name, price in items:
                cost = round(price * 0.35)
                product, _ = Product.objects.get_or_create(
                    sku=f"DX-{sku_counter:04d}",
                    defaults=dict(
                        name=name,
                        category=categories[category_name],
                        supplier=None,
                        description="Sample data only. Replace with Darlez-approved service details and pricing before production.",
                        cost_price=cost,
                        selling_price=price,
                        stock_quantity=999,
                        low_stock_threshold=5, expiry_date=None,
                    ),
                )
                created_products.append(product)
                sku_counter += 1

        for equipment_counter, (name, cost, price, stock) in enumerate(SAMPLE_EQUIPMENT, start=1):
            product, _ = Product.objects.get_or_create(
                sku=f"EQ-{equipment_counter:04d}",
                defaults=dict(
                    name=name,
                    category=categories["Diagnostic Equipment"],
                    supplier=supplier,
                    description="Sample placeholder only. No Darlez model, specifications, image, price, or stock is confirmed.",
                    cost_price=cost,
                    selling_price=price,
                    stock_quantity=stock,
                    low_stock_threshold=1,
                    expiry_date=None,
                ),
            )
            created_products.append(product)

        for name, cat, cost, price, stock, expiry_days in REAGENTS_AND_CONSUMABLES:
            expiry = today + timedelta(days=expiry_days) if expiry_days else None
            product, _ = Product.objects.get_or_create(
                sku=f"DX-{sku_counter:04d}",
                defaults=dict(
                    name=name,
                    category=categories[cat],
                    supplier=supplier,
                    description="Sample data only. Replace with Darlez-approved product details, pricing, and stock before production.",
                    cost_price=cost,
                    selling_price=price,
                    stock_quantity=stock,
                    low_stock_threshold=5,
                    expiry_date=expiry,
                ),
            )
            created_products.append(product)
            sku_counter += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(created_products)} sample services and supply products "
                f"across {len(all_category_names)} categories."
            )
        )

        promo, created = Promotion.objects.get_or_create(
            title="Screening Promotion",
            defaults=dict(
                banner_text="Promotion only - replace with Darlez-approved offer before launch.",
                discount_percent=20,
                start_date=today,
                end_date=today + timedelta(days=7),
                is_active=True,
            ),
        )
        if created:
            haem_tests = [p for p in created_products if p.category.name == "Haematology"]
            promo.products.set(random.sample(haem_tests, min(4, len(haem_tests))))
            self.stdout.write(self.style.SUCCESS("Created screening promotion."))

        sample_patients = [
            ("Patient One", "0000000001", "patient1@example.com"),
            ("Patient Two", "0000000002", "patient2@example.com"),
            ("Patient Three", "0000000003", ""),
        ]
        for name, phone, email in sample_patients:
            Customer.objects.get_or_create(phone_number=phone, defaults={"name": name, "email": email})
        self.stdout.write(self.style.SUCCESS("Seeded fictional sample patients."))

        self.stdout.write(self.style.SUCCESS("\nDone! Log in at /accounts/login/ with admin / admin12345"))
