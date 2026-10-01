# Masao — Deployment (Render backend + Vercel frontend)

## Αρχιτεκτονική production

```
Πελάτης (QR στο τραπέζι)
   │
   ▼
Vercel (Next.js frontend)  ──POST /api/chat──▶  Render (FastAPI backend)
                                                    │            │
                                              Supabase DB   Render Redis
                                              (μενού+chat)  (rate limiting)
                                                    │
                                              Anthropic API (AI σερβιτόρος)
```

## Βήμα 0 — Πριν από όλα (ασφάλεια)

1. Rotate το Supabase database password (Dashboard → Settings → Database).
2. Rotate το Anthropic API key (console.anthropic.com → API Keys).
3. Βεβαιώσου ότι κανένα `.env` δεν είναι μέσα στο git (`git status` δεν πρέπει να τα δείχνει).

## Βήμα 1 — GitHub

```bash
# Το repo είναι ήδη αρχικοποιημένο τοπικά. Ανέβασέ το:
gh repo create masao-project --private --source . --push
# ή χειροκίνητα: δημιούργησε repo στο github.com και
git remote add origin https://github.com/<USER>/masao-project.git
git push -u origin main
```

## Βήμα 2 — Backend στο Render

1. render.com → New → **Blueprint** → διάλεξε το GitHub repo.
   Το `render.yaml` στη ρίζα στήνει αυτόματα το web service + Redis.
2. Συμπλήρωσε τα secrets που ζητά το dashboard:
   - `DATABASE_URL` = το Supabase pooled connection string σε μορφή
     `postgresql+asyncpg://USER:PASSWORD@HOST:5432/postgres`
     ⚠️ Η Supabase το δίνει ως `postgresql://...` — πρόσθεσε το `+asyncpg`.
   - `ANTHROPIC_API_KEY` = το (νέο) Anthropic key
   - `CORS_ALLOWED_ORIGINS` = `https://masao-project.vercel.app` (placeholder —
     θα το αλλάξεις στο Βήμα 4 με το πραγματικό Vercel URL).
     ⚠️ ΟΧΙ localhost: σε production το config απαιτεί https origin,
     αλλιώς το app δεν ξεκινά καθόλου.
3. Deploy. Όταν τελειώσει, δοκίμασε: `https://<service>.onrender.com/ready`
   → πρέπει να επιστρέφει `{"status":"ready",...}`.

Σημείωση free tier: το service «κοιμάται» μετά από 15' αδράνειας και το
πρώτο request μετά αργεί ~30-60s. Για πραγματικό εστιατόριο, το Starter
plan ($7/μήνα) το κρατάει πάντα ζεστό.

## Βήμα 3 — Frontend στο Vercel

1. vercel.com → Add New → Project → διάλεξε το repo.
2. **Root Directory: `frontend`** (σημαντικό — το Next.js app δεν είναι στη ρίζα).
3. Environment variables:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://<service>.onrender.com`
   - `ADMIN_PASSWORD` = μεγάλη τυχαία φράση (ο κωδικός για το `/admin`)
   - `INTERNAL_API_KEY` = **ακριβώς το ίδιο** με του backend (Βήμα 2)
   - `ADMIN_SESSION_SECRET` = προαιρετικό ξεχωριστό κλειδί υπογραφής του
     session cookie· αν λείπει, υπογράφει ο `ADMIN_PASSWORD`
4. Deploy.

> Τα `ADMIN_PASSWORD` και `INTERNAL_API_KEY` **δεν** έχουν πρόθεμα
> `NEXT_PUBLIC_`: μένουν server-side και δεν φτάνουν ποτέ στον browser.

## Βήμα 4 — Κλείσιμο του κύκλου

1. Πάρε το Vercel URL (π.χ. `https://masao.vercel.app`).
2. Render dashboard → masao-backend → Environment →
   `CORS_ALLOWED_ORIGINS=https://masao.vercel.app` → redeploy.
