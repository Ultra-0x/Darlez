from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_MANAGER = "manager"
    ROLE_CASHIER = "cashier"
    ROLE_LAB_TECH = "lab_tech"
    ROLE_DELIVERY = "delivery"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_MANAGER, "Lab Manager"),
        (ROLE_CASHIER, "Front Desk / Receptionist"),
        (ROLE_LAB_TECH, "Lab Technician / Phlebotomist"),
        (ROLE_DELIVERY, "Sample Collection Rider"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CASHIER)
    phone_number = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    is_active_staff = models.BooleanField(default=True)
    photo = models.ImageField(upload_to="staff_photos/", blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_manager_or_admin(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_MANAGER)
