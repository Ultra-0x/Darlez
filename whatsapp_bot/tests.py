from django.test import SimpleTestCase, override_settings

from .bot_engine import _format_location, _format_menu


class BusinessIdentityReplyTests(SimpleTestCase):
    @override_settings(
        SITE_NAME="Darlez Medical Diagnostics Laboratory",
        SITE_ADDRESS="10 Lingu Crescent, Wuse II",
        SITE_PHONE="09031908880",
        SITE_EMAIL="",
        BUSINESS_HOURS="Please contact us to confirm current opening hours",
    )
    def test_menu_uses_current_business_name(self):
        reply = _format_menu()

        self.assertIn("Darlez Medical Diagnostics Laboratory", reply)
        self.assertNotIn("Curex", reply)

    @override_settings(
        SITE_NAME="Darlez Medical Diagnostics Laboratory",
        SITE_ADDRESS="10 Lingu Crescent, Wuse II",
        SITE_PHONE="09031908880",
        SITE_EMAIL="",
        BUSINESS_HOURS="Please contact us to confirm current opening hours",
    )
    def test_location_reply_omits_unspecified_email(self):
        reply = _format_location()

        self.assertIn("10 Lingu Crescent, Wuse II", reply)
        self.assertIn("09031908880", reply)
        self.assertNotIn("@", reply)
        self.assertNotIn("Curex", reply)
