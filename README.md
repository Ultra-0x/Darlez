# Darlez Medical Diagnostics Laboratory — Diagnostics & Laboratory Supply Platform

A full Django web app for **Darlez Medical Diagnostics Laboratory**, located at **10 Lingu Cres, Wuse II, Abuja 900288, Federal Capital Territory**.
It supports the company's two business lines: medical diagnostic testing and the supply of
diagnostic equipment, reagents, and laboratory consumables to healthcare facilities across Nigeria.
The public website and staff portal include:

- Public site for diagnostic testing and healthcare-facility supply requests
- Separate public catalog views for diagnostics and for equipment, reagents, and consumables
- WhatsApp requests for diagnostic bookings and healthcare-facility supply orders
- Homepage hero uses the supplied laboratory image; its embedded phone and email have been
  cropped from the website copy
- Homepage equipment flyer featuring the Chemwell 2910, Autolyser, and HRJ-C100; the flyer’s
  phone and email are covered on the page
- Editable catalog for diagnostic services and supply products; sample catalog entries and prices
  must be replaced with Darlez-approved listings before production use
- Reagent/kit **expiry date tracking** with a 30-day warning window
- **Low-stock alerts** for reagents and consumables
- **Sales/booking reporting** with revenue, profit, and top-test charts (Chart.js)
- **Staff management** with roles (Admin, Lab Manager, Front Desk, Lab Technician, Sample
  Collection Rider) and role-based permissions
- **Patient records** with booking/order history
- **WhatsApp requests**: patients and healthcare facilities submit their details on the public
  site and are redirected to a pre-filled `wa.me` link to confirm with your team
- The homepage message-request form opens a pre-filled WhatsApp conversation; after the visitor
  taps **Send**, staff can reply in WhatsApp or the staff conversation inbox
- **Home sample collection for diagnostic testing**: clients can request sample collection at home
  and provide their address; staff confirm service availability and scheduling
- Promotions/advertised sales tied to specific tests

## 1. Requirements

- Python 3.11+ (project was built and tested on Python 3.12 / Django 6.0)
- pip

## 2. Setup

```bash
cd diagnostic_center
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo_data   # optional: creates sample staff, tests/supplies, and fictional patients
python manage.py runserver
```

Visit:
- **Public site:** http://127.0.0.1:8000/
- **Staff login:** http://127.0.0.1:8000/accounts/login/
- **Django admin:** http://127.0.0.1:8000/admin/

### Seeded accounts (created by `seed_demo_data`)

| Username   | Password       | Role                          |
|------------|----------------|--------------------------------|
| admin      | admin12345     | Administrator (superuser)     |
| labtech    | labtech12345   | Lab Technician / Phlebotomist |
| frontdesk  | frontdesk12345 | Front Desk / Receptionist     |

**Change these passwords before deploying to production.**
The seeded catalog includes sample equipment, diagnostic services, reagents, and consumables.
Names, prices, stock, expiry dates, supplier, promotion, and patients are placeholders, not confirmed
Darlez records. Sample equipment has no individual product photos. Replace the sample records with
approved information and upload real product photos before making the site public.

## 3. Key settings to review before going live

Open `salesplatform/settings.py`:

- `SITE_NAME`, `SITE_ADDRESS`, `SITE_PHONE`, and `SITE_EMAIL` — business identity, shown
  site-wide via a context processor. Email is intentionally blank until Darlez provides one.
- `WHATSAPP_BUSINESS_NUMBER` — international format, digits only (currently set to
  `2349031908880` for 09031908880). Patients and healthcare facilities use this for requests.