3. Δοκίμασε το chat από το Vercel URL.

## Βήμα 5 — Πίνακας διαχείρισης

Ο πίνακας ζει στο `https://<vercel-url>/admin` και κλειδώνει με τον
`ADMIN_PASSWORD`. Από εκεί γίνονται:

- διαθεσιμότητα, τιμές, περιγραφές και σειρά εμφάνισης πιάτων
- δημιουργία/διαγραφή πιάτων και κατηγοριών
- οι μεταφράσεις και στις 9 γλώσσες, με αυτόματη συμπλήρωση από το Claude

Οι αλλαγές φαίνονται αμέσως στο μενού των πελατών: κάθε admin write ακυρώνει
το menu cache μετά το commit.

## Βήμα 6 — Take-away παραγγελίες

Ο πελάτης διαλέγει στο καλάθι «Στο κατάστημα» ή «Take away». Το dine-in μένει
ως έχει (δείχνει την οθόνη στον σερβιτόρο). Το take-away ζητά όνομα, τηλέφωνο
και ώρα παραλαβής, και με την επιβεβαίωση στέλνει email.

1. brevo.com → δημιούργησε δωρεάν λογαριασμό (300 email/ημέρα).
2. Settings → Senders, Domains & Dedicated IPs → Senders → **Add a sender**.
   Πάτα το link στο email επιβεβαίωσης. Domain/DNS δεν χρειάζεται.
3. SMTP & API → API Keys → **Generate a new API key**.
4. Security → Authorized IPs: αν είναι ενεργό, **απενεργοποίησέ το**. Το Render
   δεν έχει σταθερή IP και το Brevo θα απέρριπτε τις κλήσεις (401).
5. Render dashboard → masao-backend → Environment:
   - `BREVO_API_KEY` = το κλειδί
   - `ORDER_FROM_EMAIL` = η διεύθυνση του βήματος 2
   - `ORDER_NOTIFICATION_EMAIL` = το email που λαμβάνει τις παραγγελίες
6. Redeploy.

> Αν ο αποστολέας είναι Gmail/Yahoo, το Brevo τον ξαναγράφει σε
> `...@<id>.t-sender-sib.com`. Το email φτάνει κανονικά και το Reply-To δείχνει
> στην πραγματική διεύθυνση. Την πρώτη φορά έλεγξε τα Spam και σήμανέ το
> «Δεν είναι spam». Για αλλαγή παραλήπτη αλλάζεις μόνο το
> `ORDER_NOTIFICATION_EMAIL`, χωρίς νέα επαλήθευση.

Η παραγγελία γράφεται στον πίνακα `takeaway_orders` **πριν** σταλεί το email.
Αν το email αποτύχει, ο πελάτης βλέπει μήνυμα να τηλεφωνήσει και η γραμμή
μένει με `notified_at = null` και τον λόγο στο `email_error`:

```sql
select created_at, customer_name, customer_phone, total, email_error
from takeaway_orders where notified_at is null order by created_at desc;
```

## Βήμα 7 — QR codes

Κάθε τραπέζι δείχνει σε `https://<vercel-url>/?table=N` (N = 1-999).

## Checklist πριν ανοίξει για πελάτες

- [ ] `/ready` επιστρέφει ok (database + rate_limiter)
- [ ] Chat απαντά και στις 5 γλώσσες
- [ ] Rate limit δουλεύει (21ο μήνυμα σε 1 λεπτό → 429)
- [ ] Spend limit στο console.anthropic.com (π.χ. $25/μήνα)
- [ ] Admin endpoints απαντούν 403 χωρίς το X-API-Key
- [ ] Το `/admin` ανακατευθύνει στο login χωρίς συνεδρία
- [ ] Το `/admin` δεν εμφανίζεται στο `/robots.txt` ως allowed
- [ ] Δοκιμαστική take-away παραγγελία φτάνει στο inbox
- [ ] `select count(*) from takeaway_orders where notified_at is null` = 0
