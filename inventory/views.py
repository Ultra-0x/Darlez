from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from urllib.parse import quote

from accounts.permissions import staff_required, manager_required
from .forms import ContactRequestForm, ProductForm, CategoryForm, SupplierForm, PromotionForm, RestockForm
from .models import Product, Category, Supplier, Promotion, StockMovement


# ---------- Public storefront ----------

CATEGORY_ICONS = {
    "Diagnostic Equipment": "bi-cpu",
    "Haematology": "bi-droplet-half",
    "Clinical Chemistry": "bi-flask",
    "Blood Serology": "bi-shield-plus",
    "Microbiology & Parasitology": "bi-bug",
    "Semen Analysis": "bi-gender-male",
    "Skin Tests": "bi-bandaid",
    "Ultrasound Scan": "bi-soundwave",
    "Pregnancy Test": "bi-heart-pulse",
    "Hormonal Profiles": "bi-activity",
    "ECG": "bi-heart-pulse-fill",
    "Reagents & Kits": "bi-eyedropper",
    "Consumables": "bi-box-seam",
}
SUPPLY_CATEGORIES = ["Diagnostic Equipment", "Reagents & Kits", "Consumables"]
PLACEHOLDER_EQUIPMENT_DESCRIPTION = "Sample placeholder only"
FEATURED_EQUIPMENT = [
    {
        "name": "Chemwell 2910",
        "image": "img/equipment/chemwell-2910.png",
        "alt": "Chemwell 2910 chemistry analyzer from the Darlez equipment flyer",
    },
    {
        "name": "Autolyser",
        "image": "img/equipment/autolyser.png",
        "alt": "Autolyser chemistry analyzer from the Darlez equipment flyer",
    },
    {
        "name": "HRJ-C100",
        "image": "img/equipment/hrj-c100.png",
        "alt": "HRJ-C100 chemistry analyzer from the Darlez equipment flyer",
    },
]


def _storefront_home_context():
    today = timezone.localdate()
    public_products = Product.objects.filter(is_active=True).exclude(
        description__icontains=PLACEHOLDER_EQUIPMENT_DESCRIPTION
    )
    active_promotions = Promotion.objects.filter(
        is_active=True, start_date__lte=today, end_date__gte=today
    ).prefetch_related("products")
    featured_products = public_products.filter(promotions__in=active_promotions).distinct()[:12]

    billable_products = public_products.exclude(category__name__in=SUPPLY_CATEGORIES)
    popular_products = billable_products.order_by("name")[:8]
    total_tests = billable_products.count()

    categories = Category.objects.exclude(name__in=SUPPLY_CATEGORIES).filter(products__is_active=True).distinct()
    categories_with_icons = [
        {"obj": c, "icon": CATEGORY_ICONS.get(c.name, "bi-clipboard2-pulse")} for c in categories
    ]
    supply_products = public_products.filter(
        category__name__in=SUPPLY_CATEGORIES,
    ).select_related("category").order_by("category__name", "name")[:8]

    return {
        "promotions": active_promotions,
        "featured_products": featured_products,
        "featured_equipment": FEATURED_EQUIPMENT,
        "popular_products": popular_products,
        "supply_products": supply_products,
        "categories": categories_with_icons,
        "total_tests": total_tests,
        "total_categories": categories.count(),
        "contact_form": ContactRequestForm(),
    }


def storefront_home(request):
    return render(request, "storefront/home.html", _storefront_home_context())


def storefront_contact_request(request):
    if request.method != "POST":
        return redirect("storefront:home")

    form = ContactRequestForm(request.POST)
    if not form.is_valid():
        context = _storefront_home_context()
        context["contact_form"] = form
        return render(request, "storefront/home.html", context, status=400)

    request_type = dict(form.fields["request_type"].choices)[form.cleaned_data["request_type"]]
    message = "\n".join([
        f"New website message request — {settings.SITE_NAME}",
        f"Name / facility: {form.cleaned_data['name']}",
        f"Contact number: {form.cleaned_data['phone']}",
        f"Enquiry type: {request_type}",
        f"Message: {form.cleaned_data['message']}",
    ])
    whatsapp_url = (
        f"https://wa.me/{settings.WHATSAPP_BUSINESS_NUMBER}?text={quote(message, safe='')}"
    )
    return redirect(whatsapp_url)