- `EXPIRY_WARNING_DAYS` — how many days ahead of expiry a reagent/kit is flagged (default 30).
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` — **must** be changed for production. Generate a new
  `SECRET_KEY`, set `DEBUG = False`, and list your real domain(s) in `ALLOWED_HOSTS`.
- `EMAIL_BACKEND` — currently prints emails to the console. Point this at a real SMTP backend
  (e.g. Gmail, SendGrid) to receive the daily alert emails for real.

## 4. Branding and supply catalog

The approved Darlez logo is `static/img/darlez-logo.png`, used throughout the public and staff
pages. The homepage also features the Darlez equipment flyer and a laboratory hero image.
The `Diagnostic Equipment`, `Reagents & Kits`, and `Consumables` categories are created by
migrations; add Darlez's actual equipment and supply listings through **Diagnostics & Supplies**
in the staff portal. The current equipment flyer is informational; live inventory, prices, and
availability come from the catalog records.

## 5. Daily alerts (low stock & expiring reagents)

Run this manually, or wire it into cron / a scheduled task to email admins automatically:

```bash
python manage.py check_alerts
```

Example cron entry (runs every morning at 7am):
```
0 7 * * * cd /path/to/project && venv/bin/python manage.py check_alerts
```

## 6. Project structure

```
salesplatform/     # Django project settings, root urls, context processor
accounts/          # Staff profiles, roles, login/logout, staff CRUD
inventory/         # Diagnostic services and equipment/reagent/consumable catalog and stock
sales/             # Diagnostic booking/POS entry, sales history, reporting
customers/         # Patient records
orders/            # Public WhatsApp requests and staff supply/booking management
dashboard/         # Staff homepage with KPIs, alerts, recent activity
templates/          # All HTML templates (base.html = staff layout, base_public.html = public site)
static/img/darlez-logo.png  # Darlez logo
static/img/darlez-hero.png  # Homepage laboratory hero image
static/img/darlez-equipment.png  # Equipment flyer
```

## 7. Adding/editing diagnostic and supply listings

Log in as `admin`, go to **Diagnostics & Supplies** in the sidebar (`/inventory/`) to add,
edit, restock, or retire diagnostic tests, equipment, reagents, and consumables. Use
**Promotions** (`/inventory/promotions/`) to advertise discounts. Seeded catalog entries and
prices are examples; replace them with approved Darlez listings before production use.

## 9. WhatsApp Auto-Reply Bot

The app includes a smart auto-reply bot on your business number (**+2349031908880**) built on
Meta's official **WhatsApp Cloud API** — no unofficial/ban-risk libraries involved.

**What it does out of the box:**
- Menu-driven access to book diagnostic appointments, check test prices and availability, get
  location/hours, or reach staff about equipment and supply requests
- 📅 **Multi-step appointment booking** — patient picks a test, gives a preferred date/time,
  confirms, and a booking request lands in the staff dashboard automatically
- **Live diagnostic prices** pulled straight from your test catalog (typing "malaria" or "FBC" returns
  the real price from the database — never a stale hardcoded number)
- **Diagnostic availability checks** — reports whether a test is in stock, low, or unavailable
- 🤖 **AI-powered replies** (optional) for open-ended questions the menu doesn't cover — "do I
  need to fast before an FBS test?" gets a real, grounded answer via Claude, with guardrails so
  it never invents prices or gives medical diagnoses
- Staff escalation for supply enquiries and other questions the bot cannot answer reliably
- 📧 **Notifies staff by email** the moment a new appointment comes in or a patient asks for a
  human — configurable recipient list, safe to leave unset (just skips silently)
- 🗂️ **Every message saved** to the database — full conversation history per patient, visible
  in the staff dashboard

**Staff-facing pages added:**
- `/whatsapp-bot/conversations/` — read any chat, reply manually (clears the "needs human" flag)
- `/whatsapp-bot/appointments/` — confirm/cancel bot-originated bookings; confirming one
  automatically messages the patient on WhatsApp
- Two new KPI cards on the main dashboard: pending appointments, chats needing a human

### 9.1 Get your Meta credentials (if you haven't already)

1. Go to https://developers.facebook.com/, create a **Meta Business App** (type: Business),
   and add the **WhatsApp** product to it.
2. Under WhatsApp → API Setup, either use the test number Meta gives you first, or add/verify
   your real number (+2349031908880) as the business phone number. Note the **Phone Number ID**.
3. Generate a **permanent access token**: System Users → create a system user → assign it to
   your WhatsApp app with `whatsapp_business_messaging` permission → generate token (choose
   "Never expire" if offered, otherwise you'll need to refresh it periodically).
4. Fill in `.env` (copy from `.env.example` if you don't have one yet):
   ```
   WHATSAPP_CLOUD_API_TOKEN=<your permanent token>
   WHATSAPP_PHONE_NUMBER_ID=<phone number ID from step 2>
   WHATSAPP_VERIFY_TOKEN=darlez-verify-2026
   ```
   `.env` is gitignored — never commit it or paste its contents anywhere public. If a token
   ever leaks, revoke it immediately (System Users → your token → Revoke) and generate a new one.
5. Verify it's working:
   ```bash
   python manage.py check_whatsapp_connection
   ```
   This calls Meta's Graph API directly and reports your verified business name, phone number,
   and WhatsApp quality rating if everything's working, or the exact error if not.

### 9.2 Fastest way to test with a real WhatsApp message today (ngrok)

You don't need to deploy anywhere to try this out — a tunnel to your own laptop is enough for
testing (not for running the business long-term, since it dies when your laptop sleeps/closes):

1. Install ngrok: https://ngrok.com/download (free account is enough), then `ngrok config add-authtoken <your token>`.
2. In one terminal: `python manage.py runserver`
3. In another terminal: `ngrok http 8000`
4. ngrok prints a public URL like `https://a1b2-c3d4.ngrok-free.app` — copy it.
5. In the Meta dashboard, under WhatsApp → Configuration → Webhook, set:
   - **Callback URL:** `https://a1b2-c3d4.ngrok-free.app/whatsapp-bot/webhook/`
   - **Verify Token:** `darlez-verify-2026` (or whatever you set `WHATSAPP_VERIFY_TOKEN` to)
   - Click **Verify and Save** — Meta will hit your ngrok URL immediately; if `runserver` is
     running you should see a `GET /whatsapp-bot/webhook/` 200 in its logs
   - Subscribe to the **messages** webhook field
