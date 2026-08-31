# Feature Guide — August 2026

Five features, plus two pre-existing bugs fixed along the way. Everything below is
live after `python manage.py migrate`.

---

## 1. Export conference registrations to CSV

**Admin → Conference → Registrations**

Two ways out:

- **Export button** (top right) — exports the whole list, respecting any filter or
  search you have applied. Offers CSV, XLSX, JSON and more.
- **"⬇ Export selected registrations to CSV"** action — tick specific rows, pick the
  action, and a CSV downloads immediately as
  `conference-registrations-YYYYMMDD-HHMM.csv`.

27 columns: ticket ID, conference, category, name (first, last and combined), email,
phone, organisation, position, state, dietary requirements, t-shirt size, abstract
reference, amount, stakeholder flag, payment method and status, Paystack reference and
transaction ID, payment date, email-sent flags, terms accepted, check-in, and
registration timestamp.

Export only — registrations are never imported, because that would bypass ticket
numbering and the payment-confirmation flow.

---

## 2. Tickets are withheld until payment is confirmed

**The flaw:** the registration success page rendered a full "Attendance Ticket" with a
hardcoded green **Confirmed** badge, a print button and a link to public ticket
verification — for *every* registrant, including someone who picked Bank Transfer and
had not paid a naira. An unpaid registrant could print what looked like a valid ticket.

**Now**, a ticket exists only when `Registration.ticket_issued` is true, which means the
payment status is `confirmed` or `waived` (complimentary stakeholder places, where there
is no fee to collect).

| | Unpaid / pending | Confirmed or waived |
|---|---|---|
| Panel heading | "Registration Summary" | "Attendance Ticket" |
| Badge | ⏳ Awaiting Payment | ✓ Confirmed |
| ID label | "Payment Reference" | "Ticket ID" |
| Print button | hidden | shown |
| Public verify link | hidden | shown |
| Receipt / welcome email | refused | sent |
| `/conference/ticket/<id>/` | not found | verifies |

An unpaid registrant still sees their reference number and the bank details, with an
explicit note: *"This is not yet a ticket. Your attendance ticket is issued and emailed
to you only after we confirm your payment."*

The guard is enforced in three independent places, so no single change can reopen it:

1. `Registration.ticket_issued` — the model property everything else asks.
2. The success template — gated on that property.
3. `conference/emails.py` — `send_welcome`, `send_payment_receipt` and
   `send_registration_confirmation` refuse to send for an unpaid registration and log a
   warning instead.

Confirming a payment (Paystack callback, or the **Confirm selected registrations** admin
action) issues the ticket and sends the receipt and welcome emails, exactly as before.

---

## 3. Public analytics page — `/analytics/`

Open to every visitor, no login. Linked from the main navigation.

- **Headline tiles:** farmers reached, states covered, LGAs, partner organisations,
  training events, share of women reached.
- **Charts:** farmers by gender, reach by year, by state (all 25), by LGA (top 25),
  by age group, and by partner (top 15).
- Every chart has a **"Show data table"** toggle — the accessible equivalent, with
  counts and shares.
- **JSON feed** at `/api/analytics/` (add `?country=all` for every country).

### Two things worth knowing

**State and LGA names are merged.** The source data delivers these columns in two
different shapes — readable names (`Benue`, `Cross_River`) and GADM codes (`NG.BE`,
`NG.CR`). About 40% of Nigerian records use the coded form. Grouping on the raw column
split each state into two buckets: Abia showed as 39,644 under one label and the rest
under another. `dashboard/analytics.py` normalises first, so Abia now correctly reports
53,351 across 25 states rather than 50 half-counted labels.

LGAs have no readable name in the source for some records and there is no authoritative
code→name table in this project, so rather than invent names a coded LGA is shown as its
code qualified by state — `NG.AB.IS` becomes `IS (Abia)`. The page says so in a note.

**The page reads a snapshot, never the live aggregation.** Computing it scans ~200k rows
and takes about 20 seconds, far too slow per page view. `manage.py refresh_analytics`
computes it and stores it as a `DashboardMetrics` row; the page reads that in ~0.15s.
The refresh has been added to `run_sync_cpanel.sh` so it runs after each data sync. If no
snapshot exists yet the page computes one inline and logs a warning.

```bash
python manage.py refresh_analytics          # Nigeria (default)
python manage.py refresh_analytics --both   # Nigeria + all countries
```

---

## 4. Social media links and homepage feed

Two new admin models under **Website**:

**Social Media Links** — one row per account (platform, URL, handle). Drives the icon
row in the site header and footer; tick `show_in_header` / `show_in_footer` per account
and set the display `order`. Icons and brand colours are derived from the platform.

**Social Posts** — what appears in the "Follow Our Work" grid on the homepage. Fill one
in either way:

- **Upload an image** with a caption and a link to the original post. Always renders,
  needs nothing from the platform.
- **Paste an embed code** (X → "Embed post", Instagram → "Embed"). Renders the real
  post, and overrides the image when present.

The homepage section and the icon rows hide themselves entirely when nothing is
configured. The old single-URL fields on Site Settings still work as a footer fallback
for as long as no Social Media Links exist.

Live API feeds were deliberately not used: they need per-platform tokens that are
approval-gated and expire, which would make the homepage depend on credential upkeep.

---

## 5. Partner pages and partner self-service

### Public page — `/partners/<slug>/`

Every partner organisation now has its own page: cover banner and logo, about text,
mission, areas of work, services, a gallery of field photos, success story, contact
details and social links — plus a **Reach in Nigeria** panel (farmers, states, LGAs,
share of women, and the states they work in) drawn from AKILIMO participant records.

All 147 organisations were given a unique slug by the migration and are listed in a new
**Partner Directory** at the bottom of `/partners/`. ANA partner cards also link through
where they are joined to a partner organisation record.

### Partner administration — `/partners/<slug>/manage/`

A partner edits their own page behind their normal login, across four tabs:

| Tab | What they control |
|---|---|
| **About** | About text, mission, areas of work, organisation type, success story, logo, cover image, contact details, social links |
| **Services** | Add, edit, reorder, hide and remove the services listed on their page |
| **Gallery** | Upload photos of work done, with caption, location and date |
| **Analytics** | Their own reach: farmers, states, LGAs, events; charts by gender, year, state and activity type |

**Granting access.** In **Admin → User Profiles**, set the user's
**Partner organization** and tick **Is partner admin**. Both are required — being a
member of a partner organisation is not on its own permission to edit its public page.
Site staff can manage any partner page and can preview one that is not published.

Untick **Has public page** on the organisation to keep it out of the directory and off
the public web.

Partner analytics are scoped to Nigeria: several partners also appear in the wider
AKILIMO dataset for other countries, and an AKILIMO *Nigeria* partner page listing
Tanzanian districts among its states would be wrong.

---

## Two pre-existing bugs fixed

**`dashboard:index` is not a URL name** — it is `dashboard:home`. Every branch of
`verify_payment` redirected to it, so **the redirect after a successful Paystack
membership payment raised `NoReverseMatch`**. Fixed in seven places across
`dashboard/views.py` and `dashboard/decorators.py`.

**`LOGIN_URL` was never set**, so Django used its default `/accounts/login/` — a URL this
project does not serve. Any unauthenticated visit to a `@login_required` view redirected
to a 404. Now set to `/dashboard/login/` in `settings/base.py`, along with
`LOGIN_REDIRECT_URL` and `LOGOUT_REDIRECT_URL`.

*(A third, `format_html('{:,.2f}', amount)` crashing the Memberships admin changelist,
was fixed in the earlier free-membership work.)*
