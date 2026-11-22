import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt

from accounts.permissions import staff_required
from .bot_engine import handle_incoming_message
from .models import Appointment, WhatsAppContact, WhatsAppMessageLog
from .services import WhatsAppSendError, send_whatsapp_text

logger = logging.getLogger(__name__)


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        return _verify_webhook(request)
    if request.method == "POST":
        return _receive_webhook(request)
    return HttpResponse(status=405)


def _verify_webhook(request):
    """Meta calls this once when you configure the webhook URL in the developer dashboard."""
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return HttpResponse(challenge)
    return HttpResponseForbidden("Verification failed")


def _receive_webhook(request):
    """Handle an incoming message event from WhatsApp Cloud API."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.warning("WhatsApp webhook received invalid JSON body")
        return JsonResponse({"status": "ignored"}, status=200)

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts_meta = {c["wa_id"]: c.get("profile", {}).get("name", "") for c in value.get("contacts", [])}

                for message in messages:
                    _process_single_message(message, contacts_meta)
    except Exception:
        # Never let a malformed/unexpected payload crash the webhook — Meta will retry on non-2xx.
        logger.exception("Error processing WhatsApp webhook payload")

    # Always acknowledge quickly with 200 so Meta doesn't retry/backoff.
    return JsonResponse({"status": "received"}, status=200)


def _process_single_message(message, contacts_meta):
    wa_id = message.get("from")
    if not wa_id:
        return

    msg_type = message.get("type")
    if msg_type == "text":
        body = message.get("text", {}).get("body", "")
    elif msg_type == "interactive":
        interactive = message.get("interactive", {})
        body = (
            interactive.get("button_reply", {}).get("title")
            or interactive.get("list_reply", {}).get("title")
            or ""
        )
    else:
        # Non-text message (image, audio, location, etc.) — acknowledge generically.
        body = f"[{msg_type} message received]"

    contact, _ = WhatsAppContact.objects.get_or_create(
        wa_id=wa_id, defaults={"profile_name": contacts_meta.get(wa_id, "")}
    )
    if contacts_meta.get(wa_id) and not contact.profile_name:
        contact.profile_name = contacts_meta[wa_id]
        contact.save(update_fields=["profile_name"])

    WhatsAppMessageLog.objects.create(
        contact=contact, direction=WhatsAppMessageLog.DIRECTION_IN,
        body=body, wa_message_id=message.get("id", ""),
    )

    reply_text = handle_incoming_message(contact, body)

    WhatsAppMessageLog.objects.create(
        contact=contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=reply_text,
    )

    try:
        send_whatsapp_text(wa_id, reply_text)
    except WhatsAppSendError:
        logger.error("Could not deliver auto-reply to %s (check WHATSAPP_CLOUD_API_TOKEN)", wa_id)


# ---------- Staff-facing conversation viewer ----------

@staff_required
def conversation_list(request):
    contacts = WhatsAppContact.objects.all()
    needs_human = request.GET.get("needs_human", "")
    if needs_human == "1":
        contacts = contacts.filter(needs_human=True)
    return render(request, "whatsapp_bot/conversation_list.html", {"contacts": contacts, "needs_human": needs_human})


@staff_required
def conversation_detail(request, pk):
    contact = get_object_or_404(WhatsAppContact, pk=pk)
    messages_qs = contact.messages.all()

    if request.method == "POST":
        text = request.POST.get("reply", "").strip()
        if text:
            WhatsAppMessageLog.objects.create(contact=contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=text)
            try:
                send_whatsapp_text(contact.wa_id, text)
                contact.needs_human = False
                contact.state = WhatsAppContact.STATE_MENU
                contact.save(update_fields=["needs_human", "state"])
            except WhatsAppSendError:
                logger.error("Could not deliver manual reply to %s", contact.wa_id)

    return render(request, "whatsapp_bot/conversation_detail.html", {"contact": contact, "messages": messages_qs})


# ---------- Staff-facing appointment management ----------

@staff_required
def appointment_list(request):
    appointments = Appointment.objects.select_related("contact", "product").all()
    status = request.GET.get("status", "")
    if status:
        appointments = appointments.filter(status=status)
    return render(request, "whatsapp_bot/appointment_list.html", {"appointments": appointments, "status": status})


@staff_required
def appointment_set_status(request, pk, status):
    appointment = get_object_or_404(Appointment, pk=pk)
    valid_statuses = dict(Appointment.STATUS_CHOICES)
    if status in valid_statuses:
        appointment.status = status
        appointment.save(update_fields=["status"])

        if status == Appointment.STATUS_CONFIRMED:
            product_name = appointment.product.name if appointment.product else "your test"
            confirm_text = (
                f"\u2705 Your appointment for {product_name} on {appointment.preferred_date_text} "
                f"has been confirmed! See you then.\n\n{settings.SITE_NAME}\n{settings.SITE_ADDRESS}"
            )
            WhatsAppMessageLog.objects.create(
                contact=appointment.contact, direction=WhatsAppMessageLog.DIRECTION_OUT, body=confirm_text,
            )
            try:
                send_whatsapp_text(appointment.contact.wa_id, confirm_text)
            except WhatsAppSendError:
                logger.error("Could not notify patient of confirmed appointment %s", appointment.pk)

    return redirect("whatsapp_bot:appointment_list")
