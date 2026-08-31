# Free / Paid Registration Guide

The platform can run registration in one of two modes. The switch lives in the Django
admin under **Website → Site Settings → Registration & Membership → Registration Mode**.

| Mode | What a new sign-up gets |
|------|-------------------------|
| **Free** (default) | An active membership for the current year, immediately. No registration fee, no annual dues. Dashboard, certificate and ID card unlock right away. |
| **Paid** | A `pending` membership. Registration fee and annual dues are enforced through the existing Paystack flow before the dashboard unlocks. |

Use **Free** to grow the member base, then flip to **Paid** when you are ready to charge.

## Switching to Free

1. Go to `/admin/website/sitesettings/`.
2. Set **Registration Mode** to *Free*.
3. Optionally edit **Free Membership Message** — the line members see on their
   membership page and dashboard widget.
4. Save.

New sign-ups are covered from that moment. To also cover people who already have an
account:

```bash
python manage.py grant_free_memberships --dry-run   # preview
python manage.py grant_free_memberships             # apply
```

Options: `--username <name>` for a single user, `--include-staff` to include admin
accounts, `--force` to run while the site is in Paid mode.

You can do the same for a selection of members from the admin: **Memberships →
select rows → "🎁 Grant FREE membership for the current year"**.

## Switching back to Paid

1. Set **Registration Mode** to *Paid* and save.
2. Make sure prices are configured under **Membership Pricing** (registration fee and
   annual dues), otherwise the payment page has nothing to show.

Switching to Paid is **not** retroactive. Existing free members keep their membership
until it expires on 31 December, then get the normal renewal flow. To end free
memberships sooner, select them in **Memberships** and run the
**"↩ Revoke free membership"** action — that clears the free grant and moves them back
to `pending`. Members who genuinely paid a registration fee keep it.

## How to tell free members apart

The **Memberships** admin list has a **Fee** column (🎁 Free / Paid) and a
**"Is free membership"** filter. Each free membership also records
`free_membership_granted_at`.

## What happens under the hood

While Registration Mode is *Free*:

- `RegisterView` grants the membership as part of sign-up.
- The access decorators (`require_active_subscription`, `require_registration_payment`,
  `admin_or_subscription_required`) grant and refresh the membership on access, so
  members created before the switch are covered the first time they log in — and free
  memberships roll over automatically into a new calendar year.
- `/dashboard/payment/selection/` and `/dashboard/payment/renewal/` show the free
  membership page instead of the payment options.
- `POST /dashboard/payment/initiate/` refuses to charge and returns
  `{"status": "free"}` — nobody can be billed by accident while the site is free.

All of this is driven by `dashboard/membership_service.py`.
