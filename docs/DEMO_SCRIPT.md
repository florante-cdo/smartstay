# Starwood SmartStay: demo script (about 8 minutes)

The story: **one campaign link becomes an enquiry, then a confirmed booking, and the manager
can see which campaign earned it.** All data is sample data; no live availability or payments.

## Before you start (2 minutes)

```bash
source .venv/bin/activate
python manage.py reset_demo --yes
python manage.py runserver
```

Set up three windows so you never have to sign in and out mid-demo:

| Window | Who | Opens |
|---|---|---|
| A (private window) | The guest | The campaign link |
| B (normal window) | Reception | http://127.0.0.1:8000/staff/ , login `reception` / `demo12345` |
| C (second browser, or sign out of B) | Manager | http://127.0.0.1:8000/staff/ , login `manager` / `demo12345` |

Tip: use a fresh private window for every guest run. The browser remembers the first campaign
tag it saw in a session.

## The run

**1. The manager creates the link (window C, 1 min)**
Campaigns. Open *Reception QR Poster* and show its tracked link and QR code.
Say: every campaign gets its own link and QR code, so nothing is guessed later.

**2. The guest follows the link (window A, 1 min)**
Open: `http://127.0.0.1:8000/promo/?utm_source=qr&utm_medium=print&utm_campaign=qr_poster`
Fill in the enquiry (for example Amina Otieno, 0712 345 678, two nights, 2 guests, Deluxe).
Submit and note the reference on the thank-you page.
Say: no account, no payment, just an enquiry.

**3. Reception picks it up (window B, 2 min)**
Overview now shows one more *New enquiry*. Open it from the list.
- Point out the attribution: QR, print, *Reception QR Poster*.
- Take it, move it to *Contacted*, and add a note with a follow-up time.
- Create a reservation request. Try 4 guests in the Deluxe room to show the capacity check,
  then fix it and save. The enquiry becomes *Reservation pending*.
- Open the reservation: Reception has no confirm button.
Say: Reception prepares, the Manager decides.

**4. The manager decides (window C, 1 min)**
Reservations, tab *Pending*. Open Amina's request and confirm it.

**5. The payoff (window C, 2 min)**
Overview, tab *Campaign performance*.
- Reception QR Poster has gained one enquiry and one confirmed booking.
- Walk the funnel: received, handled, reservation requested, confirmed.
- Switch the period (7, 30, 90 days, all time) and open the *Table* view.
Say: a pending reservation is never counted as confirmed.

## Optional extras (pick one or two)

- **Offer ended.** Campaigns: pause *Honeymoon Package*, then open its link in a private
  window. The guest sees an "offer ended" page instead of a dead form.
- **Phone and walk-in.** As Reception, *Log an enquiry* (Phone call), choose the campaign the
  guest mentioned. It appears in the performance tab under that campaign.
- **Untracked traffic.** Open `/promo/` with no tags, then `/promo/?utm_campaign=typo`. Direct
  and unknown traffic are kept separate and never credited to a campaign.
- **Big group.** Enter 13 guests on the guest form to show the "call us for groups" message.

## After the demo

```bash
python manage.py reset_demo --yes
```

## If you are asked

- *Is this live?* No. Sample data, no real availability, rates or payments.
- *What is next in production?* Real room inventory, payment, and the Data Protection Act
  review for guest data.
