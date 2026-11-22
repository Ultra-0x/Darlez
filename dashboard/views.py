from datetime import timedelta

from django.db.models import Sum, F, DecimalField
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import staff_required
from customers.models import Customer
from inventory.models import Product
from orders.models import WhatsAppOrder, DeliveryRequest
from sales.models import Sale, SaleItem
from whatsapp_bot.models import Appointment, WhatsAppContact


@staff_required
def home(request):
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)

    todays_items = SaleItem.objects.filter(sale__created_at__date=today)
    todays_revenue = todays_items.aggregate(
        total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField())
    )["total"] or 0
    todays_sale_count = Sale.objects.filter(created_at__date=today).count()

    week_items = SaleItem.objects.filter(sale__created_at__date__gte=week_ago)
    week_revenue = week_items.aggregate(
        total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField())
    )["total"] or 0

    products = Product.objects.filter(is_active=True)
    low_stock_count = sum(1 for p in products if p.is_low_stock)
    expiring_count = sum(1 for p in products if p.is_expiring_soon and not p.is_expired)
    expired_count = sum(1 for p in products if p.is_expired)

    pending_whatsapp_orders = WhatsAppOrder.objects.filter(status=WhatsAppOrder.STATUS_PENDING).count()
    pending_deliveries = DeliveryRequest.objects.filter(status=DeliveryRequest.STATUS_PENDING).count()
    customer_count = Customer.objects.count()
    pending_appointments = Appointment.objects.filter(status=Appointment.STATUS_PENDING).count()
    needs_human_count = WhatsAppContact.objects.filter(needs_human=True).count()

    recent_sales = Sale.objects.select_related("cashier", "customer").order_by("-created_at")[:8]
    low_stock_products = [p for p in products if p.is_low_stock][:6]
    expiring_products = [p for p in products if (p.is_expiring_soon or p.is_expired)][:6]

    context = {
        "todays_revenue": todays_revenue,
        "todays_sale_count": todays_sale_count,
        "week_revenue": week_revenue,
        "low_stock_count": low_stock_count,
        "expiring_count": expiring_count,
        "expired_count": expired_count,
        "pending_whatsapp_orders": pending_whatsapp_orders,
        "pending_deliveries": pending_deliveries,
        "customer_count": customer_count,
        "pending_appointments": pending_appointments,
        "needs_human_count": needs_human_count,
        "recent_sales": recent_sales,
        "low_stock_products": low_stock_products,
        "expiring_products": expiring_products,
    }
    return render(request, "dashboard/home.html", context)
