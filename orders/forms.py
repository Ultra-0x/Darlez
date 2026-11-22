from django import forms
from .models import DeliveryRequest


class WhatsAppOrderStartForm(forms.Form):
    customer_name = forms.CharField(max_length=150, label="Your name or healthcare facility")
    customer_phone = forms.CharField(max_length=20, label="Phone / WhatsApp number")
    wants_delivery = forms.BooleanField(
        required=False,
        label="Request home sample collection for diagnostic testing",
        help_text="Choose this if you would like our team to visit your home to collect diagnostic samples. We will confirm service availability and appointment details.",
    )
    delivery_address = forms.CharField(
        max_length=255,
        required=False,
        label="Home collection or supply delivery address",
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Notes or supply requirements",
    )


class DeliveryStatusForm(forms.ModelForm):
    class Meta:
        model = DeliveryRequest
        fields = ["status", "assigned_rider", "scheduled_date", "delivery_fee", "notes"]
        widgets = {"scheduled_date": forms.DateInput(attrs={"type": "date"})}
