from urllib.parse import quote

from django.conf import settings


def business_identity(request):
    map_query = quote(f"{settings.SITE_NAME}, {settings.SITE_ADDRESS}", safe="")
    return {
        "site_name": settings.SITE_NAME,
        "site_motto": settings.SITE_MOTTO,
        "site_address": settings.SITE_ADDRESS,
        "site_map_url": f"https://www.google.com/maps/search/?api=1&query={map_query}",
        "site_map_embed_url": f"https://www.google.com/maps?q={map_query}&output=embed",
        "site_phone": settings.SITE_PHONE,
        "site_email": settings.SITE_EMAIL,
        "whatsapp_number": settings.WHATSAPP_BUSINESS_NUMBER,
    }
