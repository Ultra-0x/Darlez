from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = settings.SITE_NAME
admin.site.site_title = "Darlez Staff Administration"
admin.site.index_title = "Laboratory Management"

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('salesplatform.storefront_urls')),
    path('order/', include('orders.urls')),

    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('customers/', include('customers.urls')),
    path('whatsapp-bot/', include('whatsapp_bot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
