from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PasswordVisibilityTests(TestCase):
    def test_login_password_field_has_visibility_toggle(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, 'data-password-toggle data-password-target="id_password"')
        self.assertContains(response, 'aria-label="Show password"')
        self.assertContains(response, 'class="bi bi-eye"')

    def test_staff_creation_password_field_has_visibility_toggle(self):
        user_model = get_user_model()
        admin = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("accounts:staff_create"))

        self.assertContains(response, 'data-password-toggle data-password-target="id_password"')
