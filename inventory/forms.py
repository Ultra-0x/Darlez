from django import forms
from .models import Product, Category, Supplier, Promotion


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku", "category", "supplier", "description", "image",
            "cost_price", "selling_price", "stock_quantity", "low_stock_threshold",
            "expiry_date", "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone_number", "email", "address"]


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ["title", "banner_text", "products", "discount_percent", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "products": forms.CheckboxSelectMultiple,
        }


class RestockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity to add")
    note = forms.CharField(required=False, max_length=255)


class ContactRequestForm(forms.Form):
    REQUEST_TYPE_CHOICES = [
        ("diagnostics", "Diagnostic testing"),
        ("supplies", "Equipment, reagents or consumables"),
        ("other", "Other enquiry"),
    ]

    name = forms.CharField(
        max_length=150,
        label="Your name or facility name",
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Your phone / WhatsApp number",
        widget=forms.TelInput(attrs={"autocomplete": "tel"}),
    )
    request_type = forms.ChoiceField(
        label="What is your message about?",
        choices=REQUEST_TYPE_CHOICES,
    )
    message = forms.CharField(
        max_length=1500,
        label="Message",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