def storefront_catalog(request):
    products = Product.objects.filter(is_active=True).exclude(
        description__icontains=PLACEHOLDER_EQUIPMENT_DESCRIPTION
    ).select_related("category")
    query = request.GET.get("q", "")
    category_id = request.GET.get("category", "")
    department = request.GET.get("department", "")
    if department == "supplies":
        products = products.filter(category__name__in=SUPPLY_CATEGORIES)
        categories = Category.objects.filter(
            name__in=SUPPLY_CATEGORIES, products__is_active=True,
        ).distinct()
    elif department == "diagnostics":
        products = products.exclude(category__name__in=SUPPLY_CATEGORIES)
        categories = Category.objects.exclude(name__in=SUPPLY_CATEGORIES)
    else:
        categories = Category.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    return render(request, "storefront/catalog.html", {
        "products": products, "categories": categories, "query": query, "category_id": category_id,
        "department": department,
    })


def storefront_product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.exclude(description__icontains=PLACEHOLDER_EQUIPMENT_DESCRIPTION),
        pk=pk,
        is_active=True,
    )
    return render(request, "storefront/product_detail.html", {"product": product})


# ---------- Staff-facing inventory management ----------

@staff_required
def product_list(request):
    products = Product.objects.select_related("category", "supplier").all()
    query = request.GET.get("q", "")
    filter_type = request.GET.get("filter", "")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    if filter_type == "low_stock":
        products = [p for p in products if p.is_low_stock]
    elif filter_type == "expiring":
        products = [p for p in products if p.is_expiring_soon or p.is_expired]
    return render(request, "inventory/product_list.html", {
        "products": products, "query": query, "filter_type": filter_type,
    })


@staff_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.stock_movements.all()[:20]
    return render(request, "inventory/product_detail.html", {"product": product, "movements": movements})


@manager_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            StockMovement.objects.create(
                product=product, quantity_change=product.stock_quantity,
                reason=StockMovement.REASON_RESTOCK, note="Initial stock", created_by=request.user,
            )
            messages.success(request, "Product added.")
            return redirect("inventory:product_list")
    else:
        form = ProductForm()
    return render(request, "inventory/product_form.html", {"form": form, "title": "Add Product"})


@manager_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("inventory:product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "inventory/product_form.html", {"form": form, "title": f"Edit {product.name}"})


@manager_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("inventory:product_list")
    return render(request, "inventory/product_confirm_delete.html", {"product": product})


@staff_required
def product_restock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = RestockForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data["quantity"]
            product.stock_quantity += qty
            product.save(update_fields=["stock_quantity"])
            StockMovement.objects.create(
                product=product, quantity_change=qty, reason=StockMovement.REASON_RESTOCK,
                note=form.cleaned_data.get("note", ""), created_by=request.user,
            )
            messages.success(request, f"Added {qty} units to {product.name}.")
            return redirect("inventory:product_detail", pk=pk)
    else:
        form = RestockForm()
    return render(request, "inventory/restock_form.html", {"form": form, "product": product})


@staff_required
def alerts_view(request):
    products = Product.objects.filter(is_active=True)
    low_stock = [p for p in products if p.is_low_stock]
    expiring = [p for p in products if p.is_expiring_soon and not p.is_expired]
    expired = [p for p in products if p.is_expired]
    return render(request, "inventory/alerts.html", {
        "low_stock": low_stock, "expiring": expiring, "expired": expired,
    })


# ---------- Categories & Suppliers ----------

@manager_required
def category_list(request):
    categories = Category.objects.all()
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added.")
            return redirect("inventory:category_list")
    else:
        form = CategoryForm()
    return render(request, "inventory/category_list.html", {"categories": categories, "form": form})


@manager_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.")
    return redirect("inventory:category_list")


@manager_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added.")
            return redirect("inventory:supplier_list")
    else:
        form = SupplierForm()
    return render(request, "inventory/supplier_list.html", {"suppliers": suppliers, "form": form})


@manager_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.delete()
        messages.success(request, "Supplier deleted.")
    return redirect("inventory:supplier_list")


# ---------- Promotions (advertised sales) ----------

@manager_required
def promotion_list(request):
    promotions = Promotion.objects.all().prefetch_related("products")
    return render(request, "inventory/promotion_list.html", {"promotions": promotions})


@manager_required
def promotion_create(request):
    if request.method == "POST":
        form = PromotionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Promotion created and now advertised on the storefront.")
            return redirect("inventory:promotion_list")
    else:
        form = PromotionForm()
    return render(request, "inventory/promotion_form.html", {"form": form, "title": "New Promotion"})


@manager_required
def promotion_edit(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    if request.method == "POST":
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            form.save()
            messages.success(request, "Promotion updated.")
            return redirect("inventory:promotion_list")
    else:
        form = PromotionForm(instance=promotion)
    return render(request, "inventory/promotion_form.html", {"form": form, "title": f"Edit {promotion.title}"})


@manager_required
def promotion_delete(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    if request.method == "POST":
        promotion.delete()
        messages.success(request, "Promotion deleted.")
        return redirect("inventory:promotion_list")
    return render(request, "inventory/promotion_confirm_delete.html", {"promotion": promotion})