6. Send a WhatsApp message to +2349031908880 from your phone. You should get the menu reply
   within a few seconds, and see it appear at `/whatsapp-bot/conversations/`.

Note: `SITE_BASE_URL` in `.env` won't be your ngrok URL — leave it as your eventual real domain;
it's only used to build links the bot sends in messages (e.g. "browse our catalog at...").

### 9.3 Real deployment (so it runs without your laptop)

The project is ready for a standard Python host — it ships with `gunicorn`, `whitenoise` for
static files, and a `Procfile`. Any platform that reads a `Procfile` (Railway, Render, Heroku-
style hosts) works with roughly these steps:

1. Push the project to a Git repo (the included `.gitignore` already keeps `.env`, `venv/`,
   and `db.sqlite3` out of it).
2. Create a new app on your platform of choice, pointed at that repo.
3. Set these as environment variables in the platform's dashboard (not in a committed file):
   ```
   DJANGO_SECRET_KEY=<the one already in your local .env — copy it over, or generate a new one>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=<your platform's assigned domain>
   DJANGO_CSRF_TRUSTED_ORIGINS=https://<same domain>
   SITE_BASE_URL=https://<same domain>
   WHATSAPP_CLOUD_API_TOKEN=<your token>
   WHATSAPP_PHONE_NUMBER_ID=<your phone number id>
   WHATSAPP_VERIFY_TOKEN=darlez-verify-2026
   ANTHROPIC_API_KEY=<optional>
   STAFF_NOTIFICATION_EMAILS=<optional>
   ```
4. Most platforms auto-detect the `Procfile` and run `gunicorn salesplatform.wsgi:application`
   for you, plus `python manage.py migrate` on release. If yours doesn't, run those manually.
5. Once deployed, repeat step 5 from section 9.2 above but with your real domain instead of the
   ngrok URL — that's the one-time switch from "testing" to "live in production."
6. For real email delivery of staff notifications, also set a real `EMAIL_BACKEND` in
   `settings.py` (it currently prints emails to the server console) — e.g. Gmail SMTP,
   SendGrid, or Postmark, following Django's standard `EMAIL_*` settings.

### 9.4 Customizing the bot's replies, menu, and AI guardrails

Edit `whatsapp_bot/bot_engine.py` — the menu text, appointment flow, and matching logic all live
there in plain Python. Bot price and availability lookups cover diagnostic services; healthcare
facilities can browse supply listings in the public catalog and send requests through WhatsApp.

The AI fallback's behavior and boundaries (what it will and won't answer) are defined in the
`SYSTEM_PROMPT_TEMPLATE` at the top of `whatsapp_bot/ai_reply.py` — edit that prompt to adjust
tone or add more specific guidance (e.g. your actual fasting/prep instructions per test type).

### 9.5 Local testing without any live credentials

You can exercise the full bot logic — including the appointment flow — without any WhatsApp or
Anthropic credentials:

```bash
python manage.py shell -c "
from whatsapp_bot.models import WhatsAppContact
from whatsapp_bot.bot_engine import handle_incoming_message
c = WhatsAppContact.objects.create(wa_id='2348000000000', profile_name='Test')
print(handle_incoming_message(c, 'hi'))
print(handle_incoming_message(c, '1'))
print(handle_incoming_message(c, 'malaria'))
print(handle_incoming_message(c, 'Friday morning'))
print(handle_incoming_message(c, 'yes'))
c.delete()
"
```

## 10. Notes on scope / what to extend next

- Payment gateway integration (e.g. Paystack/Flutterwave) is not wired in — bookings are
  currently marked paid manually by staff. Hook this into the checkout flow if you want online
  prepayment.
- Lab result upload/delivery to patients isn't included; this app focuses on booking, stock,
  staff, and reporting. A "Results" module could be added as a new app following the same
  pattern as the others.
- Staff notifications are email-only for now. WhatsApp-to-staff notifications are possible but
  need an approved Meta message template (Cloud API only allows free-form replies within a
  24-hour window of the *patient's* last message, not arbitrary outbound pings to staff numbers).
- The bot currently only handles text and simple button/list replies; images, voice notes, and
  location messages are logged but not deeply processed — extend `_process_single_message` in
  `whatsapp_bot/views.py` if you want to handle those (e.g. auto-transcribe voice notes).
- Meta access tokens from a System User can be set to not expire, but tokens tied to a personal
  account expire in ~60 days — use a System User token for anything you deploy long-term.

